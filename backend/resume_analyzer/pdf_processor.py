"""
PDF text extraction and preprocessing module with enhanced capabilities
"""

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import os
import logging
import re
from typing import Optional, Dict, List, Tuple
import tempfile
from PIL import Image
import io

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handle PDF text extraction using multiple methods with enhanced preprocessing"""

    def __init__(self, ocr_enabled: bool = True, min_confidence: int = 60):
        self.extraction_methods = ["pdfplumber", "ocr"]
        self.ocr_enabled = ocr_enabled
        self.min_confidence = min_confidence

        # Common resume section headers for better text organization
        self.resume_sections = [
            "experience",
            "education",
            "skills",
            "projects",
            "certifications",
            "awards",
            "languages",
            "interests",
            "summary",
            "objective",
            "contact",
            "references",
        ]

    def extract_text(
        self, pdf_path: str, use_ocr_fallback: bool = True
    ) -> Optional[str]:
        """
        Extract text from PDF using multiple methods with fallback

        Args:
            pdf_path: Path to the PDF file
            use_ocr_fallback: Whether to use OCR as fallback if primary method fails

        Returns:
            Extracted text or None if extraction fails
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return None

        # Get file statistics
        file_stats = self._get_file_stats(pdf_path)
        logger.info(
            f"Processing PDF: {file_stats['file_size_mb']:.2f} MB, {file_stats['page_count']} pages"
        )

        # Method 1: Try pdfplumber first (fastest for text-based PDFs)
        text, method_used = self._extract_with_pdfplumber(pdf_path)
        if text and self.validate_extracted_text(text):
            logger.info(f"Successfully extracted text using {method_used}")
            return self.preprocess_text(text)

        # Method 2: Fallback to OCR for image-based or scanned PDFs
        if use_ocr_fallback and self.ocr_enabled:
            logger.info("Primary extraction insufficient, trying OCR...")
            text, method_used = self._extract_with_ocr(pdf_path)
            if text and self.validate_extracted_text(text):
                logger.info(f"Successfully extracted text using {method_used}")
                return self.preprocess_text(text)

        logger.error("All text extraction methods failed")
        return None

    def _extract_with_pdfplumber(self, pdf_path: str) -> Tuple[Optional[str], str]:
        """Extract text using pdfplumber with enhanced table handling"""
        try:
            text_content = []
            tables_content = []
            method_used = "pdfplumber_text"

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")

                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        for table_num, table in enumerate(tables):
                            table_text = self._process_table(table, page_num, table_num)
                            tables_content.append(table_text)

            # Combine text and tables
            all_content = text_content + tables_content
            result_text = "\n\n".join(all_content) if all_content else None

            # If text extraction is poor but tables were found, try layout preservation
            if result_text and len(result_text.strip()) < 500 and tables_content:
                logger.info("Trying layout-preserving extraction...")
                layout_text = self._extract_with_layout(pdf_path)
                if layout_text and len(layout_text.strip()) > len(result_text.strip()):
                    result_text = layout_text
                    method_used = "pdfplumber_layout"

            return result_text, method_used

        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return None, "pdfplumber_failed"

    def _extract_with_layout(self, pdf_path: str) -> Optional[str]:
        """Extract text while trying to preserve layout structure"""
        try:
            text_content = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Use words extraction for better layout preservation
                    words = page.extract_words()
                    if words:
                        # Group words by lines
                        lines = {}
                        for word in words:
                            line_top = round(word["top"])
                            if line_top not in lines:
                                lines[line_top] = []
                            lines[line_top].append(word)

                        # Sort lines and words within lines
                        sorted_lines = []
                        for top in sorted(lines.keys()):
                            line_words = sorted(lines[top], key=lambda x: x["x0"])
                            line_text = " ".join(word["text"] for word in line_words)
                            sorted_lines.append(line_text)

                        text_content.append("\n".join(sorted_lines))

            return "\n\n".join(text_content) if text_content else None

        except Exception as e:
            logger.error(f"Layout extraction failed: {e}")
            return None

    def _process_table(self, table: List[List], page_num: int, table_num: int) -> str:
        """Convert table data to readable text"""
        if not table or not any(any(cell for cell in row) for row in table):
            return ""

        table_text = [f"--- Table {table_num + 1} on Page {page_num + 1} ---"]

        for row in table:
            # Filter empty cells and join with tabs
            row_text = "\t".join(str(cell) if cell is not None else "" for cell in row)
            table_text.append(row_text)

        return "\n".join(table_text)

    def _extract_with_ocr(self, pdf_path: str) -> Tuple[Optional[str], str]:
        """Extract text using OCR (pytesseract) with enhanced preprocessing"""
        try:
            # Convert PDF pages to images - Use lower DPI for speed
            images = convert_from_path(
                pdf_path,
                dpi=200,  # Balanced DPI for speed/accuracy
                thread_count=min(4, os.cpu_count()),  # Use available CPUs
                grayscale=True,  # Grayscale for better OCR
                first_page=1,
                last_page=min(3, self._get_page_count(pdf_path)),  # Process max 3 pages
            )

            text_content = []
            method_used = "ocr_standard"

            for i, image in enumerate(images):
                logger.info(f"Processing page {i+1}/{len(images)} with OCR...")

                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)

                # Extract text from image using Tesseract with confidence data
                ocr_data = pytesseract.image_to_data(
                    processed_image, lang="eng", output_type=pytesseract.Output.DICT
                )

                # Filter text by confidence
                page_text = self._filter_ocr_by_confidence(ocr_data)
                if page_text.strip():
                    text_content.append(f"--- Page {i+1} ---\n{page_text}")

            result_text = "\n\n".join(text_content) if text_content else None

            # If standard OCR fails, try with different configurations
            if not result_text or len(result_text.strip()) < 100:
                logger.info("Trying alternative OCR configurations...")
                alt_text = self._extract_with_ocr_alternative(pdf_path)
                if alt_text and len(alt_text.strip()) > len(
                    result_text.strip() if result_text else 0
                ):
                    result_text = alt_text
                    method_used = "ocr_alternative"

            return result_text, method_used

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return None, "ocr_failed"

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to grayscale if not already
        if image.mode != "L":
            image = image.convert("L")

        # Enhance contrast
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Increase contrast

        # Apply slight sharpening
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)

        return image

    def _filter_ocr_by_confidence(self, ocr_data: Dict) -> str:
        """Filter OCR results by confidence level"""
        text_lines = {}

        for i in range(len(ocr_data["text"])):
            if (
                int(ocr_data["conf"][i]) > self.min_confidence
                and ocr_data["text"][i].strip()
            ):
                line_num = ocr_data["line_num"][i]
                if line_num not in text_lines:
                    text_lines[line_num] = []
                text_lines[line_num].append(ocr_data["text"][i])

        # Reconstruct text with line breaks
        lines = []
        for line_num in sorted(text_lines.keys()):
            lines.append(" ".join(text_lines[line_num]))

        return "\n".join(lines)

    def _extract_with_ocr_alternative(self, pdf_path: str) -> Optional[str]:
        """Alternative OCR extraction with different configurations"""
        try:
            images = convert_from_path(pdf_path, dpi=400)
            text_content = []

            for image in images:
                # Try different OCR configurations
                configs = [
                    "--psm 6",  # Assume uniform block of text
                    "--psm 4",  # Assume single column of text of variable sizes
                    "--psm 3",  # Fully automatic page segmentation, but no OSD
                ]

                for config in configs:
                    page_text = pytesseract.image_to_string(
                        image, lang="eng", config=config
                    )
                    if page_text.strip():
                        text_content.append(page_text)
                        break

            return "\n\n".join(text_content) if text_content else None

        except Exception as e:
            logger.error(f"Alternative OCR failed: {e}")
            return None

    def _get_file_stats(self, pdf_path: str) -> Dict:
        """Get statistics about the PDF file"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)

            file_size = os.path.getsize(pdf_path)
            file_size_mb = file_size / (1024 * 1024)

            return {
                "page_count": page_count,
                "file_size_bytes": file_size,
                "file_size_mb": file_size_mb,
            }

        except Exception as e:
            logger.error(f"Failed to get file stats: {e}")
            return {"page_count": 0, "file_size_bytes": 0, "file_size_mb": 0}

    def validate_extracted_text(self, text: str, min_length: int = 200) -> bool:
        """
        Validate that extracted text is meaningful resume content

        Args:
            text: Extracted text to validate
            min_length: Minimum character length to consider valid

        Returns:
            True if text appears to be a valid resume
        """
        if not text or not text.strip():
            return False

        # Check minimum length requirement
        if len(text.strip()) < min_length:
            logger.warning(f"Text too short: {len(text.strip())} characters")
            return False

        text_lower = text.lower()

        # Check for common resume elements with weighted scoring
        resume_indicators = {
            "experience": 2,
            "education": 2,
            "skills": 2,
            "work": 1,
            "employment": 1,
            "university": 1,
            "college": 1,
            "degree": 1,
            "project": 1,
            "email": 1,
            "phone": 1,
            "contact": 1,
            "profile": 1,
            "summary": 1,
            "objective": 1,
            "certification": 1,
            "language": 1,
            "reference": 1,
        }

        total_score = 0
        for indicator, weight in resume_indicators.items():
            if indicator in text_lower:
                total_score += weight

        # Should have reasonable resume indicator score
        is_valid = total_score >= 5

        if not is_valid:
            logger.warning(f"Low resume indicator score: {total_score}")

        return is_valid

    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess extracted text with enhanced formatting

        Args:
            text: Raw extracted text

        Returns:
            Cleaned and preprocessed text
        """
        if not text:
            return ""

        # Remove page number markers and headers/footers
        text = self._remove_page_headers_footers(text)

        # Basic text cleaning
        lines = text.split("\n")
        cleaned_lines = []

        current_section = None
        for line in lines:
            line = line.strip()

            # Skip empty lines and page markers
            if not line or line.startswith("--- Page") or line.startswith("--- Table"):
                continue

            # Detect section headers
            section_detected = self._detect_section_header(line)
            if section_detected:
                current_section = section_detected
                cleaned_lines.append(f"\n{line.upper()}\n")
                continue

            # Remove excessive whitespace but preserve line breaks for structure
            line = " ".join(line.split())

            # Add line with appropriate formatting
            if line:
                cleaned_lines.append(line)

        # Join lines with appropriate spacing
        processed_text = "\n".join(cleaned_lines)

        # Remove duplicate blank lines
        processed_text = re.sub(r"\n\s*\n", "\n\n", processed_text)

        return processed_text.strip()

    def _remove_page_headers_footers(self, text: str) -> str:
        """Remove common header/footer patterns"""
        patterns = [
            r"Page \d+ of \d+",
            r"\d+/\d+",
            r"Confidential",
            r"Resume",
            r"CV",
            r"©",
            r"Copyright",
            r"Page \d+",
        ]

        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text

    def _get_page_count(self, pdf_path: str) -> int:
        """Get total page count quickly"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 1

    def _detect_section_header(self, line: str) -> Optional[str]:
        """Detect if a line is a resume section header"""
        line_lower = line.lower().strip()

        # Common section headers and variations
        section_patterns = {
            "experience": [r"experience", r"work history", r"employment"],
            "education": [r"education", r"academic", r"qualifications"],
            "skills": [r"skills", r"technical skills", r"competencies"],
            "projects": [r"projects", r"personal projects", r"academic projects"],
            "certifications": [r"certifications", r"certificates", r"licenses"],
            "awards": [r"awards", r"honors", r"achievements"],
            "languages": [r"languages", r"language skills"],
            "interests": [r"interests", r"hobbies", r"activities"],
        }

        for section, patterns in section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    return section

        return None

    def get_text_statistics(self, text: str) -> dict:
        """
        Get comprehensive statistics about the extracted text

        Args:
            text: Extracted text

        Returns:
            Dictionary with text statistics
        """
        if not text:
            return {
                "character_count": 0,
                "word_count": 0,
                "line_count": 0,
                "section_count": 0,
                "estimated_pages": 0,
                "readability_score": 0,
            }

        lines = text.split("\n")
        words = text.split()

        # Count sections
        section_count = sum(1 for line in lines if self._detect_section_header(line))

        # Estimate pages (conservative estimate)
        estimated_pages = max(1, len(words) // 400)

        # Simple readability score (words per sentence approximation)
        sentence_count = len(re.findall(r"[.!?]+", text))
        readability_score = (
            len(words) / max(sentence_count, 1) if sentence_count > 0 else 0
        )

        return {
            "character_count": len(text),
            "word_count": len(words),
            "line_count": len(lines),
            "section_count": section_count,
            "estimated_pages": estimated_pages,
            "readability_score": round(readability_score, 1),
        }

    def extract_with_metadata(self, pdf_path: str) -> Dict:
        """
        Extract text along with metadata and quality assessment

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with text, metadata, and quality info
        """
        text = self.extract_text(pdf_path)
        stats = self.get_text_statistics(text) if text else {}
        file_stats = self._get_file_stats(pdf_path)

        quality_assessment = {
            "extraction_success": text is not None,
            "text_quality": self._assess_text_quality(text) if text else "poor",
            "likely_scanned": self._is_likely_scanned(pdf_path, text),
            "recommended_method": self._get_recommended_method(text, file_stats),
        }

        return {
            "text": text,
            "statistics": stats,
            "file_metadata": file_stats,
            "quality_assessment": quality_assessment,
            "preprocessing_applied": True,
        }

    def _assess_text_quality(self, text: str) -> str:
        """Assess the quality of extracted text"""
        if not text:
            return "poor"

        word_count = len(text.split())
        line_count = len(text.split("\n"))

        # Check for common OCR errors
        ocr_errors = sum(1 for char in text if ord(char) > 127)  # Non-ASCII characters

        if word_count < 100:
            return "very_poor"
        elif ocr_errors > word_count * 0.1:  # More than 10% non-ASCII
            return "poor"
        elif line_count < 10:
            return "fair"
        else:
            return "good"

    def _is_likely_scanned(self, pdf_path: str, extracted_text: Optional[str]) -> bool:
        """Determine if PDF is likely scanned/image-based"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                # Check if page has extractable text
                page_text = first_page.extract_text()
                has_text = page_text and len(page_text.strip()) > 50

            # If pdfplumber found little text but we have text from OCR, it's likely scanned
            return not has_text and extracted_text and len(extracted_text.strip()) > 100

        except Exception:
            return False

    def _get_recommended_method(self, text: Optional[str], file_stats: Dict) -> str:
        """Get recommended extraction method for future use"""
        if not text:
            return "ocr_high_quality"

        if len(text.split()) < 200:
            return "ocr_high_quality"
        elif file_stats.get("file_size_mb", 0) > 5:
            return "pdfplumber_fast"
        else:
            return "pdfplumber_standard"

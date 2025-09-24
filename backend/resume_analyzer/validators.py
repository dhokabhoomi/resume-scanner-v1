"""
Input validation and sanitization utilities
"""

import re
import os
import mimetypes
from typing import List, Optional, Dict, Any, Union
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, validator, Field
import bleach
import html

class FileValidator:
    """Comprehensive file validation for uploads"""
    
    # Allowed file types and their magic numbers
    ALLOWED_EXTENSIONS = {'.pdf'}
    ALLOWED_MIMETYPES = {'application/pdf'}
    PDF_MAGIC_NUMBERS = [
        b'%PDF-1.',  # Standard PDF header
        b'\x25\x50\x44\x46',  # PDF in hex
    ]
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_FILE_SIZE = 1024  # 1KB
    MAX_FILENAME_LENGTH = 255
    
    @classmethod
    def validate_file(cls, file: UploadFile) -> Dict[str, Any]:
        """
        Comprehensive file validation
        
        Args:
            file: Uploaded file to validate
            
        Returns:
            Dict with validation results
            
        Raises:
            HTTPException: If validation fails
        """
        errors = []
        warnings = []
        
        # 1. Basic file existence check
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # 2. Filename validation
        filename = cls._sanitize_filename(file.filename)
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            errors.append(f"Filename too long (max {cls.MAX_FILENAME_LENGTH} characters)")
        
        if not filename:
            errors.append("Invalid filename")
        
        # 3. Extension validation
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            errors.append(f"Invalid file type. Only {', '.join(cls.ALLOWED_EXTENSIONS)} allowed")
        
        # 4. MIME type validation
        if hasattr(file, 'content_type') and file.content_type:
            if file.content_type not in cls.ALLOWED_MIMETYPES:
                warnings.append(f"Suspicious MIME type: {file.content_type}")
        
        # 5. File size validation
        if hasattr(file, 'size') and file.size is not None:
            if file.size > cls.MAX_FILE_SIZE:
                errors.append(f"File too large (max {cls.MAX_FILE_SIZE // (1024*1024)}MB)")
            if file.size < cls.MIN_FILE_SIZE:
                errors.append(f"File too small (min {cls.MIN_FILE_SIZE} bytes)")
        
        if errors:
            raise HTTPException(status_code=400, detail=f"File validation failed: {'; '.join(errors)}")
        
        return {
            "filename": filename,
            "original_filename": file.filename,
            "warnings": warnings,
            "file_size": getattr(file, 'size', None),
            "content_type": getattr(file, 'content_type', None)
        }
    
    @classmethod
    def validate_file_content(cls, file_content: bytes) -> Dict[str, Any]:
        """
        Validate file content by checking magic numbers
        
        Args:
            file_content: Raw file bytes
            
        Returns:
            Dict with content validation results
        """
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file content")
        
        # Check PDF magic numbers
        is_valid_pdf = any(
            file_content.startswith(magic) 
            for magic in cls.PDF_MAGIC_NUMBERS
        )
        
        if not is_valid_pdf:
            raise HTTPException(
                status_code=400, 
                detail="File content does not appear to be a valid PDF"
            )
        
        return {
            "is_valid_pdf": True,
            "file_size": len(file_content),
            "starts_with": file_content[:20].hex()  # For debugging
        }
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return ""
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        # Keep only alphanumeric, dots, dashes, underscores, spaces
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Remove multiple dots and spaces
        filename = re.sub(r'\.{2,}', '.', filename)
        filename = re.sub(r'\s{2,}', ' ', filename)
        
        # Trim whitespace
        filename = filename.strip()
        
        # Ensure it has an extension
        if not os.path.splitext(filename)[1]:
            filename += '.pdf'
        
        return filename

class TextValidator:
    """Text input validation and sanitization"""
    
    MAX_TEXT_LENGTH = 50000  # 50KB of text
    MIN_TEXT_LENGTH = 10
    
    # Suspicious patterns that might indicate malicious content
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # JavaScript
        r'javascript:',  # JavaScript protocol
        r'vbscript:',  # VBScript protocol
        r'on\w+\s*=',  # Event handlers
        r'data:text/html',  # Data URLs
        r'\\x[0-9a-f]{2}',  # Hex encoded
        r'%[0-9a-f]{2}',  # URL encoded
    ]
    
    @classmethod
    def validate_and_sanitize_text(cls, text: str, field_name: str = "text") -> str:
        """
        Validate and sanitize text input
        
        Args:
            text: Input text to validate
            field_name: Name of the field for error messages
            
        Returns:
            Sanitized text
            
        Raises:
            HTTPException: If validation fails
        """
        if not isinstance(text, str):
            raise HTTPException(
                status_code=400, 
                detail=f"{field_name} must be a string"
            )
        
        # Length validation
        if len(text) > cls.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} too long (max {cls.MAX_TEXT_LENGTH} characters)"
            )
        
        if len(text.strip()) < cls.MIN_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} too short (min {cls.MIN_TEXT_LENGTH} characters)"
            )
        
        # Check for suspicious patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail=f"Suspicious content detected in {field_name}"
                )
        
        # Sanitize HTML/XML content
        cleaned_text = bleach.clean(text, tags=[], strip=True)
        
        # Decode any HTML entities
        cleaned_text = html.unescape(cleaned_text)
        
        # Normalize whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text

class PriorityValidator:
    """Validate priority lists and parameters"""
    
    VALID_PRIORITIES = {
        "Technical Skills",
        "Project Experience", 
        "Academic Performance",
        "Work Experience",
        "GitHub Profile",
        "LinkedIn Profile",
        "Certifications",
        "Resume Formatting",
        "Extracurricular Activities",
        "Communication Skills",
        "Content Quality",
        "Skill Diversity"
    }
    
    MAX_PRIORITIES = 5
    
    @classmethod
    def validate_priorities(cls, priorities_str: Optional[str]) -> Optional[List[str]]:
        """
        Validate and parse priorities string
        
        Args:
            priorities_str: Comma-separated priority string
            
        Returns:
            List of valid priorities or None
            
        Raises:
            HTTPException: If validation fails
        """
        if not priorities_str or not priorities_str.strip():
            return None
        
        # Sanitize the input string first
        priorities_str = TextValidator.validate_and_sanitize_text(
            priorities_str, "priorities"
        )
        
        # Parse priorities
        priorities = [p.strip() for p in priorities_str.split(",") if p.strip()]
        
        if len(priorities) > cls.MAX_PRIORITIES:
            raise HTTPException(
                status_code=400,
                detail=f"Too many priorities (max {cls.MAX_PRIORITIES})"
            )
        
        # Validate each priority
        invalid_priorities = []
        for priority in priorities:
            if priority not in cls.VALID_PRIORITIES:
                invalid_priorities.append(priority)
        
        if invalid_priorities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priorities: {', '.join(invalid_priorities)}. "
                      f"Valid options: {', '.join(sorted(cls.VALID_PRIORITIES))}"
            )
        
        return priorities

class JobNameValidator:
    """Validate job names for bulk processing"""
    
    MAX_LENGTH = 100
    MIN_LENGTH = 1
    ALLOWED_CHARS = re.compile(r'^[a-zA-Z0-9\s\-_\.]+$')
    
    @classmethod
    def validate_job_name(cls, job_name: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize job name
        
        Args:
            job_name: Job name to validate
            
        Returns:
            Sanitized job name or None
            
        Raises:
            HTTPException: If validation fails
        """
        if not job_name or not job_name.strip():
            return None
        
        job_name = job_name.strip()
        
        if len(job_name) > cls.MAX_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Job name too long (max {cls.MAX_LENGTH} characters)"
            )
        
        if len(job_name) < cls.MIN_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Job name too short (min {cls.MIN_LENGTH} character)"
            )
        
        if not cls.ALLOWED_CHARS.match(job_name):
            raise HTTPException(
                status_code=400,
                detail="Job name contains invalid characters. Only letters, numbers, spaces, hyphens, underscores, and dots allowed"
            )
        
        # Remove multiple spaces
        job_name = re.sub(r'\s+', ' ', job_name)
        
        return job_name

# Pydantic models with validation
class ValidatedAnalysisRequest(BaseModel):
    """Validated request model for resume analysis"""
    
    priorities: Optional[str] = Field(None, max_length=200)
    
    @validator('priorities', pre=True, always=True)
    def validate_priorities_field(cls, v):
        if v is not None:
            return PriorityValidator.validate_priorities(v)
        return v

class ValidatedBulkRequest(BaseModel):
    """Validated request model for bulk analysis"""
    
    job_name: Optional[str] = Field(None, max_length=100)
    priorities: Optional[str] = Field(None, max_length=200)
    
    @validator('job_name', pre=True, always=True)
    def validate_job_name_field(cls, v):
        if v is not None:
            return JobNameValidator.validate_job_name(v)
        return v
    
    @validator('priorities', pre=True, always=True)
    def validate_priorities_field(cls, v):
        if v is not None:
            return PriorityValidator.validate_priorities(v)
        return v

def validate_file_upload(file: UploadFile) -> Dict[str, Any]:
    """
    Main file upload validation function
    
    Args:
        file: Uploaded file
        
    Returns:
        Validation results
        
    Raises:
        HTTPException: If validation fails
    """
    return FileValidator.validate_file(file)

def validate_file_content(content: bytes) -> Dict[str, Any]:
    """
    Validate file content
    
    Args:
        content: File content bytes
        
    Returns:
        Validation results
    """
    return FileValidator.validate_file_content(content)

def sanitize_text_input(text: str, field_name: str = "input") -> str:
    """
    Sanitize text input
    
    Args:
        text: Input text
        field_name: Field name for errors
        
    Returns:
        Sanitized text
    """
    return TextValidator.validate_and_sanitize_text(text, field_name)
"""
Enhanced rule-based validation and analysis module with recruiter priorities
"""

import re
import sys
import logging
import requests
import urllib.parse
import datetime
from typing import Dict, List, Any, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from enum import Enum

from .config import RULE_VALIDATION, HTTP_VALIDATION, LINK_PATTERNS, SCORING_CONFIG, FORMATTING_RULES
from .models import (
    CGPAAnalysisResult,
    ProjectDatesAnalysisResult,
    EducationAnalysisResult,
    FormattingAnalysisResult,
    LinkAnalysisResult,
    ExtractedLink,
    LinkValidationResult,
    RuleBasedFindings,
    LinkType,
    PriorityAreas,
)

logger = logging.getLogger(__name__)


class ValidationPriority(Enum):
    """Priority levels for validation checks"""

    HIGH = 3
    MEDIUM = 2
    LOW = 1
    NONE = 0


class RuleBasedValidator:
    """Comprehensive rule-based validation and analysis with priority-based scoring"""

    def __init__(self, priorities: Optional[PriorityAreas] = None):
        self.cgpa_patterns = RULE_VALIDATION["cgpa_patterns"]
        self.date_patterns = RULE_VALIDATION["date_patterns"]
        self.education_patterns = RULE_VALIDATION["education_patterns"]
        self.link_patterns = LINK_PATTERNS
        self.priorities = (
            priorities or PriorityAreas()
        )  # Default priorities if none provided

    def run_all_checks(self, resume_text: str) -> Dict[str, Any]:
        """
        Run all rule-based checks with individual error handling

        Args:
            resume_text: The resume text to analyze

        Returns:
            Dictionary with analysis results or error information
        """
        if not resume_text or not resume_text.strip():
            return {"error": "Empty resume text provided", "rule_based_findings": {}}

        # Initialize results with safe defaults
        results = {}

        # Run each check with individual error handling
        results["cgpa_results"] = self._safe_execute(
            self.detect_cgpa,
            resume_text,
            default=CGPAAnalysisResult(
                cgpa_present=False, cgpa_values=[], cgpa_count=0
            ),
        )

        results["project_date_results"] = self._safe_execute(
            self.detect_project_dates,
            resume_text,
            default=ProjectDatesAnalysisResult(
                dates_present=False,
                total_dates_found=0,
                projects_with_dates=0,
                project_date_coverage=0,
            ),
        )

        results["education_results"] = self._safe_execute(
            self.detect_education_levels, resume_text, default=EducationAnalysisResult()
        )

        results["link_results"] = self._safe_execute(
            self.validate_links,
            resume_text,
            default=LinkAnalysisResult(links_found=[], valid_links=[], broken_links=[]),
        )

        results["formatting_results"] = self._safe_execute(
            self.analyze_formatting, resume_text, default=FormattingAnalysisResult()
        )

        results["content_quality_results"] = self._safe_execute(
            self.analyze_content_quality,
            resume_text,
            default={"score": 0, "issues": []},
        )

        try:
            # Calculate completeness and formatting scores with priority weighting
            completeness_data = self._calculate_completeness_score(results)
            formatting_data = self._calculate_formatting_score(
                results["formatting_results"]
            )

            # Build final findings
            rule_based_findings = RuleBasedFindings(
                cgpa_analysis=results["cgpa_results"],
                project_dates_analysis=results["project_date_results"],
                education_analysis=results["education_results"],
                link_validation_analysis=results["link_results"],
                formatting_analysis=formatting_data,
                content_quality_analysis=results["content_quality_results"],
                completeness_score=completeness_data["score"],
                completeness_breakdown=completeness_data["breakdown"],
                priority_areas=self.priorities.dict() if self.priorities else {},
            )

            return {
                "status": "success",
                "rule_based_findings": rule_based_findings.dict(),
            }

        except Exception as e:
            logger.error(f"Error in rule-based validation: {e}")
            return {
                "error": f"Rule-based validation failed: {str(e)}",
                "rule_based_findings": {},
            }

    def _safe_execute(self, func, *args, default=None):
        """Safely execute a function with error handling"""
        try:
            return func(*args)
        except Exception as e:
            func_name = func.__name__
            logger.error(f"Error in {func_name}: {e}")
            return default

    def detect_cgpa(self, text: str) -> CGPAAnalysisResult:
        """Detect CGPA/GPA information in resume text with enhanced patterns"""
        cgpa_values = []
        cgpa_contexts = []

        # Enhanced patterns to capture different CGPA formats
        enhanced_patterns = [
            r"(?:CGPA|GPA|Grade Point Average)[\s:]*([0-9]\.?[0-9]?[0-9]?)\s*/\s*([0-9]\.?[0-9]?)",  # CGPA: 3.5/4.0
            r"(?:CGPA|GPA|Grade Point Average)[\s:]*([0-9]\.?[0-9]?[0-9]?)",  # CGPA: 3.5
            r"([0-9]\.?[0-9]?[0-9]?)\s*/\s*([0-9]\.?[0-9]?)\s*(?:CGPA|GPA)",  # 3.5/4.0 CGPA
            r"([0-9]\.?[0-9]?[0-9]?)\s*(?:CGPA|GPA)",  # 3.5 CGPA
            r"(?:CGPA|GPA)\s*of\s*([0-9]\.?[0-9]?[0-9]?)",  # CGPA of 3.5
        ]

        for pattern in enhanced_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract the numeric value(s)
                for group in match.groups():
                    if group and re.match(r"^\d\.?\d?$", group):
                        # Get context around the match
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 20)
                        context = text[start:end].replace("\n", " ").strip()

                        if group not in cgpa_values:
                            cgpa_values.append(group)
                            cgpa_contexts.append(context)
                        break

        return CGPAAnalysisResult(
            cgpa_present=len(cgpa_values) > 0,
            cgpa_values=cgpa_values,
            cgpa_count=len(cgpa_values),
            cgpa_contexts=cgpa_contexts,
        )

    def detect_project_dates(self, text: str) -> ProjectDatesAnalysisResult:
        """Detect project dates and calculate coverage with enhanced date detection"""
        dates_found = []
        date_contexts = []

        # Enhanced date patterns
        enhanced_date_patterns = [
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}",  # Month Year
            r"\d{1,2}/\d{4}",  # MM/YYYY or M/YYYY
            r"\d{4}-\d{1,2}",  # YYYY-MM
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
            r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",  # DD-MM-YYYY or MM-DD-YYYY variants
            r"(?:Present|Current|Now|Ongoing)",
        ]

        for pattern in enhanced_date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(0)
                dates_found.append(date_str)

                # Get context around the date
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].replace("\n", " ").strip()
                date_contexts.append({"date": date_str, "context": context})

        # Estimate number of projects (improved heuristic)
        project_keywords = [
            "project",
            "developed",
            "built",
            "created",
            "implemented",
            "designed",
            "engineered",
            "led",
            "managed",
            "spearheaded",
        ]

        project_count = 0
        project_sections = []

        # Look for project sections
        project_section_patterns = [
            r"(?:PROJECTS|PROJECT EXPERIENCE|PROJECT WORK)(.*?)(?=EDUCATION|EXPERIENCE|SKILLS|$)",
            r"(?:Personal Projects|Academic Projects)(.*?)(?=EDUCATION|EXPERIENCE|SKILLS|$)",
        ]

        for pattern in project_section_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                project_sections.append(match)
                # Count project mentions in this section
                for keyword in project_keywords:
                    project_count += len(
                        re.findall(rf"\b{keyword}\b", match, re.IGNORECASE)
                    )

        # If no project sections found, search entire text
        if project_count == 0:
            for keyword in project_keywords:
                project_count += len(re.findall(rf"\b{keyword}\b", text, re.IGNORECASE))

        # Estimate projects with dates
        projects_with_dates = min(
            len(dates_found) // 2, project_count
        )  # Assuming 2 dates per project
        date_coverage = (
            projects_with_dates / max(project_count, 1) if project_count > 0 else 0
        )

        return ProjectDatesAnalysisResult(
            dates_present=len(dates_found) > 0,
            total_dates_found=len(dates_found),
            projects_with_dates=projects_with_dates,
            total_projects_identified=project_count,
            project_date_coverage=date_coverage,
            date_contexts=date_contexts,
        )

    def detect_education_levels(self, text: str) -> EducationAnalysisResult:
        """Detect various education levels with enhanced patterns"""
        results = EducationAnalysisResult()
        education_contexts = []

        # Enhanced education patterns with context capture
        enhanced_education_patterns = {
            "class_10": [
                r"(Class 10|10th Class|SSC|Secondary School Certificate|Matriculation)(.*?)(?=Class 12|HSC|Diploma|Degree|$)",
                r"(High School|Secondary Education)(.*?)(\d{4})",
            ],
            "class_12": [
                r"(Class 12|12th Class|HSC|Higher Secondary Certificate|Intermediate)(.*?)(?=Degree|Diploma|College|University|$)",
                r"(Senior Secondary|Higher Secondary)(.*?)(\d{4})",
            ],
            "diploma": [
                r"(Diploma|Polytechnic)(.*?)(?=Degree|Bachelor|B\.?Tech|B\.?E|$)",
                r"(.*?Diploma.*?)(\d{4}.*?\d{4})",
            ],
            "bachelor": [
                r"(Bachelor|B\.?Tech|B\.?E|B\.?Com|B\.?Sc|B\.?A)(.*?)(?=Master|M\.?Tech|M\.?S|MBA|$)",
                r"(Undergraduate|UG Degree)(.*?)(\d{4}.*?\d{4})",
            ],
            "master": [
                r"(Master|M\.?Tech|M\.?S|MBA|M\.?Com|M\.?Sc|M\.?A)(.*?)(?=Ph\.?D|Doctorate|$)",
                r"(Postgraduate|PG Degree)(.*?)(\d{4}.*?\d{4})",
            ],
            "phd": [
                r"(Ph\.?D|Doctorate)(.*?)(?=Experience|Skills|$)",
                r"(Doctoral|PhD)(.*?)(\d{4}.*?\d{4})",
            ],
        }

        for edu_level, patterns in enhanced_education_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    setattr(results, f"{edu_level}_present", True)

                    # Capture context
                    context = match.group(0).replace("\n", " ").strip()
                    education_contexts.append({"level": edu_level, "context": context})
                    break

        results.education_contexts = education_contexts
        return results

    def validate_links(self, text: str) -> LinkAnalysisResult:
        """Extract and validate professional links with HTTP validation"""
        extracted_links = []

        # Extract links using patterns
        for link_type, patterns in self.link_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    raw_url = match.group(0)

                    # Skip generic words
                    if link_type == "PORTFOLIO" and "." not in raw_url:
                        continue

                    reconstructed_url = self._reconstruct_url(raw_url, link_type)

                    # Avoid duplicates
                    if not any(
                        link.reconstructed_url == reconstructed_url
                        for link in extracted_links
                    ):
                        extracted_links.append(
                            ExtractedLink(
                                type=LinkType(link_type),
                                raw_text=raw_url,
                                reconstructed_url=reconstructed_url,
                            )
                        )

        # Validate links with HTTP requests (if enabled)
        if HTTP_VALIDATION["enabled"]:
            validated_links = self._validate_extracted_links(extracted_links)
        else:
            validated_links = extracted_links

        valid_links = [link for link in validated_links if link.valid is True]
        broken_links = [link for link in validated_links if link.valid is False]

        return LinkAnalysisResult(
            links_found=validated_links,
            valid_links=valid_links,
            broken_links=broken_links,
        )

    def _validate_extracted_links(
        self, links: List[ExtractedLink]
    ) -> List[ExtractedLink]:
        """Validate extracted links with concurrent HTTP requests for speed"""
        max_links = HTTP_VALIDATION["max_links_per_resume"]
        validation_links = links[:max_links]

        if not validation_links:
            return links

        logger.info(f"Validating {len(validation_links)} links concurrently...")

        # Use concurrent validation for speed
        import concurrent.futures

        def validate_link_wrapper(link):
            try:
                validation_result = self._validate_single_link(link.reconstructed_url)
                link.valid = validation_result.is_valid
                link.validation_details = validation_result
                return link
            except Exception as e:
                logger.error(f"Error validating {link.reconstructed_url}: {e}")
                link.valid = False
                link.validation_details = LinkValidationResult(
                    url=link.reconstructed_url,
                    is_valid=False,
                    error_type="VALIDATION_ERROR",
                    error_message=str(e)[:200],
                )
                return link

        # Process links concurrently with limited threads
        max_workers = min(3, len(validation_links))  # Limit concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_link = {
                executor.submit(validate_link_wrapper, link): link
                for link in validation_links
            }

            for future in concurrent.futures.as_completed(
                future_to_link, timeout=12
            ):  # 12s total timeout
                try:
                    future.result()
                except concurrent.futures.TimeoutError:
                    logger.warning("Link validation timeout reached")
                except Exception as e:
                    logger.error(f"Concurrent validation error: {e}")

        # Mark remaining links as unvalidated if over limit
        for link in links[max_links:]:
            link.valid = None
            link.validation_details = LinkValidationResult(
                url=link.reconstructed_url,
                is_valid=None,
                error_type="LIMIT_REACHED",
                error_message="Validation skipped due to link limit",
            )

        return links

    def _validate_single_link(self, url: str) -> LinkValidationResult:
        """Validate a single URL with comprehensive HTTP checking"""
        result = LinkValidationResult(url=url, is_valid=False)

        try:
            # Normalize URL
            parsed_url = urllib.parse.urlparse(url)
            if not parsed_url.scheme:
                url = "https://" + url
                result.final_url = url
            else:
                result.final_url = url

            # Create session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=HTTP_VALIDATION["max_retries"],
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # Set browser-like headers to avoid bot detection
            headers = HTTP_VALIDATION["headers"].copy()
            headers["User-Agent"] = HTTP_VALIDATION["user_agent"]

            import time

            start_time = time.time()

            # Try HEAD request first
            try:
                response = session.head(
                    url,
                    headers=headers,
                    timeout=HTTP_VALIDATION["timeout"],
                    allow_redirects=True,
                    verify=True,
                )

                if response.status_code == 405:  # Method Not Allowed
                    response = session.get(
                        url,
                        headers=headers,
                        timeout=HTTP_VALIDATION["timeout"],
                        allow_redirects=True,
                        stream=True,
                        verify=True,
                    )
                    response.close()

            except requests.exceptions.SSLError:
                logger.warning(
                    f"SSL verification failed for {url}, retrying without verification"
                )
                response = session.head(
                    url,
                    headers=headers,
                    timeout=HTTP_VALIDATION["timeout"],
                    allow_redirects=True,
                    verify=False,
                )
                result.ssl_warning = True

            end_time = time.time()
            result.response_time_ms = int((end_time - start_time) * 1000)
            result.status_code = response.status_code
            result.final_url = response.url
            result.redirect_count = len(response.history)

            # Determine validity based on status code and platform-specific rules
            final_url_lower = result.final_url.lower()

            # Platform-specific handling for common cases
            if "linkedin.com" in final_url_lower:
                result.platform = "LinkedIn"
                # LinkedIn often returns 999 for bot protection, but URL structure indicates validity
                if response.status_code == 999:
                    # Check if URL structure is valid LinkedIn profile format
                    if (
                        "/in/" in final_url_lower
                        and len(final_url_lower.split("/in/")[-1]) > 2
                    ):
                        result.is_valid = True
                        result.error_message = (
                            "LinkedIn bot protection (999) - URL structure valid"
                        )
                    else:
                        result.is_valid = False
                        result.error_type = "LINKEDIN_INVALID_FORMAT"
                        result.error_message = "Invalid LinkedIn profile URL format"
                elif 200 <= response.status_code < 400:
                    result.is_valid = True
                else:
                    result.is_valid = False
                    result.error_type = f"HTTP_{response.status_code}"
                    result.error_message = (
                        f"LinkedIn returned HTTP {response.status_code}"
                    )

            elif "github.com" in final_url_lower:
                result.platform = "GitHub"
                if 200 <= response.status_code < 400:
                    result.is_valid = True
                elif response.status_code == 404:
                    # GitHub 404 might be a private repo or user, check URL structure
                    github_path = (
                        final_url_lower.split("github.com/")[-1]
                        if "github.com/" in final_url_lower
                        else ""
                    )
                    if github_path and "/" not in github_path.strip(
                        "/"
                    ):  # Single username/org
                        result.is_valid = True
                        result.error_message = (
                            "GitHub profile exists but may be private/restricted"
                        )
                    else:
                        result.is_valid = False
                        result.error_type = "GITHUB_NOT_FOUND"
                        result.error_message = "GitHub profile or repository not found"
                else:
                    result.is_valid = False
                    result.error_type = f"HTTP_{response.status_code}"
                    result.error_message = (
                        f"GitHub returned HTTP {response.status_code}"
                    )

            else:
                # Generic website/portfolio
                result.platform = "Other/Portfolio"
                if 200 <= response.status_code < 400:
                    result.is_valid = True
                elif response.status_code in [403, 405]:
                    # Some sites block HEAD requests but are valid
                    result.is_valid = True
                    result.error_message = f"Site accessible but returned {response.status_code} (likely blocking HEAD requests)"
                else:
                    result.is_valid = False
                    result.error_type = f"HTTP_{response.status_code}"
                    result.error_message = (
                        f"Received HTTP {response.status_code} status code"
                    )

        except requests.exceptions.Timeout:
            result.error_type = "TIMEOUT"
            result.error_message = "Request timed out"
        except requests.exceptions.ConnectionError as e:
            result.error_type = "CONNECTION_ERROR"
            if "Name or service not known" in str(e):
                result.error_message = "Domain name could not be resolved (DNS error)"
            else:
                result.error_message = f"Connection failed: {str(e)[:100]}"
        except Exception as e:
            result.error_type = "UNKNOWN_ERROR"
            result.error_message = str(e)[:100]
        finally:
            result.validation_timestamp = datetime.datetime.now().isoformat()
            try:
                session.close()
            except Exception:
                pass

        return result

    def _reconstruct_url(self, raw_url: str, link_type: str) -> str:
        """Reconstruct a proper URL from raw text with improved logic"""
        url = raw_url.strip()

        # Remove common prefixes from raw text
        url = re.sub(
            r"^(?:LinkedIn|GitHub|Portfolio|Website):\s*", "", url, flags=re.IGNORECASE
        )

        # If already a complete URL, return as-is
        if url.startswith(("http://", "https://")):
            return url

        # Platform-specific reconstruction
        if link_type == "LINKEDIN":
            if "linkedin.com" not in url.lower():
                # Just a username
                if "/" not in url and len(url) > 2:
                    url = f"linkedin.com/in/{url}"
                elif not url.startswith("linkedin.com"):
                    url = f"linkedin.com/in/{url}"
            # Add www. if not present
            if not url.startswith("www."):
                url = f"www.{url}"

        elif link_type == "GITHUB":
            if "github.com" not in url.lower():
                # Just a username or username/repo
                url = f"github.com/{url}"
            # Add www. if not present
            if not url.startswith("www."):
                url = f"www.{url}"

        # Add https:// if not present
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        return url

    def analyze_formatting(self, text: str) -> FormattingAnalysisResult:
        """Analyze resume formatting quality with enhanced checks"""
        lines = text.split("\n")

        # Enhanced formatting metrics
        spacing_score, spacing_issues = self._analyze_spacing(lines)
        bullet_score, bullet_issues = self._analyze_bullets(lines)
        line_length_score, line_length_issues = self._analyze_line_lengths(lines)
        resume_length_score, length_issues = self._analyze_resume_length(text)
        consistency_score, consistency_issues = self._analyze_consistency(text)

        # Calculate overall score with weighted components
        weights = {
            "spacing": 0.2,
            "bullets": 0.2,
            "line_length": 0.2,
            "resume_length": 0.2,
            "consistency": 0.2,
        }

        overall_score = (
            spacing_score * weights["spacing"]
            + bullet_score * weights["bullets"]
            + line_length_score * weights["line_length"]
            + resume_length_score * weights["resume_length"]
            + consistency_score * weights["consistency"]
        )

        return FormattingAnalysisResult(
            spacing_analysis={
                "spacing_score": spacing_score,
                "spacing_issues": spacing_issues,
            },
            bullet_point_analysis={
                "bullet_consistency_score": bullet_score,
                "consistency_percentage": bullet_score,
                "bullet_issues": bullet_issues,
            },
            line_length_analysis={
                "line_length_score": line_length_score,
                "line_length_issues": line_length_issues,
            },
            resume_length_analysis={
                "length_score": resume_length_score,
                "is_appropriate_length": resume_length_score > 80,
                "length_issues": length_issues,
            },
            consistency_analysis={
                "consistency_score": consistency_score,
                "consistency_issues": consistency_issues,
            },
            overall_formatting_score=overall_score,
        )

    def _analyze_spacing(self, lines: List[str]) -> Tuple[float, List[str]]:
        """Analyze spacing with strict measurable rules"""
        if not lines:
            return 100.0, []
            
        rules = FORMATTING_RULES["spacing"]
        
        empty_lines = sum(1 for line in lines if not line.strip())
        total_lines = len(lines)
        empty_ratio = empty_lines / total_lines
        
        issues = []
        violations = 0
        
        # Check empty line ratio against strict rules
        optimal_min = rules["optimal_empty_ratio"]["min"]
        optimal_max = rules["optimal_empty_ratio"]["max"]
        
        if empty_ratio < optimal_min:
            issues.append(f"Insufficient spacing: {empty_ratio:.1%} (minimum {optimal_min:.1%})")
            violations += 1
        elif empty_ratio > optimal_max:
            issues.append(f"Excessive spacing: {empty_ratio:.1%} (maximum {optimal_max:.1%})")
            violations += 1
            
        # Check consecutive empty lines
        consecutive_empty = 0
        max_consecutive = 0
        
        for line in lines:
            if not line.strip():
                consecutive_empty += 1
                max_consecutive = max(max_consecutive, consecutive_empty)
            else:
                consecutive_empty = 0
                
        if max_consecutive > rules["max_consecutive_empty"]:
            issues.append(f"Too many consecutive empty lines: {max_consecutive} (maximum {rules['max_consecutive_empty']})")
            violations += 1
            
        # Calculate score based on violations
        if violations == 0:
            score = 100.0
        else:
            penalty = violations * rules["penalty_per_violation"]
            score = max(100.0 - penalty, 40.0)
            
        return score, issues

    def _analyze_bullets(self, lines: List[str]) -> Tuple[float, List[str]]:
        """Analyze bullet point consistency with detailed issue reporting"""
        bullet_patterns = [r"^\s*[•·\-]\s", r"^\s*\*\s", r"^\s*\d+\.\s"]
        bullet_lines = []
        issues = []

        for i, line in enumerate(lines):
            for pattern in bullet_patterns:
                if re.match(pattern, line):
                    bullet_lines.append((i, line))
                    break

        if len(bullet_lines) < 3:  # Not enough bullets to analyze
            return 100.0, []

        # Check for consistent bullet styles
        bullet_styles = []
        for _, line in bullet_lines:
            if re.match(r"^\s*[•·]\s", line):
                bullet_styles.append("dot")
            elif re.match(r"^\s*\*\s", line):
                bullet_styles.append("star")
            elif re.match(r"^\s*\d+\.\s", line):
                bullet_styles.append("number")
            elif re.match(r"^\s*-\s", line):
                bullet_styles.append("dash")

        if len(set(bullet_styles)) > 1:
            issues.append("Inconsistent bullet point styles used")

        # Check for proper indentation
        indentations = []
        for _, line in bullet_lines:
            indent = len(line) - len(line.lstrip())
            indentations.append(indent)

        if max(indentations) - min(indentations) > 4:
            issues.append("Inconsistent bullet point indentation")

        # Calculate score based on issues
        score = 100.0 - (len(issues) * 15)
        return max(score, 50.0), issues

    def _analyze_line_lengths(self, lines: List[str]) -> Tuple[float, List[str]]:
        """Analyze line length with strict measurable rules"""
        if not lines:
            return 100.0, []

        lines_with_content = [line for line in lines if line.strip()]
        if not lines_with_content:
            return 100.0, []

        rules = FORMATTING_RULES["line_length"]
        lengths = [len(line) for line in lines_with_content]
        
        issues = []
        violations = 0
        
        # Count violations against strict rules
        long_lines = [i for i, length in enumerate(lengths) if length > rules["max_chars"]]
        violations = len(long_lines)
        
        if violations > 0:
            issues.append(f"{violations} lines exceed {rules['max_chars']}-character limit")
            
        # Calculate score based on strict penalty system
        if violations == 0:
            avg_length = sum(lengths) / len(lengths)
            if rules["optimal_min"] <= avg_length <= rules["optimal_max"]:
                score = 100.0
            else:
                score = 90.0
        elif violations <= rules["max_violations_allowed"]:
            penalty = violations * rules["penalty_per_violation"]
            score = max(100.0 - penalty, 60.0)
        else:
            # Major penalty for excessive violations
            score = 50.0
            issues.append("Excessive line length violations detected")

        return score, issues

    def _analyze_resume_length(self, text: str) -> Tuple[float, List[str]]:
        """Analyze resume length with strict measurable rules"""
        word_count = len(text.split())
        rules = FORMATTING_RULES["page_length"]
        
        # Calculate pages based on strict word count
        estimated_pages = word_count / rules["words_per_page"]
        
        issues = []
        
        if estimated_pages < rules["min_pages"]:
            issues.append(f"Resume too short: {estimated_pages:.1f} pages (minimum {rules['min_pages']})")
            score = 60.0
        elif estimated_pages > rules["max_pages"]:
            extra_pages = estimated_pages - rules["max_pages"]
            penalty = extra_pages * rules["penalty_per_extra_page"]
            score = max(100.0 - penalty, 30.0)
            issues.append(f"Resume too long: {estimated_pages:.1f} pages (maximum {rules['max_pages']})")
        elif rules["optimal_min"] <= estimated_pages <= rules["optimal_max"]:
            score = 100.0
        else:
            score = 85.0
            
        return score, issues

    def _analyze_consistency(self, text: str) -> Tuple[float, List[str]]:
        """Analyze formatting consistency with strict measurable rules"""
        rules = FORMATTING_RULES["consistency"]
        issues = []
        violations = 0

        # Check date format consistency (strict: only 1 format allowed)
        if rules["date_format_consistency"]:
            date_formats = self._check_date_format_consistency(text)
            if len(date_formats) > 1:
                issues.append(f"Inconsistent date formats: {len(date_formats)} different formats found")
                violations += 1

        # Check heading case consistency
        if rules["heading_case_consistency"]:
            heading_issues = self._check_heading_consistency(text)
            if heading_issues:
                issues.extend(heading_issues)
                violations += len(heading_issues)

        # Check punctuation consistency in lists
        if rules["punctuation_consistency"]:
            punct_issues = self._check_punctuation_consistency(text)
            if punct_issues:
                issues.extend(punct_issues)
                violations += len(punct_issues)

        # Calculate score based on strict violation count
        if violations == 0:
            score = 100.0
        elif violations <= 2:
            score = 85.0
        elif violations <= 4:
            score = 70.0
        else:
            score = 50.0

        return score, issues
        
    def _check_punctuation_consistency(self, text: str) -> List[str]:
        """Check for consistent punctuation in bullet points"""
        lines = text.split("\\n")
        bullet_endings = []
        
        for line in lines:
            if re.match(r"^\\s*[•●\\-\\*]\\s", line):
                stripped = line.strip()
                if stripped.endswith('.'):
                    bullet_endings.append('period')
                elif stripped.endswith(','):
                    bullet_endings.append('comma')
                elif stripped.endswith(';'):
                    bullet_endings.append('semicolon')
                else:
                    bullet_endings.append('none')
        
        if len(set(bullet_endings)) > 1 and len(bullet_endings) > 3:
            return ["Inconsistent punctuation in bullet points"]
        return []

    def _check_date_format_consistency(self, text: str) -> List[str]:
        """Check for consistent date formatting"""
        date_patterns = [
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b",
            r"\b\d{1,2}/\d{4}\b",
            r"\b\d{4}-\d{1,2}\b",
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b",
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",
        ]

        found_formats = []
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_formats.append(pattern)

        return found_formats

    def _check_heading_consistency(self, text: str) -> List[str]:
        """Check for consistent heading formatting"""
        lines = text.split("\n")
        headings = []
        issues = []

        # Identify potential headings (lines in all caps or with special formatting)
        for line in lines:
            stripped = line.strip()
            if (
                len(stripped) > 2
                and len(stripped) < 50
                and (
                    stripped.isupper()
                    or re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", stripped)
                )
            ):
                headings.append(stripped)

        # Check for consistent heading capitalization
        all_caps = sum(1 for h in headings if h.isupper())
        title_case = sum(
            1 for h in headings if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", h)
        )

        if all_caps > 0 and title_case > 0:
            issues.append("Inconsistent heading capitalization styles")

        return issues

    def analyze_content_quality(self, text: str) -> Dict[str, Any]:
        """Analyze content quality of the resume"""
        issues = []

        # Check for action verbs
        action_verbs = [
            "developed",
            "designed",
            "implemented",
            "managed",
            "led",
            "created",
            "built",
            "improved",
            "optimized",
            "increased",
            "reduced",
            "transformed",
            "spearheaded",
            "coordinated",
            "organized",
        ]

        action_verb_count = 0
        for verb in action_verbs:
            action_verb_count += len(re.findall(rf"\b{verb}\b", text, re.IGNORECASE))

        if action_verb_count < 5:
            issues.append("Limited use of action verbs in experience descriptions")

        # Check for quantifiable achievements
        quant_patterns = [
            r"\b(?:increased|reduced|improved|decreased|saved)\s+(?:by\s+)?\d+%",
            r"\b\d+\s*(?:times|fold)\s+(?:increase|decrease|improvement)",
            r"\b\$(?:\d+[,.]?)+(?:\s+(?:saved|reduced|increased))",
            r"\b\d+\s*(?:people|members|clients|users)",
        ]

        quant_achievements = 0
        for pattern in quant_patterns:
            quant_achievements += len(re.findall(pattern, text, re.IGNORECASE))

        if quant_achievements < 2:
            issues.append("Few quantifiable achievements found")

        # Check for buzzwords (to avoid)
        buzzwords = [
            "synergy",
            "think outside the box",
            "go-getter",
            "hard worker",
            "results-driven",
            "team player",
            "detail-oriented",
            "self-starter",
        ]

        buzzword_count = 0
        for buzzword in buzzwords:
            buzzword_count += len(
                re.findall(rf"\b{re.escape(buzzword)}\b", text, re.IGNORECASE)
            )

        if buzzword_count > 3:
            issues.append("Overuse of clichéd buzzwords")

        # Calculate content quality score
        score = 100.0
        if action_verb_count < 5:
            score -= 15
        if quant_achievements < 2:
            score -= 20
        if buzzword_count > 3:
            score -= 10

        return {
            "score": max(score, 50.0),
            "issues": issues,
            "action_verb_count": action_verb_count,
            "quantifiable_achievements": quant_achievements,
            "buzzword_count": buzzword_count,
        }

    def _calculate_completeness_score(self, results: Dict) -> Dict:
        """Calculate overall completeness score with priority weighting"""
        base_weights = SCORING_CONFIG["completeness_weights"]

        # Apply priority weighting if priorities are set
        if self.priorities:
            weights = self._apply_priority_weighting(base_weights)
        else:
            weights = base_weights

        breakdown = {}
        total_score = 0

        # CGPA score
        cgpa_score = weights["cgpa"] if results["cgpa_results"].cgpa_present else 0
        breakdown["cgpa_score"] = cgpa_score
        total_score += cgpa_score

        # Project dates score
        date_coverage = results["project_date_results"].project_date_coverage
        project_score = int(weights["project_dates"] * date_coverage)
        breakdown["project_dates_score"] = project_score
        total_score += project_score

        # Education levels score
        edu_results = results["education_results"]
        edu_score = sum(
            [
                weights["class_10"] if edu_results.class_10_present else 0,
                weights["class_12"] if edu_results.class_12_present else 0,
                weights["diploma"] if edu_results.diploma_present else 0,
                weights["bachelor"] if edu_results.bachelor_present else 0,
                weights["master"] if edu_results.master_present else 0,
                weights["phd"] if edu_results.phd_present else 0,
            ]
        )
        breakdown["education_score"] = edu_score
        total_score += edu_score

        # Links score
        valid_links = len(results["link_results"].valid_links)
        links_score = min(
            weights["professional_links"],
            valid_links * (weights["professional_links"] / 5),
        )
        breakdown["links_score"] = links_score
        total_score += links_score

        # Content quality score
        content_score = results["content_quality_results"]["score"] * (
            weights["content_quality"] / 100
        )
        breakdown["content_quality_score"] = content_score
        total_score += content_score

        return {"score": min(total_score, 100), "breakdown": breakdown}

    def _apply_priority_weighting(
        self, base_weights: Dict[str, int]
    ) -> Dict[str, float]:
        """Apply priority-based weighting to scoring weights"""
        # Create a copy of base weights to modify
        weighted_weights = base_weights.copy()

        # Get priority fields
        priority_fields = []
        if self.priorities.priority1:
            priority_fields.append(self.priorities.priority1)
        if self.priorities.priority2:
            priority_fields.append(self.priorities.priority2)
        if self.priorities.priority3:
            priority_fields.append(self.priorities.priority3)

        # Apply priority boost (increase weight by 50% for priority fields)
        for field in priority_fields:
            if field in weighted_weights:
                weighted_weights[field] = int(weighted_weights[field] * 1.5)

        # Normalize weights to maintain total
        total_base = sum(base_weights.values())
        total_weighted = sum(weighted_weights.values())

        if total_weighted > total_base:
            scale_factor = total_base / total_weighted
            for field in weighted_weights:
                weighted_weights[field] = int(weighted_weights[field] * scale_factor)

        return weighted_weights

    def _calculate_formatting_score(
        self, formatting_results: FormattingAnalysisResult
    ) -> FormattingAnalysisResult:
        """Calculate and update formatting scores"""
        # The formatting analysis already contains calculated scores
        return formatting_results

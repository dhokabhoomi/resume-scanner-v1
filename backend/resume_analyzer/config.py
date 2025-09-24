"""
Configuration settings for the Resume Analyzer
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# HTTP Validation Settings
HTTP_VALIDATION = {
    "enabled": True,
    "timeout": 5,  # Reduced timeout for faster processing
    "max_retries": 1,  # Fewer retries for speed
    "max_links_per_resume": 5,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    },
}

# Rule-based Validation Settings
RULE_VALIDATION = {
    "cgpa_patterns": [
        r"(?:CGPA|GPA|Grade Point Average)[\s:]*([0-9]\.?[0-9]?[0-9]?)\s*/\s*([0-9]\.?[0-9]?)",
        r"(?:CGPA|GPA|Grade Point Average)[\s:]*([0-9]\.?[0-9]?[0-9]?)",
        r"([0-9]\.?[0-9]?[0-9]?)\s*/\s*([0-9]\.?[0-9]?)\s*(?:CGPA|GPA)",
        r"([0-9]\.?[0-9]?[0-9]?)\s*(?:CGPA|GPA)",
        r"(?:CGPA|GPA)\s*of\s*([0-9]\.?[0-9]?[0-9]?)",
    ],
    "date_patterns": [
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}",
        r"\d{1,2}/\d{4}",
        r"\d{4}-\d{1,2}",
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
        r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
        r"(?:Present|Current|Now|Ongoing)",
    ],
    "education_patterns": {
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
    },
}

# Scoring Configuration
SCORING_CONFIG = {
    "completeness_weights": {
        "cgpa": 15,
        "project_dates": 20,
        "class_10": 8,
        "class_12": 12,
        "diploma": 10,
        "bachelor": 15,
        "master": 10,
        "phd": 10,
        "professional_links": 20,
        "content_quality": 20,
    },
    "formatting_weights": {
        "spacing": 0.2,
        "bullets": 0.2,
        "line_length": 0.2,
        "resume_length": 0.2,
        "consistency": 0.2,
    },
    "section_weights": {
        "basic_info": 10,
        "professional_summary": 10,
        "education": 15,
        "work_experience": 20,
        "projects": 15,
        "skills": 15,
        "certifications": 10,
        "extracurriculars": 5
    },
}

# Strict Formatting Rules (Objective Measurable Criteria)
FORMATTING_RULES = {
    "page_length": {
        "min_pages": 1.0,
        "max_pages": 2.0,
        "optimal_min": 1.0,
        "optimal_max": 2.0,
        "words_per_page": 400,  # More conservative estimate
        "penalty_per_extra_page": 20,  # Points deducted per page over limit
    },
    "line_length": {
        "max_chars": 120,  # Industry standard
        "optimal_min": 50,
        "optimal_max": 100,
        "penalty_per_violation": 2,  # Points deducted per line over limit
        "max_violations_allowed": 5,  # Before major penalty
    },
    "bullet_usage": {
        "min_percentage": 70,  # At least 70% of list items should be bullets
        "required_consistency": True,  # Must use consistent bullet style
        "allowed_styles": ["•", "●", "-", "*"],  # Allowed bullet characters
        "max_indent_variation": 4,  # Max spaces difference in indentation
    },
    "spacing": {
        "max_consecutive_empty": 2,  # Max consecutive empty lines allowed
        "optimal_empty_ratio": {"min": 0.05, "max": 0.15},  # 5-15% empty lines
        "section_separator_lines": 1,  # Lines between sections
        "penalty_per_violation": 5,
    },
    "consistency": {
        "date_format_consistency": True,  # All dates same format
        "heading_case_consistency": True,  # All headings same case style
        "punctuation_consistency": True,  # Consistent punctuation in lists
        "font_emphasis_consistency": True,  # Consistent bold/italic usage
    },
    "content_structure": {
        "required_sections": ["experience", "education", "skills"],  # Core sections
        "max_orphaned_lines": 3,  # Lines not under any clear section
        "min_section_content": 2,  # Min lines per section
    },
}

# Priority Analysis Configuration
PRIORITY_MAPPING = {
    "Technical Skills": {"sections": ["skills"], "rule_based_key": None, "icon": "💻"},
    "Project Experience": {
        "sections": ["projects"],
        "rule_based_key": "project_dates_analysis",
        "icon": "🚀",
    },
    "Academic Performance": {
        "sections": ["education"],
        "rule_based_key": "cgpa_analysis",
        "icon": "🎓",
    },
    "Work Experience": {
        "sections": ["work_experience"],
        "rule_based_key": None,
        "icon": "💼",
    },
    "GitHub Profile": {
        "sections": ["links_found"],
        "rule_based_key": "link_validation_analysis",
        "filter": "github",
        "icon": "🔗",
    },
    "LinkedIn Profile": {
        "sections": ["links_found"],
        "rule_based_key": "link_validation_analysis",
        "filter": "linkedin",
        "icon": "🔗",
    },
    "Certifications": {
        "sections": ["certifications"],
        "rule_based_key": None,
        "icon": "📜",
    },
    "Resume Formatting": {
        "sections": ["formatting_issues"],
        "rule_based_key": "formatting_analysis",
        "icon": "📝",
    },
    "Extracurricular Activities": {
        "sections": ["extracurriculars"],
        "rule_based_key": None,
        "icon": "🏆",
    },
    "Communication Skills": {
        "sections": ["professional_summary", "skills"],
        "rule_based_key": None,
        "icon": "💬",
    },
    "Content Quality": {
        "sections": ["professional_summary", "work_experience", "projects"],
        "rule_based_key": "content_quality_analysis",
        "icon": "📊",
    },
    "Skill Diversity": {
        "sections": ["skills", "projects", "work_experience"],
        "rule_based_key": None,
        "icon": "🎯",
    },
}

# Link Validation Patterns
LINK_PATTERNS = {
    "LINKEDIN": [
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]{3,}/?",
        r"LinkedIn:\s*(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+",
        r"LinkedIn:\s*[a-zA-Z0-9-]{3,}(?:\s|$)",
    ],
    "GITHUB": [
        r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-._]{1,39}(?:/[a-zA-Z0-9-._]+)?/?",
        r"GitHub:\s*(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-._]+",
        r"GitHub:\s*[a-zA-Z0-9-._]{1,39}(?:\s|$)",
    ],
    "PORTFOLIO": [
        r"(?:https?://)?(?:www\.)?[a-zA-Z0-9-]{2,}\.[a-zA-Z]{2,}(?:/[^\s]*)?",
        r"Portfolio:\s*(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}",
        r"Website:\s*(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}",
    ],
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "resume_analyzer.log",
}

# Content Quality Analysis Patterns
CONTENT_QUALITY_PATTERNS = {
    "action_verbs": [
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
    ],
    "quant_patterns": [
        r"\b(?:increased|reduced|improved|decreased|saved)\s+(?:by\s+)?\d+%",
        r"\b\d+\s*(?:times|fold)\s+(?:increase|decrease|improvement)",
        r"\b\$(?:\d+[,.]?)+(?:\s+(?:saved|reduced|increased))",
        r"\b\d+\s*(?:people|members|clients|users)",
    ],
    "buzzwords": [
        "synergy",
        "think outside the box",
        "go-getter",
        "hard worker",
        "results-driven",
        "team player",
        "detail-oriented",
        "self-starter",
    ],
}

"""
Data models for the Resume Analyzer system
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PriorityStatus(str, Enum):
    """Status levels for priority evaluation"""

    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"


class LinkType(str, Enum):
    """Types of links that can be found in resumes"""

    LINKEDIN = "LINKEDIN"
    GITHUB = "GITHUB"
    PORTFOLIO = "PORTFOLIO"
    OTHER = "OTHER"


class ValidationStatus(str, Enum):
    """Validation status for links"""

    VALID = True
    INVALID = False
    UNKNOWN = None


# Request Models
class PriorityAreas(BaseModel):
    """Priority areas for analysis focus"""

    priority1: Optional[str] = Field(None, description="Top priority area")
    priority2: Optional[str] = Field(None, description="Second priority area")
    priority3: Optional[str] = Field(None, description="Third priority area")


class ResumeAnalysisRequest(BaseModel):
    """Request model for resume analysis"""

    priorities: Optional[PriorityAreas] = Field(
        None, description="Priority areas for analysis focus"
    )
    retry_on_fail: bool = Field(
        True, description="Whether to retry on AI analysis failure"
    )


# Core Data Models
class LinkValidationResult(BaseModel):
    """Result of HTTP link validation"""

    url: str
    is_valid: Optional[bool]
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    redirect_count: int = 0
    response_time_ms: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    platform: Optional[str] = None
    ssl_warning: bool = False
    validation_timestamp: Optional[str] = None


class ExtractedLink(BaseModel):
    """Model for links extracted from resume text"""

    type: LinkType
    raw_text: str
    reconstructed_url: str
    valid: Optional[bool] = None
    validation_details: Optional[LinkValidationResult] = None


class LinkAnalysisResult(BaseModel):
    """Results of link analysis"""

    links_found: List[ExtractedLink]
    valid_links: List[ExtractedLink]
    broken_links: List[ExtractedLink]


class CGPAAnalysisResult(BaseModel):
    """Results of CGPA detection"""

    cgpa_present: bool
    cgpa_values: List[str] = []
    cgpa_count: int = 0
    cgpa_contexts: List[str] = []
    scale: str = "unknown"


class ProjectDatesAnalysisResult(BaseModel):
    """Results of project dates analysis"""

    dates_present: bool
    total_dates_found: int = 0
    projects_with_dates: int = 0
    projects_with_date_ranges: int = 0
    total_projects_identified: int = 0
    project_date_coverage: float = 0.0
    date_contexts: List[Dict[str, str]] = []


class EducationAnalysisResult(BaseModel):
    """Results of education level analysis"""

    class_10_present: bool = False
    class_12_present: bool = False
    diploma_present: bool = False
    bachelor_present: bool = False
    master_present: bool = False
    phd_present: bool = False
    education_contexts: List[Dict[str, str]] = []


class FormattingAnalysisResult(BaseModel):
    """Results of formatting analysis"""

    spacing_analysis: Dict[str, Any] = {}
    bullet_point_analysis: Dict[str, Any] = {}
    line_length_analysis: Dict[str, Any] = {}
    resume_length_analysis: Dict[str, Any] = {}
    consistency_analysis: Dict[str, Any] = {}
    overall_formatting_score: float = 100.0


class ContentQualityAnalysis(BaseModel):
    """Results of content quality analysis"""

    score: float = 100.0
    issues: List[str] = []
    action_verb_count: int = 0
    quantifiable_achievements: int = 0
    buzzword_count: int = 0


class RuleBasedFindings(BaseModel):
    """Comprehensive rule-based analysis results"""

    cgpa_analysis: CGPAAnalysisResult
    project_dates_analysis: ProjectDatesAnalysisResult
    education_analysis: EducationAnalysisResult
    link_validation_analysis: LinkAnalysisResult
    formatting_analysis: FormattingAnalysisResult
    content_quality_analysis: ContentQualityAnalysis
    completeness_score: float
    completeness_breakdown: Dict[str, float] = {}
    priority_areas: Dict[str, Optional[str]] = {}


# AI Analysis Models
class SectionAnalysis(BaseModel):
    """Analysis results for a resume section"""

    content: Dict[str, Any]
    quality_score: int = Field(ge=0, le=100)
    suggestions: str


class LinksFoundAnalysis(BaseModel):
    """Analysis of links found in resume"""

    linkedin_present: bool = False
    github_present: bool = False
    portfolio_website_present: bool = False
    other_links_present: bool = False
    all_links_list: List[str] = []
    link_suggestions: str = "Include relevant professional links."


class FormattingIssuesAnalysis(BaseModel):
    """Analysis of formatting issues"""

    has_headshot: bool = False
    headshot_suggestion: str = "Remove headshot if present."
    other_formatting_issues: str = "No suggestions."


class AIAnalysisResult(BaseModel):
    """Complete AI analysis result"""

    basic_info: SectionAnalysis
    professional_summary: SectionAnalysis
    education: SectionAnalysis
    work_experience: SectionAnalysis
    projects: SectionAnalysis
    skills: SectionAnalysis
    certifications: SectionAnalysis
    extracurriculars: SectionAnalysis
    links_found: LinksFoundAnalysis
    formatting_issues: FormattingIssuesAnalysis
    overall_score: int = Field(ge=0, le=100)
    overall_suggestions: str


# Priority Analysis Models
class PriorityFeedback(BaseModel):
    """Feedback for a specific priority area"""

    score: int = Field(ge=0, le=100)
    feedback: List[str]
    icon: str
    status: PriorityStatus


class PriorityAnalysis(BaseModel):
    """Priority-based analysis results"""

    selected_priorities: List[str]
    priority_scores: Dict[str, int]
    priority_feedback: Dict[str, PriorityFeedback]
    overall_priority_score: int = Field(ge=0, le=100)
    total_priorities: int


class FactSheet(BaseModel):
    """Fact sheet summary"""

    summary: str
    completeness_score: int = Field(ge=0, le=100)
    formatting_score: float = Field(ge=0, le=100)
    prompt_was_customized: bool = False


# Priority Selection Model
class PrioritySelection(BaseModel):
    """Model for priority selection"""

    priorities: List[str] = Field(
        default_factory=list, description="Selected priority areas"
    )


# Response Models
class ResumeAnalysisResponse(BaseModel):
    """Complete response for resume analysis"""

    status: str
    analysis: AIAnalysisResult
    rule_based_findings: RuleBasedFindings
    fact_sheet: FactSheet
    priority_analysis: Optional[PriorityAnalysis] = None
    extracted_text_preview: Optional[str] = None
    _enforcement_corrections: Optional[List[str]] = None


# Bulk Processing Models
class BulkJobStatus(str, Enum):
    """Status values for bulk processing jobs"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class CandidateResult(BaseModel):
    """Individual candidate analysis result"""

    filename: str
    candidate_name: Optional[str] = None
    overall_score: int = Field(ge=0, le=100)
    completeness_score: int = Field(ge=0, le=100)
    formatting_score: float = Field(ge=0, le=100)
    key_skills: List[str] = []
    experience_level: str = "fresher"
    education_level: str = "unknown"
    cgpa_found: bool = False
    cgpa_value: Optional[str] = None
    links_status: str = "none"
    valid_links_count: int = 0
    broken_links_count: int = 0
    priority_scores: Optional[Dict[str, int]] = None
    analysis_status: str = "success"
    error_message: Optional[str] = None
    processed_at: Optional[str] = None

    # Add full analysis data for complete analysis access
    full_analysis: Optional[AIAnalysisResult] = None
    rule_based_findings: Optional[RuleBasedFindings] = None
    fact_sheet: Optional[FactSheet] = None
    priority_analysis: Optional[PriorityAnalysis] = None


class BulkAnalysisJob(BaseModel):
    """Bulk analysis job tracking"""

    job_id: str
    status: BulkJobStatus
    total_files: int
    processed_files: int
    successful_analyses: int
    failed_analyses: int
    created_at: str
    completed_at: Optional[str] = None
    results: List[CandidateResult] = []
    error_summary: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class BulkAnalysisRequest(BaseModel):
    """Request model for bulk analysis"""

    priorities: Optional[str] = Field(
        None, description="Comma-separated priority areas"
    )
    job_name: Optional[str] = Field(None, description="Optional job name for tracking")


class BulkAnalysisResponse(BaseModel):
    """Response model for bulk analysis"""

    job_id: str
    status: BulkJobStatus
    message: str
    total_files: int
    results_preview: List[CandidateResult] = []
    download_links: Dict[str, str] = {}


class ExportRequest(BaseModel):
    """Request model for exporting results"""

    job_id: str
    format: str = Field(description="Export format: 'excel' or 'csv'")
    include_detailed_analysis: bool = Field(
        default=False, description="Include detailed section analysis"
    )


class ErrorResponse(BaseModel):
    """Error response model"""

    status: str = "error"
    error: str
    details: Optional[Dict[str, Any]] = None

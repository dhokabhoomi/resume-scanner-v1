"""
AI-powered resume analysis using Google Gemini
"""

import json
import re
import logging
from typing import List, Optional, Dict, Any
import google.generativeai as genai

from .config import GOOGLE_API_KEY, GEMINI_MODEL, PRIORITY_MAPPING, SCORING_CONFIG
from .models import PriorityAnalysis, PriorityFeedback, PriorityStatus, AIAnalysisResult

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Handle AI-powered resume analysis using Google Gemini"""

    def __init__(self):
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Google Gemini model"""
        if not GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY not found in environment variables")
            return

        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            logger.info(f"Initialized Gemini model: {GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None

    def analyze_resume(
        self,
        resume_text: str,
        priorities: Optional[List[str]] = None,
        rule_based_findings: Optional[Dict] = None,
        retry_on_fail: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of resume

        Args:
            resume_text: The extracted resume text
            priorities: Optional list of priority areas for focused analysis
            rule_based_findings: Results from rule-based validation
            retry_on_fail: Whether to retry on analysis failure

        Returns:
            Dictionary containing analysis results
        """
        if not resume_text:
            return {"error": "Empty resume text"}

        if self.model is None:
            return {"error": "AI model not configured. Please check GOOGLE_API_KEY."}

        try:
            # Generate dynamic prompt based on findings and priorities
            prompt = self._generate_dynamic_prompt(
                resume_text, priorities, rule_based_findings
            )

            # Get AI analysis
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()

            # Clean and parse JSON response
            cleaned_response = self._clean_json_response(raw_text)

            # Retry if failed and retry is enabled
            if "error" in cleaned_response and retry_on_fail:
                logger.warning("Retrying with fallback prompt...")
                fallback_prompt = self._create_fallback_prompt(resume_text)
                retry_response = self.model.generate_content(fallback_prompt)
                cleaned_response = self._clean_json_response(
                    retry_response.text.strip()
                )

            # Calculate overall score if not provided
            if "overall_score" not in cleaned_response or cleaned_response["overall_score"] == 0:
                # Calculate section weights from priorities list
                section_weights = None
                if priorities:
                    priority_weights = self._calculate_priority_weights(priorities)
                    section_weights = self._map_priority_weights_to_sections(priority_weights)
                cleaned_response["overall_score"] = self._calculate_overall_score(cleaned_response, section_weights)

            return AIAnalysisResult(**cleaned_response)

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {"error": f"AI analysis failed: {str(e)}"}

    def _generate_dynamic_prompt(
        self,
        resume_text: str,
        priorities: Optional[List[str]] = None,
        rule_based_findings: Optional[Dict] = None,
    ) -> str:
        """Generate dynamic prompt based on rule-based findings and priorities"""

        # Create fact sheet from rule-based findings
        fact_sheet = (
            self._create_fact_sheet(rule_based_findings) if rule_based_findings else ""
        )

        prompt_parts = [
            "You are an expert resume evaluator. Analyze the resume text and provide comprehensive feedback in valid JSON format.",
            "",
        ]

        # Add fact sheet if available
        if fact_sheet:
            prompt_parts.extend(
                [
                    "FACT SHEET - PRE-ANALYSIS FINDINGS:",
                    fact_sheet,
                    "",
                    "IMPORTANT: Use the fact sheet above to inform your analysis. Address gaps indicated by ❌ and ⚠️ symbols.",
                    "",
                ]
            )

        # Add priority-specific instructions or general analysis guidance
        if priorities:
            priority_text = ", ".join(priorities)
            prompt_parts.extend(
                [
                    f"RECRUITER PRIORITIES: {priority_text}",
                    "ANALYSIS REQUIREMENTS:",
                    "- MANDATORY: Analyze ALL sections (basic_info, professional_summary, education, work_experience, projects, skills, certifications, extracurriculars) regardless of priorities",
                    "- MANDATORY: Provide complete content extraction and quality scores for every section",
                    "- MANDATORY: Include specific suggestions for every section, even non-priority ones",
                    "PRIORITY WEIGHTING: After completing full analysis:",
                    "- Apply 50% higher importance to priority areas in overall scoring calculation",
                    "- Provide more detailed and actionable suggestions for priority areas",
                    "- When multiple areas are equally strong, highlight priority area achievements first",
                    "- Overall score should reflect priority area performance more heavily in final calculation",
                    "",
                ]
            )
        else:
            prompt_parts.extend(
                [
                    "GENERAL ANALYSIS MODE:",
                    "Provide a comprehensive, balanced evaluation across all resume aspects including technical skills, experience, education, formatting, and content quality.",
                    "Give equal weight to all sections and provide holistic feedback for overall improvement.",
                    "Apply balanced scoring across all areas without specific emphasis.",
                    "",
                ]
            )

        # Add dynamic scoring guidance based on findings
        if rule_based_findings and "rule_based_findings" in rule_based_findings:
            findings = rule_based_findings["rule_based_findings"]
            prompt_parts.extend(self._generate_scoring_guidance(findings))

        # Add standard rules and schema
        prompt_parts.extend(
            [
                "SCORING AND FEEDBACK RULES:",
                "- Extract only actual resume content into content fields - do not invent details",
                "- Provide realistic quality scores (0-100) based on content presence and quality",
                "- ALWAYS provide specific, actionable suggestions - never use generic placeholders",
                "- Return ONLY valid JSON in the exact schema below",
                "- Output MUST start with '{' and end with '}'",
                "- Never recommend headshots or profile pictures",
                "",
                "CONTENT-BASED SCORING GUIDELINES:",
                "- Completely empty sections: 0 points + suggestions for what to include",
                "- Minimal content (1-2 items): 30-50 points + suggestions for improvement",
                "- Good content (3-4 items): 60-80 points + suggestions for enhancement",
                "- Excellent content (5+ items): 85-100 points + minor improvement suggestions",
                "",
                "SUGGESTION QUALITY REQUIREMENTS:",
                "- Be specific to the section being analyzed",
                "- Mention exactly what is missing or could be improved",
                "- Provide actionable advice relevant to the section",
                "- Use professional, encouraging tone",
                "",
                "SKILLS CATEGORIZATION REQUIREMENTS:",
                "- TECHNICAL SKILLS: Programming languages, frameworks, databases, tools, operating systems",
                "- HARD SKILLS: Domain-specific skills, certifications, methodologies, quantifiable competencies",
                "- SOFT SKILLS: Communication, leadership, problem-solving, interpersonal, adaptability",
                "- Properly categorize each skill into the correct category based on its nature",
                "- Do not mix categories - keep technical and hard skills separate from soft skills",
                "- Focus on clear skill categorization and organization",
                "",
                "COMPREHENSIVE ANALYSIS REQUIREMENT:",
                "You MUST analyze and provide data for ALL sections in the JSON schema below.",
                "Even if priorities are specified, you must still analyze ALL sections completely.",
                "No section should be omitted or have empty content if information exists in the resume.",
                "",
                "MANDATORY CONTENT EXTRACTION RULES:",
                "- ALWAYS extract actual content from the resume into the 'content' field of each section",
                "- If a section exists in the resume, populate ALL relevant fields in the content object",
                "- For skills: Extract skills exactly as they appear in the resume, preserving original formatting and organization",
                "- For work_experience: Extract ALL companies, positions, durations, and specific achievements",
                "- For education: Extract ALL institutions, degrees, dates, and any academic details",
                "- For projects: Extract ALL project names, descriptions, technologies, and outcomes",
                "- Never leave content fields empty if corresponding information exists in the resume",
                "",
                self._get_json_schema(),
                "",
                f"INPUT RESUME TEXT:\\n{resume_text}",
            ]
        )

        return "\\n".join(prompt_parts)

    def _create_fact_sheet(self, rule_based_results: Dict) -> str:
        """Create fact sheet from rule-based analysis"""
        if not rule_based_results or "rule_based_findings" not in rule_based_results:
            return "No pre-analysis data available."

        findings = rule_based_results["rule_based_findings"]
        sections = []

        # CGPA Status
        cgpa = findings.get("cgpa_analysis", {})
        if cgpa.get("cgpa_present"):
            sections.append(f"✅ CGPA: {cgpa.get('cgpa_count', 0)} found")
        else:
            sections.append("❌ CGPA: Missing")

        # Project Dates Status
        dates = findings.get("project_dates_analysis", {})
        if dates.get("dates_present"):
            coverage = int(dates.get("project_date_coverage", 0) * 100)
            sections.append(f"✅ Project Dates: {coverage}% coverage")
        else:
            sections.append("❌ Project Dates: Missing")

        # Formatting Status
        formatting = findings.get("formatting_analysis", {})
        if formatting:
            score = formatting.get("overall_formatting_score", 100)
            if score >= 85:
                sections.append(f"✅ Formatting: {score:.0f}/100")
            elif score >= 70:
                sections.append(f"⚠️ Formatting: {score:.0f}/100")
            else:
                sections.append(f"❌ Formatting: {score:.0f}/100")

        # Links Status
        links = findings.get("link_validation_analysis", {})
        if links:
            valid_count = len(links.get("valid_links", []))
            broken_count = len(links.get("broken_links", []))
            if broken_count > 0:
                sections.append(f"❌ Links: {broken_count} broken")
            elif valid_count > 0:
                sections.append(f"✅ Links: {valid_count} valid")
            else:
                sections.append("⚠️ Links: None found")

        # Overall Completeness
        completeness = findings.get("completeness_score", 0)
        if completeness >= 75:
            sections.append(f"✅ Completeness: {completeness}/100")
        elif completeness >= 50:
            sections.append(f"⚠️ Completeness: {completeness}/100")
        else:
            sections.append(f"❌ Completeness: {completeness}/100")

        return " | ".join(sections)

    def _generate_scoring_guidance(self, findings: Dict) -> List[str]:
        """Generate dynamic scoring guidance based on findings"""
        guidance = ["DYNAMIC SCORING GUIDANCE:"]

        # CGPA guidance
        cgpa_present = findings.get("cgpa_analysis", {}).get("cgpa_present", False)
        if cgpa_present:
            guidance.append(
                "- Education section: Award full points - CGPA information detected"
            )
        else:
            guidance.append(
                "- Education section: Reduce score significantly - CGPA/GPA missing (detected gap)"
            )

        # Project dates guidance
        project_coverage = findings.get("project_dates_analysis", {}).get(
            "project_date_coverage", 0
        )
        if project_coverage >= 0.8:
            guidance.append(
                "- Projects section: Award full points - good date coverage detected"
            )
        else:
            guidance.append(
                "- Projects section: Reduce score due to missing/incomplete project dates (detected gap)"
            )

        # Formatting guidance
        format_score = findings.get("formatting_analysis", {}).get(
            "overall_formatting_score", 100
        )
        guidance.append(
            f"- Overall formatting: Base assessment on detected formatting score of {format_score:.0f}/100"
        )

        guidance.extend(
            [
                "",
                "ADAPTIVE SUGGESTIONS - Address the specific gaps detected above. Avoid generic advice when specific issues are identified.",
                "",
            ]
        )

        return guidance

    def _create_fallback_prompt(self, resume_text: str) -> str:
        """Create fallback prompt when rule-based analysis fails"""
        return f"""
You are an expert resume evaluator. Analyze the resume text and provide comprehensive feedback in valid JSON format.

Since automated pre-analysis was unavailable, pay extra attention to:
- Completeness of all sections
- Presence of dates in projects and experience  
- Academic performance metrics (CGPA/GPA)
- Formatting consistency
- Professional presentation

{self._get_json_schema()}

INPUT RESUME TEXT:
{resume_text}
"""

    def _get_json_schema(self) -> str:
        """Get the standard JSON schema for resume analysis"""
        return """REQUIRED JSON STRUCTURE:
{
  "basic_info": {
    "content": {"name": "extracted_name", "email": "email@example.com", "phone": "phone_number", "location": "city_state"},
    "quality_score": [15-100 based on completeness],
    "suggestions": "specific advice for improving contact information"
  },
  "professional_summary": {
    "content": {"summary_text": "extracted_summary_content"},
    "quality_score": [15-100 based on quality and presence],
    "suggestions": "specific advice about summary content, length, and focus"
  },
  "education": {
    "content": {"institutions": ["school_names"], "degrees": ["degree_types"], "dates": ["graduation_dates"]},
    "quality_score": [15-100 based on completeness],
    "suggestions": "specific advice about missing CGPA, dates, or institution details"
  },
  "work_experience": {
    "content": {"companies": ["company_names"], "positions": ["job_titles"], "durations": ["time_periods"], "achievements": ["accomplishments"]},
    "quality_score": [15-100 based on depth and relevance],
    "suggestions": "specific advice about quantifying achievements, adding responsibilities, or formatting"
  },
  "projects": {
    "content": {"project_names": ["project_titles"], "descriptions": ["project_details"]},
    "quality_score": [15-100 based on technical depth and dates],
    "suggestions": "specific advice about adding dates, technologies used, or project outcomes"
  },
  "skills": {
    "content": {
      "original_format": "skills exactly as written in the resume, preserving original structure and formatting",
      "is_properly_categorized": "boolean - true if skills are already organized into technical/hard/soft categories",
      "technical_skills": {
        "programming_languages": ["only if already categorized in resume, otherwise empty"],
        "frameworks_libraries": ["only if already categorized in resume, otherwise empty"],
        "databases": ["only if already categorized in resume, otherwise empty"],
        "tools_software": ["only if already categorized in resume, otherwise empty"],
        "operating_systems": ["only if already categorized in resume, otherwise empty"]
      },
      "hard_skills": {
        "domain_specific": ["only if already categorized in resume, otherwise empty"],
        "certifications": ["only if already categorized in resume, otherwise empty"],
        "methodologies": ["only if already categorized in resume, otherwise empty"],
        "quantifiable_skills": ["only if already categorized in resume, otherwise empty"]
      },
      "soft_skills": {
        "communication": ["only if already categorized in resume, otherwise empty"],
        "leadership": ["only if already categorized in resume, otherwise empty"],
        "problem_solving": ["only if already categorized in resume, otherwise empty"],
        "interpersonal": ["only if already categorized in resume, otherwise empty"],
        "adaptability": ["only if already categorized in resume, otherwise empty"]
      },
      "languages": ["spoken languages mentioned in resume"]
    },
    "quality_score": [15-100 based on relevance, organization, and skill depth],
    "suggestions": "if is_properly_categorized is false, suggest organizing skills into technical/hard/soft categories. Otherwise provide suggestions for missing relevant skills or better organization"
  },
  "certifications": {
    "content": {"certification_names": ["cert_names"], "issuing_organizations": ["cert_providers"], "dates": ["cert_dates"]},
    "quality_score": [15-100 based on relevance and completeness],
    "suggestions": "specific advice about adding relevant certifications, dates, or certification providers"
  },
  "extracurriculars": {
    "content": {"activities": ["activity_names"], "roles": ["leadership_positions"], "durations": ["time_periods"]},
    "quality_score": [15-100 based on leadership and relevance],
    "suggestions": "specific advice about highlighting leadership, adding dates, or describing impact"
  },
  "links_found": {
    "linkedin_present": false,
    "github_present": false,
    "portfolio_website_present": false,
    "other_links_present": false,
    "all_links_list": [],
    "link_suggestions": "Include relevant professional links."
  },
  "formatting_issues": {
    "has_headshot": false,
    "headshot_suggestion": "Remove headshot if present.",
    "other_formatting_issues": "No suggestions."
  },
  "overall_score": [0-100 based on weighted average of all section scores],
  "overall_suggestions": "Comprehensive suggestions based on all section analysis"
}"""

    def _clean_json_response(self, raw_text: str) -> Dict[str, Any]:
        """Clean and parse AI response to valid JSON"""
        try:
            # Remove markdown formatting
            cleaned = re.sub(r"```(?:json)?", "", raw_text)
            cleaned = cleaned.strip()

            # Find JSON boundaries
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1


            json_str = cleaned[start:end]

            # Parse JSON
            result = json.loads(json_str)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            # Try to fix common JSON issues
            try:
                fixed_json = self._fix_common_json_issues(json_str)
                result = json.loads(fixed_json)
                return result
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": raw_text[:500]}
        except Exception as e:
            logger.error(f"Response cleaning failed: {e}")
            return {"error": f"Response processing failed: {str(e)}"}

    def _fix_common_json_issues(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        # Remove trailing commas
        json_str = re.sub(r",(\s*[}\]])", r"\\1", json_str)

        # Fix unescaped quotes in strings
        json_str = re.sub(r'(?<!\\)"(?=(?:[^"\\\\]|\\\\.)*("|$))', '\\\\"', json_str)

        return json_str

    def create_priority_analysis(
        self, ai_analysis: Dict, priorities: List[str], rule_based_results: Dict
    ) -> Optional[PriorityAnalysis]:
        """Create priority-based evaluation from AI analysis and rule-based findings"""
        if not priorities:
            return None

        priority_scores = {}
        priority_feedback = {}
        findings = (
            rule_based_results.get("rule_based_findings", {})
            if rule_based_results
            else {}
        )

        for priority in priorities:
            if priority not in PRIORITY_MAPPING:
                continue

            mapping = PRIORITY_MAPPING[priority]
            section_scores = []
            feedback_parts = []

            # Get AI analysis scores for relevant sections
            for section_name in mapping["sections"]:
                if section_name in ai_analysis and isinstance(
                    ai_analysis[section_name], dict
                ):
                    section = ai_analysis[section_name]
                    score = section.get("quality_score", 0)
                    suggestions = section.get("suggestions", "")

                    section_scores.append(score)

                    if suggestions and suggestions != "No suggestions.":
                        feedback_parts.append(
                            f"{section_name.replace('_', ' ').title()}: {suggestions}"
                        )

            # Apply rule-based findings adjustments
            section_scores = self._apply_rule_based_adjustments(
                priority, section_scores, feedback_parts, findings, mapping
            )

            # Calculate final priority score
            priority_score = (
                sum(section_scores) / len(section_scores) if section_scores else 0
            )

            # Determine status
            if priority_score >= 85:
                status = PriorityStatus.EXCELLENT
            elif priority_score >= 70:
                status = PriorityStatus.GOOD
            elif priority_score >= 50:
                status = PriorityStatus.NEEDS_IMPROVEMENT
            else:
                status = PriorityStatus.CRITICAL

            priority_scores[priority] = round(priority_score)
            priority_feedback[priority] = PriorityFeedback(
                score=round(priority_score),
                feedback=(
                    feedback_parts if feedback_parts else ["No specific issues found."]
                ),
                icon=mapping["icon"],
                status=status,
            )

        # Calculate overall priority score
        overall_score = (
            sum(priority_scores.values()) / len(priority_scores)
            if priority_scores
            else 0
        )

        return PriorityAnalysis(
            selected_priorities=priorities,
            priority_scores=priority_scores,
            priority_feedback=priority_feedback,
            overall_priority_score=round(overall_score),
            total_priorities=len(priorities),
        )

    def _apply_rule_based_adjustments(
        self,
        priority: str,
        section_scores: List[int],
        feedback_parts: List[str],
        findings: Dict,
        mapping: Dict,
    ) -> List[int]:
        """Apply rule-based findings to adjust scores and feedback"""
        rule_key = mapping.get("rule_based_key")

        if not rule_key or rule_key not in findings:
            return section_scores

        rule_data = findings[rule_key]

        if priority == "Project Experience":
            if not rule_data.get("dates_present"):
                feedback_parts.insert(
                    0, "❌ Missing project dates - significantly impacts credibility"
                )
                section_scores = [max(0, s - 25) for s in section_scores]
            elif rule_data.get("project_date_coverage", 0) < 0.7:
                coverage = rule_data.get("project_date_coverage", 0) * 100
                feedback_parts.insert(
                    0, f"⚠️ Only {coverage:.0f}% of projects have dates"
                )
                section_scores = [max(0, s - 15) for s in section_scores]
            else:
                feedback_parts.insert(0, "✅ Good project date coverage")

        elif priority == "Academic Performance":
            if not rule_data.get("cgpa_present"):
                feedback_parts.insert(
                    0, "❌ No CGPA/GPA found - academic performance unclear"
                )
                section_scores = [max(0, s - 20) for s in section_scores]
            else:
                cgpa_count = rule_data.get("cgpa_count", 0)
                feedback_parts.insert(0, f"✅ {cgpa_count} academic score(s) found")

        elif priority == "Resume Formatting":
            format_score = rule_data.get("overall_formatting_score", 100)
            if format_score < 70:
                feedback_parts.insert(
                    0, f"❌ Poor formatting detected (score: {format_score:.0f}/100)"
                )
                section_scores = [format_score] + section_scores
            elif format_score < 85:
                feedback_parts.insert(
                    0, f"⚠️ Minor formatting issues (score: {format_score:.0f}/100)"
                )
                section_scores = [format_score] + section_scores
            else:
                feedback_parts.insert(
                    0, f"✅ Good formatting (score: {format_score:.0f}/100)"
                )
                section_scores = [format_score] + section_scores

        elif priority in ["GitHub Profile", "LinkedIn Profile"]:
            valid_links = rule_data.get("valid_links", [])
            broken_links = rule_data.get("broken_links", [])

            platform = "GitHub" if "github" in priority.lower() else "LinkedIn"
            platform_links = [
                link
                for link in valid_links
                if platform.lower()
                in link.get("validation_details", {}).get("platform", "").lower()
            ]
            platform_broken = [
                link
                for link in broken_links
                if platform.lower()
                in link.get("validation_details", {}).get("platform", "").lower()
            ]

            if platform_broken:
                feedback_parts.insert(0, f"❌ Broken {platform} link found")
                section_scores = [max(0, s - 30) for s in section_scores]
            elif platform_links:
                feedback_parts.insert(0, f"✅ Valid {platform} profile found")
                section_scores = [min(100, s + 10) for s in section_scores]
            else:
                feedback_parts.insert(0, f"⚠️ No {platform} profile found")
                section_scores = [max(0, s - 10) for s in section_scores]

        return section_scores

    def _calculate_overall_score(self, analysis_data: Dict[str, Any], section_weights: Optional[Dict[str, int]] = None) -> int:
        """Calculate overall score from section scores using configurable or priority-based weights"""
        try:
            # Use provided section weights or default section weights
            if section_weights is None:
                section_weights = SCORING_CONFIG.get("section_weights", {
                    "basic_info": 10,
                    "professional_summary": 10,
                    "education": 15,
                    "work_experience": 20,
                    "projects": 15,
                    "skills": 15,
                    "certifications": 10,
                    "extracurriculars": 5
                })

            weighted_score = 0
            total_weight = 0

            for section, weight in section_weights.items():
                if section in analysis_data and isinstance(analysis_data[section], dict):
                    section_score = analysis_data[section].get("quality_score", 0)
                    if isinstance(section_score, (int, float)) and section_score > 0:
                        weighted_score += section_score * weight
                        total_weight += weight

            # Calculate final score
            if total_weight > 0:
                overall_score = round(weighted_score / total_weight)
                return max(0, min(100, overall_score))  # Ensure score is between 0-100
            else:
                return 0

        except Exception as e:
            logger.warning(f"Failed to calculate overall score: {e}")
            return 0

    def _calculate_priority_weights(self, priorities: List[str]) -> Dict[str, int]:
        """Calculate scoring weights based on priority order"""
        if not priorities or len(priorities) == 0:
            return {}

        total_priorities = len(priorities)
        weights = {}

        # Calculate weights using a descending scale
        for i, priority in enumerate(priorities):
            # Weight formula: (totalPriorities - index) / sum of (1 to totalPriorities) * 100
            weight = round(((total_priorities - i) / self._sum_of_integers(total_priorities)) * 100)
            weights[priority] = weight

        # Adjust for rounding errors to ensure total is exactly 100
        total_weight = sum(weights.values())
        if total_weight != 100 and len(priorities) > 0:
            difference = 100 - total_weight
            weights[priorities[0]] += difference

        return weights

    def _sum_of_integers(self, n: int) -> int:
        """Helper function to calculate sum of integers from 1 to n"""
        return (n * (n + 1)) // 2

    def _map_priority_weights_to_sections(self, priority_weights: Dict[str, int]) -> Dict[str, int]:
        """Map priority labels to backend section names"""
        # Mapping from frontend priority labels to backend section names
        section_mapping = {
            "Technical Skills": "skills",
            "Work Experience": "work_experience",
            "Academic Performance": "education",
            "Project Experience": "projects",
            "Resume Formatting": "formatting",
            "Certifications": "certifications",
            "Extracurricular Activities": "extracurriculars",
            "Communication Skills": "professional_summary",
            "Content Quality": "professional_summary",
            "Skill Diversity": "skills",
            "GitHub Profile": "basic_info",
            "LinkedIn Profile": "basic_info",
            "CGPA Scores": "education"
        }

        # Initialize section weights
        section_weights = {
            "basic_info": 0,
            "professional_summary": 0,
            "education": 0,
            "work_experience": 0,
            "projects": 0,
            "skills": 0,
            "certifications": 0,
            "extracurriculars": 0
        }

        # Map priority weights to sections
        for priority, weight in priority_weights.items():
            section = section_mapping.get(priority)
            if section and section in section_weights:
                section_weights[section] += weight

        # If no priorities mapped to a section, distribute remaining weight evenly
        total_mapped = sum(section_weights.values())
        if total_mapped < 100:
            remaining = 100 - total_mapped
            unmapped_sections = [s for s, w in section_weights.items() if w == 0]

            if unmapped_sections:
                weight_per_section = remaining // len(unmapped_sections)
                remainder = remaining % len(unmapped_sections)

                for i, section in enumerate(unmapped_sections):
                    section_weights[section] = weight_per_section
                    if i < remainder:  # Distribute remainder
                        section_weights[section] += 1

        return section_weights

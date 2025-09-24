"""
Post-processing module for score enforcement and validation
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ScoreEnforcer:
    """Handle intelligent score enforcement and validation"""

    def enforce_scores_with_facts(
        self, analysis: Dict[str, Any], rule_based_results: Dict[str, Any], priorities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Intelligent score enforcement that validates AI response against known facts

        Args:
            analysis: AI analysis results
            rule_based_results: Rule-based validation results

        Returns:
            Analysis with enforced and corrected scores
        """
        # Handle Pydantic model objects by converting to dict
        if hasattr(analysis, 'model_dump'):
            analysis = analysis.model_dump()
        elif hasattr(analysis, 'dict'):
            analysis = analysis.dict()

        if not rule_based_results or "rule_based_findings" not in rule_based_results:
            return self._enforce_basic_consistency(analysis)

        findings = rule_based_results["rule_based_findings"]
        corrections_made = []

        # Extract key facts
        cgpa_present = findings.get("cgpa_analysis", {}).get("cgpa_present", False)
        project_dates_coverage = findings.get("project_dates_analysis", {}).get(
            "project_date_coverage", 0
        )
        project_dates_present = findings.get("project_dates_analysis", {}).get(
            "dates_present", False
        )
        formatting_score = findings.get("formatting_analysis", {}).get(
            "overall_formatting_score", 100
        )
        completeness_score = findings.get("completeness_score", 100)

        # Education Section Validation
        corrections_made.extend(self._enforce_education_scores(analysis, cgpa_present))

        # Projects Section Validation
        corrections_made.extend(
            self._enforce_project_scores(
                analysis, project_dates_present, project_dates_coverage
            )
        )

        # Overall Score Validation
        corrections_made.extend(
            self._enforce_overall_score(analysis, completeness_score, priorities)
        )

        # Formatting Validation
        corrections_made.extend(
            self._enforce_formatting_scores(analysis, findings, formatting_score)
        )

        # Comprehensive section validation
        corrections_made.extend(self._validate_all_sections(analysis, findings))

        # Additional cross-validation
        corrections_made.extend(self._validate_ai_consistency(analysis, findings))

        # Apply basic consistency checks
        analysis = self._enforce_basic_consistency(analysis)

        # Log corrections if any were made
        if corrections_made:
            logger.info(f"Score enforcement corrections: {'; '.join(corrections_made)}")
            analysis["_enforcement_corrections"] = corrections_made

        return analysis

    def _enforce_education_scores(
        self, analysis: Dict, cgpa_present: bool
    ) -> List[str]:
        """Enforce education section scores based on CGPA presence"""
        corrections = []

        if "education" in analysis and isinstance(analysis["education"], dict):
            edu_section = analysis["education"]
            edu_score = edu_section.get("quality_score", 0)
            edu_suggestions = edu_section.get("suggestions", "").strip()

            # If CGPA is missing but AI gave high score, correct it
            if not cgpa_present and edu_score > 85:
                original_score = edu_score
                edu_section["quality_score"] = min(75, edu_score)
                corrections.append(
                    f"Education score reduced from {original_score} to {edu_section['quality_score']} due to missing CGPA"
                )

                # Ensure suggestions mention CGPA if not already there
                if (
                    "cgpa" not in edu_suggestions.lower()
                    and "gpa" not in edu_suggestions.lower()
                ):
                    if edu_suggestions == "No suggestions." or not edu_suggestions:
                        edu_section["suggestions"] = (
                            "Include CGPA/GPA information to demonstrate academic performance."
                        )
                    else:
                        edu_section[
                            "suggestions"
                        ] += " Also include CGPA/GPA information to demonstrate academic performance."
                    corrections.append("Added CGPA suggestion to education section")

        return corrections

    def _enforce_project_scores(
        self, analysis: Dict, dates_present: bool, date_coverage: float
    ) -> List[str]:
        """Enforce project section scores based on date information"""
        corrections = []

        if "projects" in analysis and isinstance(analysis["projects"], dict):
            proj_section = analysis["projects"]
            proj_score = proj_section.get("quality_score", 0)
            proj_suggestions = proj_section.get("suggestions", "").strip()

            # If project dates are missing/incomplete but AI gave high score, correct it
            if not dates_present and proj_score > 80:
                original_score = proj_score
                proj_section["quality_score"] = min(
                    65, proj_score
                )  # Significant penalty
                corrections.append(
                    f"Projects score reduced from {original_score} to {proj_section['quality_score']} due to missing project dates"
                )

                # Ensure suggestions mention dates
                if "date" not in proj_suggestions.lower():
                    if proj_suggestions == "No suggestions." or not proj_suggestions:
                        proj_section["suggestions"] = (
                            "Add start and end dates for all projects to establish timeline and credibility."
                        )
                    else:
                        proj_section[
                            "suggestions"
                        ] += " Add start and end dates for all projects."
                    corrections.append("Added date suggestion to projects section")

            elif date_coverage < 0.7 and proj_score > 85:
                # Partial coverage should still get some penalty
                original_score = proj_score
                coverage_penalty = int(
                    (1 - date_coverage) * 20
                )  # Up to 20 point penalty
                proj_section["quality_score"] = max(70, proj_score - coverage_penalty)
                corrections.append(
                    f"Projects score adjusted from {original_score} to {proj_section['quality_score']} due to incomplete date coverage ({int(date_coverage * 100)}%)"
                )

        return corrections

    def _enforce_overall_score(
        self, analysis: Dict, completeness_score: int, priorities: Optional[List[str]] = None
    ) -> List[str]:
        """Enforce overall score based on completeness"""
        corrections = []

        if completeness_score < 50 and analysis.get("overall_score", 0) > 70:
            original_overall = analysis.get("overall_score", 0)
            analysis["overall_score"] = min(60, analysis.get("overall_score", 0))
            corrections.append(
                f"Overall score reduced from {original_overall} to {analysis['overall_score']} due to low completeness ({completeness_score}/100)"
            )

        return corrections

    def _enforce_formatting_scores(
        self, analysis: Dict, findings: Dict, formatting_score: float
    ) -> List[str]:
        """Enforce formatting-related scores"""
        corrections = []

        if formatting_score < 70 and "formatting_issues" in analysis:
            format_section = analysis["formatting_issues"]
            other_issues = format_section.get("other_formatting_issues", "").strip()

            if other_issues == "No suggestions." or not other_issues:
                # AI missed formatting issues that were detected
                format_issues = []

                spacing_issues = (
                    findings.get("formatting_analysis", {})
                    .get("spacing_analysis", {})
                    .get("spacing_issues", [])
                )
                if spacing_issues:
                    format_issues.extend(spacing_issues)

                bullet_consistency = (
                    findings.get("formatting_analysis", {})
                    .get("bullet_point_analysis", {})
                    .get("consistency_percentage", 100)
                )
                if bullet_consistency < 80:
                    format_issues.append(
                        f"Inconsistent bullet points ({bullet_consistency:.0f}% consistency)"
                    )

                if format_issues:
                    format_section["other_formatting_issues"] = "; ".join(format_issues)
                    corrections.append(
                        "Added detected formatting issues that AI missed"
                    )

        return corrections

    def _validate_ai_consistency(self, analysis: Dict, findings: Dict) -> List[str]:
        """Additional validation to ensure AI response consistency with facts"""
        corrections = []

        # Check if overall score is reasonable compared to section scores
        section_scores = []
        critical_sections = ["education", "projects", "work_experience"]

        for section in critical_sections:
            if section in analysis and isinstance(analysis[section], dict):
                score = analysis[section].get("quality_score", 0)
                if isinstance(score, (int, float)):
                    section_scores.append(score)

        if section_scores:
            avg_critical_score = sum(section_scores) / len(section_scores)
            overall_score = analysis.get("overall_score", 0)

            # Overall score shouldn't be much higher than average of critical sections
            if overall_score > avg_critical_score + 20:
                original_overall = overall_score
                analysis["overall_score"] = int(
                    min(overall_score, avg_critical_score + 15)
                )
                corrections.append(
                    f"Overall score adjusted from {original_overall} to {analysis['overall_score']} (too high compared to section average {avg_critical_score:.1f})"
                )

        # Validate suggestions match detected issues
        completeness_score = findings.get("completeness_score", 100)
        if completeness_score < 60:
            overall_suggestions = analysis.get("overall_suggestions", "").strip()
            if (
                overall_suggestions == "No overall suggestions."
                or not overall_suggestions
            ):
                # AI failed to provide suggestions despite low completeness
                key_issues = []
                if not findings.get("cgpa_analysis", {}).get("cgpa_present"):
                    key_issues.append("missing academic performance metrics")
                if not findings.get("project_dates_analysis", {}).get("dates_present"):
                    key_issues.append("missing project dates")

                if key_issues:
                    analysis["overall_suggestions"] = (
                        f"Address critical gaps: {', '.join(key_issues)}. Consider adding more comprehensive information to improve resume completeness."
                    )
                    corrections.append(
                        "Added overall suggestions due to detected completeness issues"
                    )

        # Check for contradictory high scores when multiple issues exist
        major_issues = 0
        if not findings.get("cgpa_analysis", {}).get("cgpa_present"):
            major_issues += 1
        if not findings.get("project_dates_analysis", {}).get("dates_present"):
            major_issues += 1
        if (
            findings.get("formatting_analysis", {}).get("overall_formatting_score", 100)
            < 70
        ):
            major_issues += 1

        if major_issues >= 2 and analysis.get("overall_score", 0) > 75:
            original_score = analysis.get("overall_score", 0)
            penalty = min(20, major_issues * 8)
            analysis["overall_score"] = max(
                55, analysis.get("overall_score", 0) - penalty
            )
            corrections.append(
                f"Overall score reduced from {original_score} to {analysis['overall_score']} due to {major_issues} major detected issues"
            )

        return corrections

    def _enforce_basic_consistency(self, analysis: Dict) -> Dict[str, Any]:
        """Basic score enforcement for consistency (fallback when no facts available)"""
        # Handle Pydantic model objects by converting to dict
        if hasattr(analysis, 'model_dump'):
            analysis = analysis.model_dump()
        elif hasattr(analysis, 'dict'):
            analysis = analysis.dict()

        # Define default suggestions for empty sections
        default_suggestions = {
            "basic_info": "Include complete contact information with name, email, phone, and location.",
            "professional_summary": "Add a professional summary that highlights your key qualifications and career objectives.",
            "education": "Include educational background with institution names, degrees, and graduation dates.",
            "work_experience": "Add work experience with company names, positions, dates, and quantified achievements.",
            "projects": "Include technical projects with names, descriptions, technologies used, and dates.",
            "skills": "Add relevant technical skills, soft skills, and programming languages organized by category.",
            "certifications": "Consider adding relevant certifications with issuing organizations and dates.",
            "extracurriculars": "Include extracurricular activities, leadership roles, and volunteer work with dates and impact descriptions.",
        }

        for section, data in analysis.items():
            if isinstance(data, dict) and "quality_score" in data:
                if not isinstance(data["quality_score"], int):
                    data["quality_score"] = 0

                if "suggestions" in data:
                    suggestions = data["suggestions"].strip()

                    # Handle empty or generic suggestions
                    if (
                        not suggestions
                        or suggestions == "No suggestions."
                        or "profile picture" in suggestions.lower()
                        or "headshot" in suggestions.lower()
                    ):

                        # If score is high (85+), keep "No suggestions."
                        if data["quality_score"] >= 85:
                            data["suggestions"] = (
                                "Consider minor refinements to further enhance this section."
                            )
                        else:
                            # Use content-aware suggestions for lower scores
                            if section in default_suggestions:
                                data["suggestions"] = default_suggestions[section]
                            else:
                                data["suggestions"] = (
                                    "Consider adding more relevant content to strengthen this section."
                                )

                    # Handle contradictory high scores with detailed suggestions
                    elif data["quality_score"] == 100 and len(suggestions) > 20:
                        logger.warning(
                            f"Section '{section}' has score 100 but detailed suggestions: {suggestions}"
                        )
                        data["quality_score"] = (
                            95  # Slight adjustment for contradiction
                        )

        # Handle overall scoring
        if "overall_score" not in analysis:
            # Calculate reasonable overall score from section averages
            section_scores = []
            for section, data in analysis.items():
                if isinstance(data, dict) and "quality_score" in data:
                    section_scores.append(data["quality_score"])

            if section_scores:
                analysis["overall_score"] = round(
                    sum(section_scores) / len(section_scores)
                )
            else:
                analysis["overall_score"] = 50

        # Handle overall suggestions
        if (
            "overall_suggestions" not in analysis
            or not analysis["overall_suggestions"].strip()
        ):
            if analysis.get("overall_score", 0) >= 80:
                analysis["overall_suggestions"] = (
                    "Your resume shows strong potential. Focus on the specific suggestions above to optimize each section."
                )
            else:
                analysis["overall_suggestions"] = (
                    "Strengthen your resume by addressing the key areas highlighted in each section above."
                )

        return analysis

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
            "Resume Formatting": "formatting_issues",
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
            "extracurriculars": 0,
            "formatting_issues": 0
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

    def enforce_headshot_rule(self, analysis: Dict) -> Dict[str, Any]:
        """Enforce the no-headshot rule for professional resumes"""
        if "formatting_issues" in analysis and isinstance(
            analysis["formatting_issues"], dict
        ):
            has_headshot = analysis["formatting_issues"].get("has_headshot", False)

            if has_headshot:
                analysis["formatting_issues"][
                    "headshot_suggestion"
                ] = "Remove the headshot; photos are not recommended in professional resumes."
            else:
                analysis["formatting_issues"][
                    "headshot_suggestion"
                ] = "No suggestions regarding headshots."

        return analysis

    def _validate_all_sections(self, analysis: Dict, findings: Dict) -> List[str]:
        """Comprehensive validation for all resume sections"""
        corrections = []

        # Define section validation rules
        section_rules = {
            "basic_info": {
                "required_fields": ["name", "email"],
                "min_score_if_empty": 0,
                "default_suggestions": "Include complete contact information with name, email, phone, and location.",
            },
            "professional_summary": {
                "content_key": "summary_text",
                "min_length": 20,
                "min_score_if_empty": 0,
                "default_suggestions": "Add a professional summary that highlights your key qualifications and career objectives.",
            },
            "work_experience": {
                "content_keys": ["companies", "positions"],
                "min_items": 1,
                "min_score_if_empty": 0,
                "default_suggestions": "Include work experience with company names, positions, dates, and quantified achievements.",
            },
            "projects": {
                "content_keys": ["project_names"],
                "min_items": 1,
                "min_score_if_empty": 0,
                "default_suggestions": "Add technical projects with names, descriptions, technologies used, and dates.",
            },
            "skills": {
                "content_keys": ["technical_skills"],
                "min_items": 3,
                "min_score_if_empty": 0,
                "min_score_if_few": 30,
                "default_suggestions": "Include relevant technical skills, soft skills, and programming languages organized by category.",
            },
            "certifications": {
                "content_keys": ["certification_names"],
                "min_items": 0,
                "optional": True,
                "min_score_if_empty": 0,
                "default_suggestions": "Consider adding relevant certifications with issuing organizations and dates.",
            },
            "extracurriculars": {
                "content_keys": ["activities"],
                "min_items": 0,
                "optional": True,
                "min_score_if_empty": 0,
                "default_suggestions": "Include extracurricular activities, leadership roles, and volunteer work with dates and impact descriptions.",
            },
        }

        for section_name, rules in section_rules.items():
            if section_name in analysis and isinstance(analysis[section_name], dict):
                section = analysis[section_name]
                content = section.get("content", {})
                score = section.get("quality_score", 0)
                suggestions = section.get("suggestions", "").strip()

                # Check content completeness
                is_empty = self._is_section_empty(content, rules)
                is_minimal = self._is_section_minimal(content, rules)

                # Validate empty sections
                if is_empty:
                    # Empty sections should always be 0, regardless if optional or not
                    if score > 0:
                        original_score = score
                        section["quality_score"] = 0
                        corrections.append(
                            f"{section_name} score reduced from {original_score} to 0 due to completely empty content"
                        )

                    # Ensure proper suggestions for empty sections
                    if (
                        suggestions in ["No suggestions.", ""]
                        or "LinkedIn" in suggestions
                    ):
                        section["suggestions"] = rules["default_suggestions"]
                        corrections.append(
                            f"Improved {section_name} suggestions for empty content"
                        )

                # Validate minimal sections
                elif is_minimal:
                    max_allowed = rules.get("min_score_if_few", 60)
                    if score > max_allowed:
                        original_score = score
                        section["quality_score"] = max_allowed
                        corrections.append(
                            f"{section_name} score reduced from {original_score} to {section['quality_score']} due to minimal content"
                        )

                # Validate suggestion quality
                if suggestions in ["No suggestions.", ""] and score < 85:
                    section["suggestions"] = rules["default_suggestions"]
                    corrections.append(
                        f"Added meaningful suggestions to {section_name}"
                    )

                # Check for inappropriate suggestions (like LinkedIn profile picture)
                if (
                    "profile picture" in suggestions.lower()
                    or "headshot" in suggestions.lower()
                ):
                    section["suggestions"] = rules["default_suggestions"]
                    corrections.append(
                        f"Replaced inappropriate suggestion in {section_name}"
                    )

        return corrections

    def _is_section_empty(self, content: Dict, rules: Dict) -> bool:
        """Check if a section has no meaningful content"""
        if not content:
            return True

        # Check basic info special case
        if "required_fields" in rules:
            return not any(content.get(field) for field in rules["required_fields"])

        # Check content keys
        if "content_key" in rules:
            text = content.get(rules["content_key"], "")
            return not text or len(text.strip()) < rules.get("min_length", 5)

        # Check content arrays
        if "content_keys" in rules:
            for key in rules["content_keys"]:
                items = content.get(key, [])
                if isinstance(items, list) and len(items) > 0:
                    return False
            return True

        return False

    def _is_section_minimal(self, content: Dict, rules: Dict) -> bool:
        """Check if a section has minimal content"""
        if self._is_section_empty(content, rules):
            return False

        min_items = rules.get("min_items", 2)

        if "content_keys" in rules:
            total_items = 0
            for key in rules["content_keys"]:
                items = content.get(key, [])
                if isinstance(items, list):
                    total_items += len(items)
            return total_items < min_items

        return False

"""
Bulk Resume Processing Module
Handles batch processing of multiple resumes and export functionality
"""

import os
import uuid
import asyncio
import tempfile
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

from .models import (
    BulkAnalysisJob,
    CandidateResult,
    BulkJobStatus,
    ResumeAnalysisResponse,
    AIAnalysisResult,
    PriorityAnalysis,
)
from .pdf_processor import PDFProcessor
from .rule_validator import RuleBasedValidator
from .ai_analyzer import AIAnalyzer
from .post_processor import ScoreEnforcer

logger = logging.getLogger(__name__)


class BulkProcessor:
    """Handles bulk resume processing operations"""

    def __init__(self):
        self.jobs: Dict[str, BulkAnalysisJob] = {}
        self.pdf_processor = PDFProcessor()
        self.rule_validator = RuleBasedValidator()
        self.ai_analyzer = AIAnalyzer()
        self.score_enforcer = ScoreEnforcer()
        self.max_concurrent_jobs = 5
        self.max_files_per_job = 100

    def create_bulk_job(
        self,
        file_count: int,
        priorities: Optional[str] = None,
        job_name: Optional[str] = None,
    ) -> str:
        """Create a new bulk processing job"""
        job_id = str(uuid.uuid4())

        job = BulkAnalysisJob(
            job_id=job_id,
            status=BulkJobStatus.PENDING,
            total_files=file_count,
            processed_files=0,
            successful_analyses=0,
            failed_analyses=0,
            created_at=datetime.now().isoformat(),
            results=[],
        )

        self.jobs[job_id] = job
        logger.info(f"Created bulk job {job_id} for {file_count} files")
        return job_id

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    BATCH_SIZE = 10  # Configurable batch size

    async def process_bulk_resumes(
        self, job_id: str, file_paths: List[str], priorities: Optional[str] = None
    ) -> BulkAnalysisJob:
        """Process multiple resumes in parallel"""

        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]
        job.status = BulkJobStatus.PROCESSING

        start_time = datetime.now()
        priority_list = None
        if priorities:
            priority_list = [p.strip() for p in priorities.split(",") if p.strip()]

        try:
            # Process files in batches to avoid overwhelming the system
            results = []

            for i in range(0, len(file_paths), self.BATCH_SIZE):
                batch = file_paths[i : i + self.BATCH_SIZE]
                batch_results = await self._process_batch(batch, priority_list)
                results.extend(batch_results)

                # Update job progress
                job.processed_files += len(batch)
                job.successful_analyses += sum(
                    1 for r in batch_results if r.analysis_status == "success"
                )
                job.failed_analyses += sum(
                    1 for r in batch_results if r.analysis_status == "error"
                )

                logger.info(
                    f"Job {job_id}: Processed batch {i//self.BATCH_SIZE + 1}, total progress: {job.processed_files}/{job.total_files}"
                )

            job.results = results
            job.status = (
                BulkJobStatus.COMPLETED
                if job.failed_analyses == 0
                else BulkJobStatus.PARTIAL
            )
            job.completed_at = datetime.now().isoformat()
            job.processing_time_seconds = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Job {job_id} completed: {job.successful_analyses} success, {job.failed_analyses} failed"
            )

        except Exception as e:
            job.status = BulkJobStatus.FAILED
            job.error_summary = str(e)
            job.completed_at = datetime.now().isoformat()
            logger.error(f"Job {job_id} failed: {e}")

        return job

    async def _process_batch(
        self, file_paths: List[str], priorities: Optional[List[str]]
    ) -> List[CandidateResult]:
        """Process a batch of files in parallel"""
        tasks = []

        for file_path in file_paths:
            task = self._process_single_resume(file_path, priorities)
            tasks.append(task)

        # Process batch concurrently with limit
        semaphore = asyncio.Semaphore(self.max_concurrent_jobs)

        async def bounded_process(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[bounded_process(task) for task in tasks], return_exceptions=True
        )

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = CandidateResult(
                    filename=os.path.basename(file_paths[i]),
                    overall_score=0,
                    completeness_score=0,
                    formatting_score=0,
                    analysis_status="error",
                    error_message=str(result),
                    processed_at=datetime.now().isoformat(),
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        return processed_results

    async def _process_single_resume(
        self, file_path: str, priorities: Optional[List[str]], timeout: int = 300
    ) -> CandidateResult:
        """
        Process a single resume file with retry and timeout mechanisms.
        Args:
            file_path: The path to the resume file.
            priorities: Optional list of priority areas.
            timeout: Maximum time in seconds to allow for processing a single resume.
        Returns:
            A CandidateResult object containing the analysis results or error.
        """
        filename = os.path.basename(file_path)
        last_error_message = ""

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.MAX_RETRIES} for {filename}")
                return await asyncio.wait_for(
                    self._perform_single_resume_analysis(file_path, priorities),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                last_error_message = f"Processing timed out after {timeout} seconds"
                logger.error(f"Timeout processing {filename}: {last_error_message}")
            except ValueError as e:
                last_error_message = f"Data validation error: {e}"
                logger.error(f"Validation error for {filename}: {last_error_message}")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                last_error_message = f"Unexpected error: {e}"
                logger.error(f"Error processing {filename}: {last_error_message}")
                logger.error(f"Full error traceback for {filename}:\n{error_details}")

            if attempt < self.MAX_RETRIES - 1:
                logger.warning(
                    f"Retrying {filename} in {self.RETRY_DELAY_SECONDS} seconds..."
                )
                await asyncio.sleep(self.RETRY_DELAY_SECONDS)
            else:
                logger.error(
                    f"All {self.MAX_RETRIES} attempts failed for {filename}."
                )

        return CandidateResult(
            filename=filename,
            overall_score=0,
            completeness_score=0,
            formatting_score=0,
            analysis_status="error",
            error_message=last_error_message,
            processed_at=datetime.now().isoformat(),
        )

    async def _perform_single_resume_analysis(
        self, file_path: str, priorities: Optional[List[str]]
    ) -> CandidateResult:
        """Internal helper to perform the actual analysis for a single resume."""
        filename = os.path.basename(file_path)

        # Step 1: Extract and preprocess text
        clean_text = await self._extract_and_preprocess_text(file_path)

        # Step 2: Run rule-based and AI analyses
        rule_results, ai_results = await self._run_analyses(
            clean_text, priorities
        )

        # Step 3: Enforce scores and extract candidate info
        return self._enforce_scores_and_extract_info(
            ai_results, rule_results, priorities, filename
        )

    async def _extract_and_preprocess_text(self, file_path: str) -> str:
        """Extracts, validates, and preprocesses text from a PDF file."""
        extracted_text = await asyncio.get_event_loop().run_in_executor(
            None, self.pdf_processor.extract_text, file_path
        )

        if not extracted_text:
            raise ValueError("Failed to extract text from PDF")

        if not self.pdf_processor.validate_extracted_text(extracted_text):
            raise ValueError("Extracted text does not appear to be a valid resume")

        return self.pdf_processor.preprocess_text(extracted_text)

    async def _run_analyses(
        self, clean_text: str, priorities: Optional[List[str]]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Runs rule-based and AI analyses on the preprocessed text."""
        rule_results = await asyncio.get_event_loop().run_in_executor(
            None, self.rule_validator.run_all_checks, clean_text
        )

        if "error" in rule_results:
            rule_results = {"rule_based_findings": {}}

        ai_results = await asyncio.get_event_loop().run_in_executor(
            None,
            self.ai_analyzer.analyze_resume,
            clean_text,
            priorities,
            rule_results,
        )

        if "error" in ai_results:
            raise ValueError(f"AI analysis failed: {ai_results['error']}")

        return rule_results, ai_results

    def _enforce_scores_and_extract_info(
        self,
        ai_results: Dict[str, Any],
        rule_results: Dict[str, Any],
        priorities: Optional[List[str]],
        filename: str,
    ) -> CandidateResult:
        """Enforces scores and extracts candidate information to form a CandidateResult."""
        # Convert AIAnalysisResult object to dict if needed
        if hasattr(ai_results, 'model_dump'):
            ai_results_dict = ai_results.model_dump()
        elif hasattr(ai_results, 'dict'):
            ai_results_dict = ai_results.dict()
        else:
            ai_results_dict = ai_results

        enforced_analysis = self.score_enforcer.enforce_scores_with_facts(
            ai_results_dict, rule_results
        )
        enforced_analysis = self.score_enforcer.enforce_headshot_rule(
            enforced_analysis
        )

        enforced_analysis = AIAnalysisResult(**enforced_analysis)

        candidate_name = self._extract_candidate_name(enforced_analysis)
        key_skills = self._extract_key_skills(enforced_analysis)
        experience_level = self._determine_experience_level(enforced_analysis)
        education_level = self._determine_education_level(enforced_analysis)

        cgpa_analysis = rule_results.get("rule_based_findings", {}).get(
            "cgpa_analysis", {}
        )
        cgpa_found = cgpa_analysis.get("cgpa_present", False)
        cgpa_value = (
            cgpa_analysis.get("cgpa_values", [None])[0]
            if cgpa_analysis.get("cgpa_values")
            else None
        )

        link_analysis = rule_results.get("rule_based_findings", {}).get(
            "link_validation_analysis", {}
        )
        valid_links_count = len(link_analysis.get("valid_links", []))
        broken_links_count = len(link_analysis.get("broken_links", []))
        links_status = (
            "valid"
            if valid_links_count > 0
            else ("broken" if broken_links_count > 0 else "none")
        )

        priority_analysis_result = None
        if priorities:
            priority_analysis_result = self.ai_analyzer.create_priority_analysis(
                ai_results, priorities, rule_results
            )
            priority_scores = (
                priority_analysis_result.priority_scores
                if priority_analysis_result
                else None
            )

        # Create fact sheet
        rule_findings = rule_results.get("rule_based_findings", {})
        fact_sheet_obj = {
            "summary": self._create_fact_sheet_summary(rule_findings),
            "completeness_score": int(rule_findings.get("completeness_score", 0)),
            "formatting_score": float(rule_findings.get("formatting_analysis", {}).get("overall_formatting_score", 0)),
            "prompt_was_customized": bool(priorities)
        }

        return CandidateResult(
            filename=filename,
            candidate_name=candidate_name,
            overall_score=enforced_analysis.overall_score,
            completeness_score=int(
                rule_results.get("rule_based_findings", {}).get(
                    "completeness_score", 0
                )
            ),
            formatting_score=rule_results.get("rule_based_findings", {})
            .get("formatting_analysis", {})
            .get("overall_formatting_score", 0),
            key_skills=key_skills,
            experience_level=experience_level,
            education_level=education_level,
            cgpa_found=cgpa_found,
            cgpa_value=cgpa_value,
            links_status=links_status,
            valid_links_count=valid_links_count,
            broken_links_count=broken_links_count,
            priority_scores=priority_scores,
            analysis_status="success",
            processed_at=datetime.now().isoformat(),

            # Add full analysis data
            full_analysis=enforced_analysis,
            rule_based_findings=rule_findings,
            fact_sheet=fact_sheet_obj,
            priority_analysis=priority_analysis_result,
        )

    def _extract_candidate_name(self, analysis) -> Optional[str]:
        """Extract candidate name from analysis"""
        try:
            # Handle both dict and object formats
            if hasattr(analysis, "basic_info"):
                basic_info = analysis.basic_info
                if hasattr(basic_info, "content"):
                    basic_info = basic_info.content
            elif isinstance(analysis, dict) and "basic_info" in analysis:
                basic_info = analysis["basic_info"]
                if isinstance(basic_info, dict) and "content" in basic_info:
                    basic_info = basic_info["content"]
            else:
                return None

            if isinstance(basic_info, dict):
                # Look for name in various possible keys
                name_keys = [
                    "name",
                    "full_name",
                    "candidate_name",
                    "Name",
                    "Full Name",
                    "candidate",
                    "full name",
                ]
                for key in name_keys:
                    if key in basic_info and basic_info[key]:
                        return str(basic_info[key]).strip()
            return None
        except Exception as e:
            logger.warning(f"Error extracting candidate name: {e}")
            return None

    def _extract_key_skills(self, analysis) -> List[str]:
        """Extract key skills from analysis"""
        try:
            # Handle both dict and object formats
            if hasattr(analysis, "skills"):
                skills_content = analysis.skills
                if hasattr(skills_content, "content"):
                    skills_content = skills_content.content
            elif isinstance(analysis, dict) and "skills" in analysis:
                skills_content = analysis["skills"]
                if isinstance(skills_content, dict) and "content" in skills_content:
                    skills_content = skills_content["content"]
            else:
                return []

            if isinstance(skills_content, dict):
                skills_list = []
                for key, value in skills_content.items():
                    if isinstance(value, list):
                        skills_list.extend(value)
                    elif isinstance(value, str):
                        # Split comma-separated skills
                        skills_list.extend(
                            [s.strip() for s in value.split(",") if s.strip()]
                        )
                return skills_list[:10]  # Limit to top 10 skills
            return []
        except Exception as e:
            logger.warning(f"Error extracting skills: {e}")
            return []

    def _determine_experience_level(self, analysis) -> str:
        """Determine experience level from work experience"""
        try:
            # Handle both dict and object formats
            if hasattr(analysis, "work_experience"):
                work_exp = analysis.work_experience
                if hasattr(work_exp, "content"):
                    work_exp = work_exp.content
            elif isinstance(analysis, dict) and "work_experience" in analysis:
                work_exp = analysis["work_experience"]
                if isinstance(work_exp, dict) and "content" in work_exp:
                    work_exp = work_exp["content"]
            else:
                return "fresher"

            if isinstance(work_exp, dict):
                # Look for years of experience or number of jobs
                work_text = str(work_exp).lower()
                if any(
                    keyword in work_text
                    for keyword in [
                        "year",
                        "experience",
                        "worked",
                        "developer",
                        "engineer",
                    ]
                ):
                    if any(num in work_text for num in ["2", "3", "4", "5"]):
                        return "experienced"
                    else:
                        return "entry_level"
                elif any(work_exp.values()):
                    return "entry_level"
            return "fresher"
        except Exception as e:
            logger.warning(f"Error determining experience level: {e}")
            return "fresher"

    def _determine_education_level(self, analysis) -> str:
        """Determine highest education level"""
        try:
            # Handle both dict and object formats
            if hasattr(analysis, "education"):
                education = analysis.education
                if hasattr(education, "content"):
                    education = education.content
            elif isinstance(analysis, dict) and "education" in analysis:
                education = analysis["education"]
                if isinstance(education, dict) and "content" in education:
                    education = education["content"]
            else:
                return "unknown"

            if isinstance(education, dict):
                education_str = str(education).lower()
                if any(
                    degree in education_str
                    for degree in ["phd", "doctorate", "ph.d", "doctor"]
                ):
                    return "phd"
                elif any(
                    degree in education_str
                    for degree in ["master", "mtech", "mba", "ms", "m.tech", "m.sc"]
                ):
                    return "masters"
                elif any(
                    degree in education_str
                    for degree in [
                        "bachelor",
                        "btech",
                        "be",
                        "bsc",
                        "b.tech",
                        "b.sc",
                        "b.e",
                    ]
                ):
                    return "bachelors"
                elif any(degree in education_str for degree in ["diploma"]):
                    return "diploma"
            return "unknown"
        except Exception as e:
            logger.warning(f"Error determining education level: {e}")
            return "unknown"

    def _create_fact_sheet_summary(self, findings: dict) -> str:
        """Create a readable fact sheet summary for API response"""
        if not findings:
            return "No pre-analysis data available."

        summary_parts = []

        # CGPA Status
        cgpa = findings.get("cgpa_analysis", {})
        if cgpa.get("cgpa_present"):
            summary_parts.append(f"✅ CGPA: {cgpa.get('cgpa_count', 0)} found")
        else:
            summary_parts.append("❌ CGPA: Missing")

        # Project Dates Status
        dates = findings.get("project_dates_analysis", {})
        if dates.get("dates_present"):
            coverage = int(dates.get("project_date_coverage", 0) * 100)
            summary_parts.append(f"✅ Project Dates: {coverage}% coverage")
        else:
            summary_parts.append("❌ Project Dates: Missing")

        # Formatting Status
        formatting = findings.get("formatting_analysis", {})
        if formatting:
            format_score = formatting.get("overall_formatting_score", 0)
            if format_score >= 85:
                summary_parts.append(f"✅ Formatting: {format_score:.0f}/100")
            elif format_score >= 70:
                summary_parts.append(f"⚠️ Formatting: {format_score:.0f}/100")
            else:
                summary_parts.append(f"❌ Formatting: {format_score:.0f}/100")

        # Links Status
        link_analysis = findings.get("link_validation_analysis", {})
        if link_analysis:
            valid_links = len(link_analysis.get("valid_links", []))
            broken_links = len(link_analysis.get("broken_links", []))

            if broken_links > 0:
                summary_parts.append(f"❌ Links: {broken_links} broken")
            elif valid_links > 0:
                summary_parts.append(f"✅ Links: {valid_links} valid")
            else:
                summary_parts.append("⚠️ Links: None found")

        # Overall Completeness
        completeness = findings.get("completeness_score", 0)
        if completeness >= 75:
            summary_parts.append(f"✅ Completeness: {completeness}/100")
        elif completeness >= 50:
            summary_parts.append(f"⚠️ Completeness: {completeness}/100")
        else:
            summary_parts.append(f"❌ Completeness: {completeness}/100")

        return " | ".join(summary_parts)

    def get_job_status(self, job_id: str) -> Optional[BulkAnalysisJob]:
        """Get status of a bulk processing job"""
        return self.jobs.get(job_id)

    def export_results_to_excel(
        self, job_id: str, include_detailed: bool = False
    ) -> str:
        """Export results to Excel format"""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if not job.results:
            raise ValueError(f"Job {job_id} has no results to export")

        # Create temporary Excel file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        temp_file.close()

        try:
            # Convert results to DataFrame
            data = []
            for result in job.results:
                row = {
                    "Filename": result.filename,
                    "Candidate Name": result.candidate_name or "Not Found",
                    "Overall Score": result.overall_score,
                    "Completeness Score": result.completeness_score,
                    "Formatting Score": f"{result.formatting_score:.1f}",
                    "Key Skills": (
                        ", ".join(result.key_skills) if result.key_skills else "None"
                    ),
                    "Experience Level": result.experience_level.title(),
                    "Education Level": result.education_level.title(),
                    "CGPA Found": "Yes" if result.cgpa_found else "No",
                    "CGPA Value": result.cgpa_value or "N/A",
                    "Links Status": result.links_status.title(),
                    "Valid Links": result.valid_links_count,
                    "Broken Links": result.broken_links_count,
                    "Analysis Status": result.analysis_status.title(),
                    "Error Message": result.error_message or "",
                    "Processed At": result.processed_at,
                }

                # Add priority scores if available
                if result.priority_scores:
                    for priority, score in result.priority_scores.items():
                        row[f"{priority} Score"] = score

                data.append(row)

            df = pd.DataFrame(data)

            # Create Excel file with multiple sheets
            with pd.ExcelWriter(temp_file.name, engine="openpyxl") as writer:
                # Main results sheet
                df.to_excel(writer, sheet_name="Resume Analysis Results", index=False)

                # Summary sheet
                summary_data = {
                    "Metric": [
                        "Total Resumes",
                        "Successfully Processed",
                        "Failed Processing",
                        "Average Overall Score",
                        "Average Completeness Score",
                        "Average Formatting Score",
                        "Resumes with CGPA",
                        "Resumes with Valid Links",
                        "Processing Time (seconds)",
                    ],
                    "Value": [
                        job.total_files,
                        job.successful_analyses,
                        job.failed_analyses,
                        f"{df['Overall Score'].mean():.1f}" if not df.empty else "0",
                        (
                            f"{df['Completeness Score'].mean():.1f}"
                            if not df.empty
                            else "0"
                        ),
                        (
                            f"{df['Formatting Score'].astype(float).mean():.1f}"
                            if not df.empty
                            else "0"
                        ),
                        sum(1 for r in job.results if r.cgpa_found),
                        sum(1 for r in job.results if r.valid_links_count > 0),
                        (
                            f"{job.processing_time_seconds:.2f}"
                            if job.processing_time_seconds
                            else "N/A"
                        ),
                    ],
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

            logger.info(f"Excel export created for job {job_id}: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e

    def export_results_to_csv(self, job_id: str) -> str:
        """Export results to CSV format"""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if not job.results:
            raise ValueError(f"Job {job_id} has no results to export")

        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w")
        temp_file.close()

        try:
            # Convert results to DataFrame
            data = []
            for result in job.results:
                row = {
                    "filename": result.filename,
                    "candidate_name": result.candidate_name or "",
                    "overall_score": result.overall_score,
                    "completeness_score": result.completeness_score,
                    "formatting_score": result.formatting_score,
                    "key_skills": (
                        ", ".join(result.key_skills) if result.key_skills else ""
                    ),
                    "experience_level": result.experience_level,
                    "education_level": result.education_level,
                    "cgpa_found": result.cgpa_found,
                    "cgpa_value": result.cgpa_value or "",
                    "links_status": result.links_status,
                    "valid_links_count": result.valid_links_count,
                    "broken_links_count": result.broken_links_count,
                    "analysis_status": result.analysis_status,
                    "error_message": result.error_message or "",
                    "processed_at": result.processed_at,
                }

                # Add priority scores if available
                if result.priority_scores:
                    for priority, score in result.priority_scores.items():
                        row[f'{priority.lower().replace(" ", "_")}_score'] = score

                data.append(row)

            df = pd.DataFrame(data)
            df.to_csv(temp_file.name, index=False)

            logger.info(f"CSV export created for job {job_id}: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e


# Global instance
bulk_processor = BulkProcessor()

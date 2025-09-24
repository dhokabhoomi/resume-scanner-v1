"""
Asynchronous processing utilities for improved performance
"""

import asyncio
import concurrent.futures
from typing import Dict, Any, Optional, List
import logging
import time

logger = logging.getLogger(__name__)


class AsyncProcessor:
    """Handle asynchronous processing of resume analysis components"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def process_resume_parallel(
        self,
        resume_text: str,
        pdf_processor,
        rule_validator,
        ai_analyzer,
        score_enforcer,
        priorities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Process resume components in parallel for better performance

        Args:
            resume_text: Extracted resume text
            pdf_processor: PDF processing instance
            rule_validator: Rule validation instance
            ai_analyzer: AI analysis instance
            score_enforcer: Score enforcement instance
            priorities: Optional priority areas

        Returns:
            Combined analysis results
        """
        start_time = time.time()

        # Run rule-based validation and AI analysis in parallel
        tasks = []

        # Task 1: Rule-based validation (CPU-intensive)
        rule_task = asyncio.create_task(
            self._run_rule_validation_async(rule_validator, resume_text)
        )
        tasks.append(("rule_validation", rule_task))

        # Task 2: AI analysis (IO-intensive)
        ai_task = asyncio.create_task(
            self._run_ai_analysis_async(ai_analyzer, resume_text, priorities)
        )
        tasks.append(("ai_analysis", ai_task))

        # Wait for both tasks to complete
        results = {}
        for task_name, task in tasks:
            try:
                results[task_name] = await task
                logger.info(f"Completed {task_name}")
            except Exception as e:
                logger.error(f"Task {task_name} failed: {e}")
                results[task_name] = {"error": str(e)}

        # Process results sequentially (fast operations)
        if "rule_validation" in results and "ai_analysis" in results:
            rule_results = results["rule_validation"]
            ai_results = results["ai_analysis"]

            if "error" not in rule_results and "error" not in ai_results:
                # Apply score enforcement
                enforced_results = score_enforcer.enforce_scores_with_facts(
                    ai_results, rule_results
                )
                enforced_results = score_enforcer.enforce_headshot_rule(
                    enforced_results
                )

                # Generate priority analysis if needed
                priority_analysis = None
                if priorities:
                    priority_analysis = ai_analyzer.create_priority_analysis(
                        enforced_results, priorities, rule_results
                    )

                processing_time = time.time() - start_time
                logger.info(f"Total processing time: {processing_time:.2f}s")

                return {
                    "analysis": enforced_results,
                    "rule_based_findings": rule_results.get("rule_based_findings", {}),
                    "priority_analysis": priority_analysis,
                    "processing_time": processing_time,
                    "parallel_processing": True,
                }

        # Fallback to sequential processing if parallel failed
        logger.warning("Parallel processing failed, falling back to sequential")
        return await self._fallback_sequential_processing(
            resume_text, rule_validator, ai_analyzer, score_enforcer, priorities
        )

    async def _run_rule_validation_async(
        self, rule_validator, resume_text: str
    ) -> Dict[str, Any]:
        """Run rule-based validation asynchronously"""
        loop = asyncio.get_event_loop()

        # Run CPU-intensive rule validation in thread pool
        return await loop.run_in_executor(
            self.executor, rule_validator.run_all_checks, resume_text
        )

    async def _run_ai_analysis_async(
        self, ai_analyzer, resume_text: str, priorities: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Run AI analysis asynchronously"""
        loop = asyncio.get_event_loop()

        # Run IO-intensive AI analysis in thread pool
        return await loop.run_in_executor(
            self.executor, lambda: ai_analyzer.analyze_resume(resume_text, priorities)
        )

    async def _fallback_sequential_processing(
        self,
        resume_text: str,
        rule_validator,
        ai_analyzer,
        score_enforcer,
        priorities: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Fallback sequential processing"""
        start_time = time.time()

        # Sequential processing
        rule_results = rule_validator.run_all_checks(resume_text)
        ai_results = ai_analyzer.analyze_resume(resume_text, priorities, rule_results)

        if "error" not in ai_results:
            enforced_results = score_enforcer.enforce_scores_with_facts(
                ai_results, rule_results
            )
            enforced_results = score_enforcer.enforce_headshot_rule(enforced_results)

            priority_analysis = None
            if priorities:
                priority_analysis = ai_analyzer.create_priority_analysis(
                    enforced_results, priorities, rule_results
                )

            processing_time = time.time() - start_time
            logger.info(f"Sequential processing time: {processing_time:.2f}s")

            return {
                "analysis": enforced_results,
                "rule_based_findings": rule_results.get("rule_based_findings", {}),
                "priority_analysis": priority_analysis,
                "processing_time": processing_time,
                "parallel_processing": False,
            }

        return {"error": "Both parallel and sequential processing failed"}

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)


# Caching utilities
class ResumeCache:
    """Simple in-memory cache for resume analysis results"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.timestamps = {}

    def _generate_key(
        self, resume_text: str, priorities: Optional[List[str]] = None
    ) -> str:
        """Generate cache key from resume content"""
        import hashlib

        content = resume_text + (str(sorted(priorities)) if priorities else "")
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def get(
        self, resume_text: str, priorities: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired"""
        key = self._generate_key(resume_text, priorities)

        if key in self.cache:
            # Check if expired
            if time.time() - self.timestamps[key] < self.ttl_seconds:
                logger.info("Cache hit - returning cached analysis")
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.timestamps[key]

        return None

    def set(
        self,
        resume_text: str,
        result: Dict[str, Any],
        priorities: Optional[List[str]] = None,
    ):
        """Cache the analysis result"""
        key = self._generate_key(resume_text, priorities)

        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = result
        self.timestamps[key] = time.time()
        logger.info("Cached analysis result")

    def clear(self):
        """Clear all cached results"""
        self.cache.clear()
        self.timestamps.clear()


# Global instances
async_processor = AsyncProcessor()
resume_cache = ResumeCache()

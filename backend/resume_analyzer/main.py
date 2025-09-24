"""
Main FastAPI application for the Resume Analyzer
"""

import os
import logging
import tempfile
import traceback
import time
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from .models import (
    ResumeAnalysisResponse,
    ErrorResponse,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    ExportRequest,
    BulkAnalysisJob,
)
from .pdf_processor import PDFProcessor
from .rule_validator import RuleBasedValidator
from .ai_analyzer import AIAnalyzer
from .post_processor import ScoreEnforcer
from .config import LOGGING_CONFIG
from .bulk_processor import bulk_processor
from .logger import setup_logging, get_logger, LogContext
from .validators import (
    validate_file_upload, 
    validate_file_content, 
    PriorityValidator, 
    JobNameValidator,
    ValidatedAnalysisRequest,
    ValidatedBulkRequest
)
from .rate_limiter import rate_limiter, rate_limit_middleware
from .performance_optimizer import optimized_processor
from .enhanced_cache import enhanced_cache

# Setup enhanced logging
setup_logging(
    log_level=LOGGING_CONFIG.get('level', 'INFO'),
    log_file=LOGGING_CONFIG.get('file', 'logs/resume_analyzer.log'),
    enable_console=True,
    enable_colors=True
)

logger = get_logger(__name__)
logger.info("Starting Resume Analyzer API...")

# Fallback logging configuration
try:
    fallback_level = getattr(logging, LOGGING_CONFIG.get("level", "INFO"), logging.INFO)
    logging.basicConfig(
        level=fallback_level,
        format=LOGGING_CONFIG.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )
except Exception as e:
    print(f"Warning: Failed to configure basic logging: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="VU Resume Analyzer",
    description="AI-powered resume analysis with bulk processing, export capabilities, and placement cell features",
    version="1.2.0",
)

# Configure CORS
allowed_origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Add production URLs if specified
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_origin_regex="http://localhost:\\d+"
)

logger.info(f"CORS Middleware configured with allowed_origins: {allowed_origins} and allow_origin_regex: http://localhost:\\d+")

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with enhanced logging"""
    logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.method} {request.url.path}: {error_details}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Request validation failed",
            "details": error_details,
            "status_code": 422,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(exc)}"
    
    logger.error(
        f"Unhandled exception [{error_id}] on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    # In development, return detailed error info
    if os.getenv("ENVIRONMENT", "development").lower() == "development":
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Internal server error",
                "details": str(exc),
                "error_id": error_id,
                "status_code": 500,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    else:
        # In production, return generic error message
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Internal server error occurred",
                "error_id": error_id,
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }
        )

# Rate limiting middleware - TEMPORARILY DISABLED FOR TESTING
# @app.middleware("http")
# async def apply_rate_limiting(request: Request, call_next):
#     """Apply rate limiting to all requests"""
#     return await rate_limit_middleware(request, call_next)

# Request logging middleware with rate limit headers
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing and add rate limit headers"""
    start_time = datetime.now()
    
    # Log incoming request
    logger.info(f"⬇️  {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Add rate limiting headers to response
        try:
            client_id = rate_limiter._get_client_id(request)
            if client_id in rate_limiter.clients:
                client_record = rate_limiter.clients[client_id]
                endpoint_category = rate_limiter._get_endpoint_category(request.url.path, request.method)
                rule = rate_limiter.rules.get(endpoint_category, rate_limiter.rules['default'])
                
                # Calculate remaining requests in current window
                current_time = time.time()
                window_start = current_time - rule.window
                recent_requests = [req for req in client_record.requests if req > window_start]
                remaining = max(0, (rule.requests + rule.burst) - len(recent_requests))
                
                # Add headers
                response.headers["X-RateLimit-Limit"] = str(rule.requests + rule.burst)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Window"] = str(rule.window)
        except Exception:
            pass  # Don't fail the response if header addition fails
        
        # Log response
        status_emoji = "✅" if response.status_code < 400 else "❌" if response.status_code >= 500 else "⚠️"
        logger.info(f"⬆️  {status_emoji} {response.status_code} {request.method} {request.url.path} - {duration:.3f}s")
        
        return response
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"💥 {request.method} {request.url.path} - Error after {duration:.3f}s: {str(e)}")
        raise

# Initialize components
pdf_processor = PDFProcessor()
rule_validator = RuleBasedValidator()
ai_analyzer = AIAnalyzer()
score_enforcer = ScoreEnforcer()

# Application startup
@app.on_event("startup")
async def startup_event():
    """Initialize application state"""
    import time
    app.state.start_time = time.time()
    logger.info("🚀 Resume Analyzer API started successfully!")

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get application metrics for monitoring"""
    from .async_processor import async_processor, resume_cache
    import time
    
    start_time = getattr(app.state, 'start_time', time.time())
    uptime = time.time() - start_time
    
    return {
        "timestamp": datetime.now().isoformat(),
        "uptime": {
            "seconds": uptime,
            "human_readable": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
        },
        "cache": {
            "total_entries": len(resume_cache.cache),
            "cache_hits": getattr(resume_cache, 'hits', 0),
            "cache_misses": getattr(resume_cache, 'misses', 0)
        },
        "async_processor": {
            "max_workers": async_processor.max_workers,
            "active_tasks": getattr(async_processor, 'active_tasks', 0)
        },
        "components": {
            "pdf_processor_ready": pdf_processor is not None,
            "rule_validator_ready": rule_validator is not None,
            "ai_analyzer_ready": ai_analyzer.model is not None,
            "score_enforcer_ready": score_enforcer is not None
        },
        "rate_limiter": rate_limiter.get_stats(),
        "performance": optimized_processor.get_performance_stats(),
        "enhanced_cache": enhanced_cache.get_stats()
    }

# Rate limiter status endpoint
@app.get("/rate-limit-status")
async def rate_limit_status():
    """Get detailed rate limiting statistics"""
    stats = rate_limiter.get_stats()
    
    return {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        **stats,
        "limits": {
            "rules": {name: {
                "requests": rule.requests,
                "window_seconds": rule.window,
                "burst": rule.burst,
                "description": str(rule)
            } for name, rule in rate_limiter.rules.items()},
            "global": {
                "max_concurrent": rate_limiter.global_limits['max_concurrent'],
                "max_new_clients_per_minute": rate_limiter.global_limits['max_clients_per_minute']
            }
        }
    }

# Performance monitoring endpoint
@app.get("/performance")
async def performance_stats():
    """Get detailed performance statistics and optimizations info"""
    perf_stats = optimized_processor.get_performance_stats()
    cache_stats = enhanced_cache.get_stats()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "optimization_status": "active",
        "performance": perf_stats,
        "caching": {
            "enhanced_cache": cache_stats,
            "cache_layers": ["memory", "disk"],
            "optimization_features": [
                "persistent_storage",
                "intelligent_eviction",
                "background_cleanup",
                "multi_level_caching"
            ]
        },
        "async_processing": {
            "pipeline_stages": ["preprocessing", "parallel_analysis", "post_processing"],
            "optimization_features": [
                "task_batching",
                "priority_queues", 
                "concurrent_execution",
                "resource_pooling"
            ]
        },
        "recommendations": {
            "cache_hit_rate_target": "above 70%",
            "avg_response_time_target": "under 5000ms",
            "concurrent_request_limit": perf_stats["thread_pools"]["cpu_pool_size"]
        }
    }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "VU Resume Analyzer API is running", "version": "1.2.0"}


@app.get("/health")
async def health_check():
    """Detailed health check with performance info"""
    from .async_processor import async_processor, resume_cache
    import psutil
    import time
    
    # Check component health
    components = {}
    overall_status = "healthy"
    
    try:
        components["pdf_processor"] = "active"
    except Exception as e:
        components["pdf_processor"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    try:
        components["rule_validator"] = "active"
    except Exception as e:
        components["rule_validator"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    try:
        if ai_analyzer.model:
            components["ai_analyzer"] = "active"
        else:
            components["ai_analyzer"] = "inactive - check API key"
            overall_status = "degraded"
    except Exception as e:
        components["ai_analyzer"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    try:
        components["score_enforcer"] = "active"
    except Exception as e:
        components["score_enforcer"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    try:
        components["async_processor"] = f"active ({async_processor.max_workers} workers)"
    except Exception as e:
        components["async_processor"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    try:
        components["cache"] = f"active ({len(resume_cache.cache)} cached)"
    except Exception as e:
        components["cache"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    try:
        rate_stats = rate_limiter.get_stats()
        components["rate_limiter"] = f"active ({rate_stats['unique_clients']} clients, {rate_stats['blocked_clients']} blocked)"
        if rate_stats['block_rate'] > 50:  # More than 50% requests blocked
            overall_status = "degraded"
    except Exception as e:
        components["rate_limiter"] = f"error: {str(e)}"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - (getattr(app.state, 'start_time', time.time())),
        "components": components,
        "performance_features": {
            "parallel_processing": True,
            "result_caching": True,
            "concurrent_link_validation": True,
            "optimized_ocr": True,
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        } if 'psutil' in globals() else {"system_info": "unavailable"}
    }



@app.post("/analyze_resume", response_model=ResumeAnalysisResponse)
async def analyze_resume_endpoint(
    file: UploadFile = File(...), 
    priorities: Optional[str] = Form(None)
):
    """
    Analyze a resume PDF with optional priority areas

    Args:
        file: PDF file to analyze
        priorities: Comma-separated list of priority areas (optional)

    Returns:
        Comprehensive resume analysis results
    """
    # Comprehensive file validation
    file_validation = validate_file_upload(file)
    logger.info(f"File validation passed: {file_validation['filename']}")
    
    # Validate priorities if provided
    validated_priorities = None
    if priorities:
        validated_priorities = PriorityValidator.validate_priorities(priorities)
        logger.info(f"Validated priorities: {validated_priorities}")

    tmp_pdf_path = None

    try:
        with LogContext(logger, f"analyze-{file.filename}"):
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_pdf_path = tmp_file.name
                content = await file.read()
                
                # Validate file content (magic numbers, structure)
                content_validation = validate_file_content(content)
                logger.info(f"Content validation passed: {content_validation}")
                
                tmp_file.write(content)

            logger.info(f"Processing resume: {file_validation['filename']}")

            # Step 1: Extract text from PDF
            extracted_text = pdf_processor.extract_text(tmp_pdf_path)
            if not extracted_text:
                raise HTTPException(
                    status_code=500, detail="Failed to extract text from PDF"
                )

            # Validate extracted text
            if not pdf_processor.validate_extracted_text(extracted_text):
                raise HTTPException(
                    status_code=400,
                    detail="Extracted text does not appear to be a valid resume",
                )

            # Preprocess text
            clean_text = pdf_processor.preprocess_text(extracted_text)

            # Use optimized processing pipeline
            logger.info("Starting optimized analysis pipeline...")
            
            # Determine priority level based on request context
            priority_level = 0 if len(validated_priorities or []) > 0 else 1
            
            # Use optimized processor with enhanced caching
            analysis_results = await optimized_processor.process_resume_optimized(
                clean_text,
                pdf_processor,
                rule_validator,
                ai_analyzer,
                score_enforcer,
                priorities=validated_priorities,
                priority_level=priority_level
            )
            
            # Handle errors in optimized processing
            if "error" in analysis_results:
                return ErrorResponse(
                    error=analysis_results["error"],
                    details={
                        "extracted_text_preview": clean_text[:500],
                        "processing_metadata": analysis_results.get("processing_metadata", {})
                    },
                ).dict()
            
            # Extract results from optimized processor
            enforced_analysis = analysis_results
            processing_metadata = analysis_results.get("processing_metadata", {})
            
            # Build optimized response
            logger.info(f"Analysis completed successfully in {processing_metadata.get('processing_time', 0):.3f}s")
            
            # Create priority analysis if requested
            priority_analysis = None
            if validated_priorities and "error" not in analysis_results:
                priority_analysis = ai_analyzer.create_priority_analysis(
                    enforced_analysis, validated_priorities, 
                    analysis_results.get("rule_based_findings", {})
                )
            
            # Create fact sheet from rule-based findings
            rule_findings = analysis_results.get("rule_based_findings", {})
            
            # Extract scores properly
            completeness_data = rule_findings.get("completeness_score", {})
            formatting_data = rule_findings.get("formatting_analysis", {})
            
            completeness_score = (
                completeness_data.get("score", 0) if isinstance(completeness_data, dict) 
                else completeness_data if isinstance(completeness_data, (int, float)) 
                else 0
            )
            
            formatting_score = (
                formatting_data.get("overall_formatting_score", 0) if isinstance(formatting_data, dict)
                else formatting_data if isinstance(formatting_data, (int, float))
                else 0
            )
            
            fact_sheet_obj = {
                "summary": _create_fact_sheet_summary(rule_findings),
                "completeness_score": int(completeness_score),
                "formatting_score": float(formatting_score),
                "prompt_was_customized": bool(validated_priorities)
            }
            
            response = ResumeAnalysisResponse(
                status="success",
                analysis=enforced_analysis,
                rule_based_findings=rule_findings,
                fact_sheet=fact_sheet_obj,
                priority_analysis=priority_analysis,
                extracted_text_preview=clean_text[:500],
            )

        logger.info(f"Analysis completed successfully for {file.filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Cleanup temporary file
        if tmp_pdf_path and os.path.exists(tmp_pdf_path):
            try:
                os.unlink(tmp_pdf_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file: {e}")


def _create_fact_sheet_summary(findings: dict) -> str:
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


@app.post("/bulk_analyze_resumes", response_model=BulkAnalysisResponse)
async def bulk_analyze_resumes_endpoint(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    priorities: Optional[str] = Form(None),
    job_name: Optional[str] = Form(None),
):
    """
    Start bulk analysis of multiple resume PDFs

    Args:
        files: List of PDF files to analyze
        priorities: Comma-separated list of priority areas (optional)
        job_name: Optional job name for tracking

    Returns:
        Bulk analysis job details with job ID for tracking
    """
    # Validate input parameters
    validated_job_name = None
    if job_name:
        validated_job_name = JobNameValidator.validate_job_name(job_name)
        logger.info(f"Validated job name: {validated_job_name}")
    
    # Handle custom priorities for bulk processing
    validated_priorities = None
    
    if priorities:
        # Use custom priorities
        validated_priorities = PriorityValidator.validate_priorities(priorities)
        logger.info(f"Validated custom priorities for bulk processing: {validated_priorities}")
    
    # Validate file count
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
        
    if len(files) > bulk_processor.max_files_per_job:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {bulk_processor.max_files_per_job} files allowed per batch",
        )

    # Validate each file
    pdf_files = []
    for i, file in enumerate(files):
        try:
            file_validation = validate_file_upload(file)
            pdf_files.append({
                'file': file,
                'validation': file_validation,
                'index': i
            })
            logger.debug(f"File {i+1}/{len(files)} validated: {file_validation['filename']}")
        except HTTPException as e:
            raise HTTPException(
                status_code=400, 
                detail=f"File {i+1} ({file.filename if file.filename else 'unnamed'}): {e.detail}"
            )

    if not pdf_files:
        raise HTTPException(status_code=400, detail="No valid PDF files provided")

    # Create bulk job with validated parameters
    job_id = bulk_processor.create_bulk_job(
        file_count=len(pdf_files), 
        priorities=validated_priorities, 
        job_name=validated_job_name
    )

    # Save uploaded files temporarily
    temp_file_paths = []
    try:
        for file_info in pdf_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                content = await file_info['file'].read()
                tmp_file.write(content)
                temp_file_paths.append(tmp_file.name)

        # Start background processing
        background_tasks.add_task(
            _process_bulk_job_background, job_id, temp_file_paths, priorities
        )

        logger.info(f"Started bulk analysis job {job_id} with {len(pdf_files)} files")

        return BulkAnalysisResponse(
            job_id=job_id,
            status="processing",
            message=f"Bulk analysis started for {len(pdf_files)} files",
            total_files=len(pdf_files),
            results_preview=[],
            download_links={},
        )

    except Exception as e:
        # Clean up temp files only if the background task failed to start
        for temp_path in temp_file_paths:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file {temp_path}: {cleanup_error}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start bulk analysis: {str(e)}"
        )
    # Note: temp files will be cleaned up by the background task after processing


@app.get("/bulk_job_status/{job_id}", response_model=BulkAnalysisJob)
async def get_bulk_job_status(job_id: str):
    """
    Get status and results of a bulk analysis job

    Args:
        job_id: ID of the bulk analysis job

    Returns:
        Current status and results of the job
    """
    job = bulk_processor.get_job_status(job_id)
    if not job:
        logger.warning(f"Bulk job {job_id} not found. It might have expired or the server restarted.")
        raise HTTPException(status_code=404, detail=f"Bulk job with ID '{job_id}' not found. It may have expired or the server was restarted.")

    return job


@app.post("/export_results/{job_id}")
async def export_bulk_results(
    job_id: str,
    format: str = Form(..., description="Export format: 'excel' or 'csv'"),
    include_detailed_analysis: bool = Form(
        False, description="Include detailed analysis"
    ),
):
    """
    Export bulk analysis results to Excel or CSV

    Args:
        job_id: ID of the bulk analysis job
        format: Export format ('excel' or 'csv')
        include_detailed_analysis: Whether to include detailed analysis

    Returns:
        File download response
    """
    job = bulk_processor.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status not in ["completed", "partial"]:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not ready for export. Status: {job.status}",
        )

    try:
        if format.lower() == "excel":
            file_path = bulk_processor.export_results_to_excel(
                job_id, include_detailed_analysis
            )
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            filename = f"resume_analysis_results_{job_id[:8]}.xlsx"
        elif format.lower() == "csv":
            file_path = bulk_processor.export_results_to_csv(job_id)
            media_type = "text/csv"
            filename = f"resume_analysis_results_{job_id[:8]}.csv"
        else:
            raise HTTPException(
                status_code=400, detail="Format must be 'excel' or 'csv'"
            )

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


async def _process_bulk_job_background(
    job_id: str, file_paths: List[str], priorities: Optional[str]
):
    """Background task to process bulk job"""
    try:
        await bulk_processor.process_bulk_resumes(job_id, file_paths, priorities)
    except Exception as e:
        logger.error(f"Background bulk processing failed for job {job_id}: {e}")
    finally:
        # Cleanup temporary files
        for temp_path in file_paths:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup {temp_path}: {cleanup_error}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

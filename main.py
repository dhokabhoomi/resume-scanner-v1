from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pdf_processing import extract_text_from_pdf, analyze_resume

app = FastAPI()

# CORS Configuration: Add your frontend's origin here
origins = [
    "http://localhost:5173",  
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,   
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze_resume")
async def analyze_resume_endpoint(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    tmp_pdf_path = None
    try:
        # Save uploaded file temporarily
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_pdf_path = tmp_file.name

        # Extract text using pdf_processing utility
        extracted_text = extract_text_from_pdf(tmp_pdf_path)
        if not extracted_text:
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")

        # Get AI analysis dict from Gemini
        analysis_result = analyze_resume(extracted_text)

        # Check if there's an error in the analysis
        if "error" in analysis_result:
            return {
                "status": "error",
                "analysis": analysis_result,
                "extracted_text_preview": extracted_text[:500],
            }

        return {
            "status": "success",
            "analysis": analysis_result.get("analysis", analysis_result),
            "extracted_text_preview": extracted_text[:500],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if tmp_pdf_path and os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)
            
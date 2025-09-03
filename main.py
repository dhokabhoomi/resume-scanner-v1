from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from dotenv import load_dotenv
from pdf_processing import extract_text_from_pdf, analyze_resume

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("WARNING: GOOGLE_API_KEY not found in environment variables!")
else:
    print(f"API Key loaded: {api_key[:10]}..." if len(api_key) > 10 else "API Key loaded but very short")

app = FastAPI(title="VU Resume Analyzer API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "VU Resume Analyzer API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "resume-analyzer-api"}

# CORS Configuration: Add your frontend's origin here
origins = [
    "http://localhost:5173",  
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://resume-scanner-v1.vercel.app",  # Your Vercel frontend
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
            
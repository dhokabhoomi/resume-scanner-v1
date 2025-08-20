import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"Direct text extraction failed: {e}")

    print("Fallback using OCR for scanned PDF...")
    try:
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
    except Exception as e:
        print(f"OCR extraction failed: {e}")

    return text.strip()


def analyze_resume(resume_text: str) -> str:
    if not resume_text:
        return '{"error": "Empty resume text"}'

    base_prompt = f"""
You are an intelligent resume evaluator. Analyze the resume text and return ONLY valid JSON with the following structure:

{{
  "basic_info": {{"full_name": "", "email": "", "phone": "", "linkedin": "", "github": "", "completeness": "", "quality_score": 0, "suggestions": ""}},
  "professional_summary": {{"content": "", "completeness": "", "quality_score": 0, "suggestions": ""}},
  "education": [{{"degree": "", "institution": "", "start_date": "", "end_date": "", "gpa": "", "completeness": "", "quality_score": 0, "suggestions": ""}}],
  "work_experience": [{{"company": "", "role": "", "start_date": "", "end_date": "", "responsibilities": "", "achievements": "", "completeness": "", "quality_score": 0, "suggestions": ""}}],
  "projects": [{{"name": "", "description": "", "technologies": "", "outcome": "", "completeness": "", "quality_score": 0, "suggestions": ""}}],
  "skills": {{"technical_skills": [], "soft_skills": [], "domain_skills": [], "completeness": "", "quality_score": 0, "suggestions": ""}},
  "certifications": [{{"name": "", "authority": "", "date": "", "completeness": "", "quality_score": 0, "suggestions": ""}}],
  "extracurriculars": [{{"activity": "", "role": "", "duration": "", "completeness": "", "quality_score": 0, "suggestions": ""}}],
  "overall_score": 0,
  "overall_suggestions": ""
}}

Return **strict JSON only**, no extra commentary.

Input Resume Text:
{resume_text}
"""

    response = model.generate_content(base_prompt)
    raw_text = response.text.strip()

    # Strip markdown triple backticks ``````
    if raw_text.startswith("```json"):
        lines = raw_text.splitlines()
        if lines[-1].strip() == "```":
            raw_text = "\n".join(lines[1:-1])

    return raw_text

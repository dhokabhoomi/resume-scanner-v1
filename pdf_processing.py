import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import re
import logging

load_dotenv()

# Configure Google AI with better error handling
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in environment variables!")
    print("Available env vars:", list(os.environ.keys())[:10])  # Show first 10 env vars for debug
else:
    print(f"Configuring Google AI with key: {api_key[:10]}...")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("Google AI model configured successfully")
except Exception as e:
    print(f"Failed to configure Google AI: {e}")
    model = None

logging.basicConfig(level=logging.INFO)

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
        logging.warning(f"Direct text extraction failed: {e}")

    logging.info("Fallback using OCR for scanned PDF...")
    try:
        for page_num, img in enumerate(convert_from_path(pdf_path)):
            page_text = pytesseract.image_to_string(img)
            if page_text.strip():
                text += page_text + "\n"
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")

    return text.strip()

def clean_json_response(raw_text: str) -> dict:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r'(\{(?:.|\n)*\})', raw_text)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception as e:
                logging.error(f"Nested JSON parsing failed: {e}")
        return {"error": "Failed to parse JSON", "raw_response": raw_text[:500]}

def enforce_scores(analysis: dict) -> dict:
    for section, data in analysis.items():
        if isinstance(data, dict) and "quality_score" in data:
            if not isinstance(data["quality_score"], int):
                data["quality_score"] = 0
            # Ensure 'suggestions' always has content or "No suggestions."
            # And try to enforce the score consistency if possible post-hoc
            if "suggestions" in data:
                if not data["suggestions"].strip() or data["suggestions"].strip() == "No suggestions.":
                    data["suggestions"] = "No suggestions."
                    # If no suggestions, score should ideally be 100, or very high if minor unstated nuance
                    if data["quality_score"] < 90: # Allowing a tiny buffer for edge cases not explicitly suggested
                        data["quality_score"] = 90 # Set to a high value if no suggestions but not 100 by model
                elif data["quality_score"] == 100 and data["suggestions"].strip() != "No suggestions.":
                    # If score is 100 but there are suggestions, this indicates a contradiction.
                    # This is tricky as we defer to the model, but we can log it.
                    logging.warning(f"Section '{section}' has score 100 but also suggestions: {data['suggestions']}")

    if "overall_score" not in analysis:
        analysis["overall_score"] = 0
    if "overall_suggestions" not in analysis or not analysis["overall_suggestions"].strip():
        analysis["overall_suggestions"] = "No overall suggestions."
    return analysis

def enforce_headshot_rule(analysis: dict) -> dict:
    if "formatting_issues" in analysis and isinstance(analysis["formatting_issues"], dict):
        has_headshot = analysis["formatting_issues"].get("has_headshot", False)
        if has_headshot:
            analysis["formatting_issues"]["headshot_suggestion"] = (
                "Remove the headshot; photos are not recommended in professional resumes."
            )
        else:
            analysis["formatting_issues"]["headshot_suggestion"] = "No suggestions regarding headshots."
    return analysis

def analyze_resume(resume_text: str, retry_on_fail: bool = True) -> dict:
    if not resume_text:
        return {"error": "Empty resume text"}
    
    if model is None:
        return {"error": "Google AI model not configured. Please check GOOGLE_API_KEY environment variable."}

    base_prompt = f"""
You are an expert resume evaluator capable of analyzing resumes across ALL industries and domains (tech, healthcare, finance, marketing, engineering, education, legal, etc.). You will receive resume text. Your task is to scan the resume text and provide comprehensive feedback. Return ONLY valid JSON in the exact structure below.

Rules:
- Extract only resume content into the content fields.
- Provide analysis separately in quality_score and suggestions.
- Always return valid JSON in the schema.
- Do not invent or infer missing details.
- If a section is missing, leave it empty and flag in suggestions.
- Do not add commentary, explanations, or markdown.
- Output MUST start with '{{' and end with '}}'.
- A professional headshot should NEVER be recommended or suggested. Resumes are not supposed to have headshots.
- For the 'suggestions' field in each section, if there are no specific improvements needed, explicitly state "No suggestions." Do not leave it empty.
- **CRITICAL SCORING RULE:** If a section's 'quality_score' is less than 100, there MUST be explicit 'suggestions' provided to explain why. Conversely, if a section's 'suggestions' explicitly state "No suggestions.", then its 'quality_score' MUST be 100, indicating optimal performance for that section.
- When evaluating 'education', differentiate between degrees (e.g., Bachelor's, Master's) and non-degree education (e.g., high school, junior college). Do not request a 'degree' for non-degree educational entries.
- Regarding email, only suggest a 'professional email ID' if the current one appears unprofessional or informal (e.g., gamer tags, overly casual names). Do not compel it otherwise.

Scoring:
The 'overall_score' is a holistic evaluation, not a direct arithmetic average of individual section scores. It considers the weighted importance of each section, the overall impact of the resume, and adherence to best practices. Key sections like work experience and projects will significantly influence the overall score.
90–100 = Exceptional
70–89  = Good
50–69  = Average
30–49   = Below average
0–29   = Poor

Schema:
{{
  "basic_info": {{
    "content": {{"name": "", "email": "", "phone": "", "location": ""}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "professional_summary": {{
    "content": {{"summary_text": ""}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "education": {{
    "content": {{"institutions": [], "degrees": [], "dates": []}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "work_experience": {{
    "content": {{"companies": [], "positions": [], "durations": [], "achievements": []}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "projects": {{
    "content": {{"project_names": [], "descriptions": []}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "skills": {{
    "content": {{"technical_skills": [], "soft_skills": [], "languages": []}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "certifications": {{
    "content": {{"certification_names": [], "issuing_organizations": [], "dates": []}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "extracurriculars": {{
    "content": {{"activities": [], "roles": [], "durations": []}},
    "quality_score": 0,
    "suggestions": "No suggestions."
  }},
  "links_found": {{
    "linkedin_present": false,
    "github_present": false,
    "portfolio_website_present": false,
    "other_links_present": false,
    "all_links_list": [],
    "link_suggestions": "Include relevant professional links like LinkedIn or a portfolio website if applicable to your industry. A GitHub link is beneficial for technical roles but not universally required. No other suggestions."
  }},
  "formatting_issues": {{
    "has_headshot": false,
    "headshot_suggestion": "Remove the headshot; photos are not recommended in professional resumes.",
    "other_formatting_issues": "No suggestions."
  }},
  "overall_score": 0,
  "overall_suggestions": "No overall suggestions."
}}

Input Resume Text:
{resume_text}
"""

    try:
        response = model.generate_content(base_prompt)
        raw_text = response.text.strip()
        cleaned = clean_json_response(raw_text)

        # Retry if failed
        if "error" in cleaned and retry_on_fail:
            logging.warning("Retrying with stricter JSON-only prompt...")
            retry_prompt = (
                "Return ONLY valid JSON, no text outside. "
                "Do not include markdown. Resume follows:\n" + resume_text
            )
            retry_response = model.generate_content(retry_prompt)
            cleaned = clean_json_response(retry_response.text.strip())

        return {
            "status": "success",
            "analysis": enforce_headshot_rule(enforce_scores(cleaned))
        }
    except Exception as e:
        logging.error(f"Error in AI analysis: {e}")
        return {"error": f"Analysis failed: {str(e)}"}
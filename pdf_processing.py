import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import re

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


def clean_json_response(raw_text: str) -> dict:
    """Clean and parse the JSON response from the AI model"""
    # Remove markdown code blocks if present
    if raw_text.startswith("```json"):
        raw_text = re.sub(r'^```json\s*|\s*```$', '', raw_text, flags=re.MULTILINE)
    elif raw_text.startswith("```"):
        raw_text = re.sub(r'^```\s*|\s*```$', '', raw_text, flags=re.MULTILINE)
    
    # Try to parse the JSON
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {raw_text}")
        
        # Try to extract JSON from malformed response
        try:
            # Look for JSON object pattern
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
            
        # Return error if parsing fails
        return {"error": "Failed to parse analysis results", "raw_response": raw_text[:500] + "..."}


def analyze_resume(resume_text: str) -> dict:
    if not resume_text:
        return {"error": "Empty resume text"}

    base_prompt = f"""
You are an expert resume evaluator capable of analyzing resumes across ALL industries and domains. Your task is to scan the resume text and provide comprehensive feedback. Return ONLY valid JSON in the exact structure below.
UNIVERSAL ANALYSIS APPROACH:
Evaluate content based on professional standards applicable to ANY field.
Score sections based on completeness, clarity, and impact, implicitly considering the candidate's likely career stage (e.g., recent graduate, experienced professional) as inferred from the resume content.
Provide suggestions that improve the resume for any domain, tailored to the inferred experience level.
Identify all links mentioned in the resume text and verify their presence accurately.
SCORING SCALE (0-100%):
90-100%: Exceptional quality, industry best practices.
70-89%: Good quality, minor improvements needed.
50-69%: Average quality, several improvements needed.
30-49%: Below average, major improvements required.
0-29%: Poor quality or missing critical elements.
Phone numbers should be a valid, professionally formatted number. (e.g., +91-XXXXX-XXXXX, (XXX) XXX-XXXX, or XXXXXXXXXX).
JSON OUTPUT STRUCTURE:
{{
  "basic_info": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "professional_summary": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "education": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "work_experience": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "projects": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "skills": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "certifications": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "extracurriculars": {{
    "quality_score": 0,
    "suggestions": ""
  }},
  "links_found": {{
    "linkedin_present": false,
    "github_present": false,
    "portfolio_website_present": false,
    "other_links_present": false,
    "all_links_list": [],
    "link_suggestions": ""
  }},
  "formatting_issues": {{
    "has_headshot": false,
    "headshot_suggestion": "",
    "other_formatting_issues": ""
  }},
  "overall_score": 0,
  "overall_suggestions": ""
}}
EVALUATION INSTRUCTIONS:
BASIC INFO ANALYSIS:
Check for complete contact information (name, email, phone, location if relevant).
Assess professionalism of email address.
Score based on completeness and presentation.
PROFESSIONAL SUMMARY ANALYSIS:
Evaluate clarity, conciseness, and impact.
Check if it effectively highlights the candidate's core strengths and career goals, proportional to their inferred experience level.
Score based on how well it immediately sells the candidate's value.
EDUCATION ANALYSIS:
Assess relevance and presentation of educational background.
Check for appropriate inclusion of GPA, honors, relevant coursework. For recent graduates, this section is more critical; for experienced professionals, it's less so.
Score based on how education supports the candidate's professional trajectory.
WORK EXPERIENCE ANALYSIS:
Look for quantified achievements and impact statements.
Evaluate use of strong action verbs and professional language.
Assess career progression, responsibilities, and achievements relative to the candidate's inferred experience level. (e.g., expectations for a senior role are different from a junior role).
Score based on how well experience demonstrates value and growth.
PROJECTS ANALYSIS:
Evaluate project descriptions for clarity and impact.
Check for clear demonstration of skills and problem-solving abilities.
Assess outcome and contribution clarity. This section is often more impactful for recent graduates or those with limited professional experience.
Score based on how projects showcase abilities.
SKILLS ANALYSIS:
Evaluate organization and relevance of skills.
Check for appropriate skill categorization (e.g., Technical, Soft, Languages).
Assess depth vs. breadth balance appropriate for the candidate's inferred experience level.
Score based on how well skills are presented and support the candidate's capabilities.
CERTIFICATIONS ANALYSIS:
Check relevance to the candidate's likely field.
Assess credibility and currency of certifications.
Score based on value addition to candidacy.
EXTRACURRICULARS ANALYSIS:
Look for demonstrations of leadership, teamwork, communication, and diverse interests.
Evaluate relevance to professional development or transferable skills.
Score based on demonstration of a well-rounded personality and soft skills.
LINK DETECTION AND VERIFICATION:
CAREFULLY scan the entire resume text for ANY URLs or web links.
Look for: linkedin.com, github.com, portfolio sites, personal websites, project demos.
Mark each type as present (true) or not present (false) in the links_found object.
List ALL unique and valid links found in "all_links_list".
For link_suggestions:
If important professional links (e.g., LinkedIn, GitHub for relevant roles, portfolio for creative roles) are missing, suggest adding them.
If links are present but formatted poorly (e.g., not clickable, full URL not visible), suggest improvements like ensuring they are clickable and clearly displayed.
Avoid specific statements like "LinkedIn: Present" within the link_suggestions field; this field is for actionable advice.
HEADSHOT DETECTION:
The has_headshot field should always default to false in your output, as headshots are not to be included.
If you find any mention or placeholder of a photo/headshot within the resume text, in headshot_suggestion, recommend removal for ATS compatibility. Otherwise, leave it empty.
OVERALL SCORING:
Calculate weighted average as percentage: Work Experience (35%), Skills (20%), Education (15%), Projects (15%), Professional Summary (10%), Basic Info (3%), Certifications (1%), Extracurriculars (1%).
OVERALL SUGGESTIONS:
Provide actionable, domain-neutral suggestions that will improve the resume regardless of industry.
Tailor suggestions to the inferred experience level of the candidate (e.g., for a recent grad, focus on projects and skills; for experienced, focus on leadership and impact).

Input Resume Text:
{resume_text}
"""

   
    try:
        response = model.generate_content(base_prompt)
        raw_text = response.text.strip()
        cleaned = clean_json_response(raw_text)
        return {"status": "success", "analysis": cleaned}
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

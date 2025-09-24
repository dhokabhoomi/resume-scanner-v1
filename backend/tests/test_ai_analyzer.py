import pytest
from unittest.mock import MagicMock, patch
from resume_analyzer.ai_analyzer import AIAnalyzer

@pytest.fixture
def ai_analyzer_instance():
    with patch('google.generativeai.GenerativeModel') as MockGenerativeModel:
        mock_model = MockGenerativeModel.return_value
        mock_model.generate_content.return_value.text = """```json
{
  "basic_info": {
    "content": {"name": "John Doe"},
    "quality_score": 80,
    "suggestions": ""
  },
  "overall_score": 85
}
```"""
        analyzer = AIAnalyzer()
        analyzer.model = mock_model  # Ensure the mock is used
        return analyzer

def test_analyze_resume_success(ai_analyzer_instance):
    resume_text = "This is a test resume."
    result = ai_analyzer_instance.analyze_resume(resume_text)

    assert "overall_score" in result
    assert result["overall_score"] == 85
    assert "basic_info" in result
    assert result["basic_info"]["content"]["name"] == "John Doe"

def test_analyze_resume_empty_text(ai_analyzer_instance):
    resume_text = ""
    result = ai_analyzer_instance.analyze_resume(resume_text)

    assert "error" in result
    assert result["error"] == "Empty resume text"

def test_analyze_resume_model_not_configured():
    analyzer = AIAnalyzer()
    analyzer.model = None  # Explicitly set model to None
    resume_text = "This is a test resume."
    result = analyzer.analyze_resume(resume_text)

    assert "error" in result
    assert result["error"] == "AI model not configured. Please check GOOGLE_API_KEY."

def test_clean_json_response_valid_json(ai_analyzer_instance):
    raw_text = """```json
{
  "key": "value"
}
```"""
    result = ai_analyzer_instance._clean_json_response(raw_text)
    assert result == {"key": "value"}

def test_clean_json_response_no_json(ai_analyzer_instance):
    raw_text = "This is not JSON."
    result = ai_analyzer_instance._clean_json_response(raw_text)
    assert "error" in result
    assert "Failed to parse JSON" in result["error"]

def test_clean_json_response_malformed_json(ai_analyzer_instance):
    raw_text = """```json
{
  "key": "value",
```"""
    result = ai_analyzer_instance._clean_json_response(raw_text)
    assert "error" in result
    assert "Failed to parse JSON" in result["error"]

# You can add more tests here for other methods and edge cases

import requests
import json
import re
import os
from difflib import SequenceMatcher
from requests.exceptions import JSONDecodeError
from typing import Dict, Any, Optional, List, Tuple
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_text_for_prompt(text):
    """Clean text by removing special characters and normalizing whitespace.
    Preserves characters common in tech resumes: +, #, /, -, ."""
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?+#/\-@()]', '', text)
    text = ''.join(char for char in text if ord(char) >= 32)
    cleaned = text.strip()
    return cleaned[:10000] if len(cleaned) > 10000 else cleaned

RESUME_EXTRACTION_PROMPT = """You are an expert at parsing resumes with deep knowledge of tech industries. Extract ALL information in the following exact JSON format. Be thorough and comprehensive - extract every skill, every job entry, and every detail mentioned.

{
    "candidate_name": "full name if mentioned",
    "email": "email address if mentioned",
    "phone_number": "phone number if mentioned",
    "job_title": "current/most recent title",
    "years_of_experience": 0,
    "certifications": ["cert1", "cert2"],
    "professional_summary": "brief summary of career highlights",
    "education": {
        "degree": "highest degree",
        "field": "field of study",
        "institution": "university/school name"
    },
    "all_skills": ["skill1", "skill2", "skill3"],
    "work_history": [
        {
            "company": "company name",
            "role": "job title at this company",
            "start_date": "MMM YYYY or YYYY",
            "end_date": "MMM YYYY or YYYY or Present",
            "duration_months": 0,
            "skills_used": ["skill1", "skill2"],
            "responsibilities": ["key responsibility 1", "key responsibility 2"]
        }
    ]
}

CRITICAL INSTRUCTIONS for work_history:
- Extract EVERY job position mentioned, in chronological order (most recent first).
- Extract contact details ("email" and "phone_number") if visible.
- For each position, extract the company name, role/title, dates, and skills used in that role.
- Calculate duration_months as the approximate number of months worked there.
- List specific technical skills and tools used in each role.
- If exact dates are not given, estimate from context (e.g., "3 years at Google" -> duration_months: 36).
- If only years are given, set duration_months to year_count * 12.
- The "all_skills" field should be a comprehensive deduplicated list of ALL skills mentioned anywhere in the resume, including skills from work_history, certifications, education, and summary sections.

Resume Text:
<<<{text}>>>

Return ONLY the valid JSON object, no other text."""

def extract_contact_info(text: str) -> Dict[str, str]:
    """Robust regex extractor for email and phone numbers from resume text."""
    if not text:
        return {"email": "", "phone_number": ""}

    email = ""
    phone_number = ""

    # 1. Email extraction
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    if emails:
        email = emails[0].strip()
    else:
        spaced_email = re.search(r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}', text)
        if spaced_email:
            email = re.sub(r'\s+', '', spaced_email.group(0))

    # 2. Phone number extraction
    phone_patterns = [
        r'\+?\d{1,3}[\s\-]?\(?\d{2,5}\)?[\s\-]?\d{3,5}[\s\-]?\d{3,5}',
        r'\b\d{10}\b',
        r'\b\d{5}[\s\-]\d{5}\b',
        r'\b0\d{10}\b'
    ]

    # Try labeled phone first (e.g. Phone: +91 96700 53443, Mobile: 9876543210)
    label_match = re.search(r'(?:phone|mobile|mob|tel|contact|cell)[\s:\-]*([\+\d\s\-\(\)]{8,20})', text, re.IGNORECASE)
    if label_match:
        candidate = label_match.group(1).strip()
        digits = re.sub(r'[^\d+]', '', candidate)
        if len(re.sub(r'[^\d]', '', digits)) >= 10:
            phone_number = candidate

    if not phone_number:
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                m_str = match.group(0).strip()
                digits = re.sub(r'[^\d]', '', m_str)
                # Ensure 10-13 digits and not a year like 2024, 2025, or zip code
                if 10 <= len(digits) <= 13 and not digits.startswith(('202', '201', '199', '198')):
                    phone_number = m_str
                    break
            if phone_number:
                break

    return {
        "email": email,
        "phone_number": phone_number
    }

def extract_structured_data(text: str, extraction_type: str) -> Dict[str, Any]:
    """Extract structured data with improved error handling and schema normalization."""
    cleaned_text = clean_text_for_prompt(text)

    try:
        prompt = RESUME_EXTRACTION_PROMPT if extraction_type == "resume" else JD_EXTRACTION_PROMPT
        response = call_llm(prompt.replace("{text}", cleaned_text))

        parsed_data = extract_json_from_text(response)
        if not parsed_data:
            parsed_data = _fallback_structure(extraction_type)
        else:
            parsed_data = _normalize_extracted(parsed_data, extraction_type)

        # Force contact extraction regex fallback if email or phone_number is missing/empty
        if extraction_type == "resume":
            contacts = extract_contact_info(text)
            if not parsed_data.get("email") or str(parsed_data.get("email")).strip() in ["", "N/A", "null", "None"]:
                parsed_data["email"] = contacts["email"]
            if not parsed_data.get("phone_number") or str(parsed_data.get("phone_number")).strip() in ["", "N/A", "null", "None"]:
                parsed_data["phone_number"] = contacts["phone_number"]

        return parsed_data
    except Exception as e:
        print(f"Error in extraction: {str(e)}")
        fallback = {"error": str(e)}
        if extraction_type == "resume":
            contacts = extract_contact_info(text)
            fallback.update(contacts)
        return fallback


def _fallback_structure(extraction_type: str) -> Dict[str, Any]:
    """Return a safe fallback dict when LLM extraction completely fails."""
    if extraction_type == "resume":
        return {
            "candidate_name": "",
            "email": "",
            "phone_number": "",
            "candidate_skills": [],
            "all_skills": [],
            "job_title": "",
            "years_of_experience": 0,
            "certifications": [],
            "professional_summary": "",
            "education": {"degree": "", "field": ""},
            "work_history": []
        }
    return {
        "required_skills": [],
        "must_have_skills": [],
        "nice_to_have_skills": [],
        "job_title": "",
        "required_experience": 0,
        "certifications": [],
        "key_responsibilities": [],
        "education": {"degree": "", "field": ""}
    }


def _normalize_extracted(data: Dict[str, Any], extraction_type: str) -> Dict[str, Any]:
    """Ensure all expected keys exist and have correct types."""
    if extraction_type == "resume":
        data.setdefault("candidate_name", "")
        data.setdefault("email", "")
        data.setdefault("phone_number", "")
        data.setdefault("candidate_skills", data.get("all_skills", []))
        data.setdefault("all_skills", data.get("candidate_skills", []))
        data.setdefault("job_title", "")
        data.setdefault("years_of_experience", 0)
        data.setdefault("certifications", [])
        data.setdefault("professional_summary", "")
        data.setdefault("education", {"degree": "", "field": ""})
        data.setdefault("work_history", [])

        if not data["all_skills"] and data["candidate_skills"]:
            data["all_skills"] = data["candidate_skills"]
        if not data["candidate_skills"] and data["all_skills"]:
            data["candidate_skills"] = data["all_skills"]

        for job in data["work_history"]:
            job.setdefault("company", "Unknown")
            job.setdefault("role", "")
            job.setdefault("start_date", "")
            job.setdefault("end_date", "")
            job.setdefault("duration_months", 0)
            job.setdefault("skills_used", [])
            job.setdefault("responsibilities", [])
    else:
        data.setdefault("required_skills", [])
        data.setdefault("must_have_skills", [])
        data.setdefault("nice_to_have_skills", [])
        data.setdefault("job_title", "")
        data.setdefault("required_experience", 0)
        data.setdefault("certifications", [])
        data.setdefault("key_responsibilities", [])
        data.setdefault("education", {"degree": "", "field": ""})

        if not data["must_have_skills"] and not data["nice_to_have_skills"]:
            data["must_have_skills"] = data["required_skills"]
            data["nice_to_have_skills"] = []
        if not data["required_skills"]:
            data["required_skills"] = data["must_have_skills"]

    return data

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Enhanced JSON extraction with robust pattern matching, handling think tags, markdown, and invalid characters."""
    if not text or not isinstance(text, str):
        return None

    # Remove reasoning/think tags if present (e.g. DeepSeek/Qwen models)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # Remove markdown code block wrappers
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    # 1. Direct JSON parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Find outermost JSON braces { ... }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = text[start:end + 1]
        try:
            return json.loads(json_str)
        except Exception:
            # Clean trailing commas (e.g., [1, 2,] or {"a": "b",})
            cleaned = re.sub(r',\s*([\}\]])', r'\1', json_str)
            try:
                return json.loads(cleaned)
            except Exception:
                pass

    return None

JD_EXTRACTION_PROMPT = """You are an expert at parsing job descriptions. Extract ALL information in the following exact JSON format. Be thorough.

{
    "job_title": "exact position title",
    "required_experience": 0,
    "required_skills": ["skill1", "skill2"],
    "must_have_skills": ["skill1", "skill2"],
    "nice_to_have_skills": ["skill1", "skill2"],
    "certifications": ["cert1", "cert2"],
    "key_responsibilities": ["resp1", "resp2"],
    "education": {
        "degree": "required degree level",
        "field": "required field of study"
    }
}

CRITICAL INSTRUCTIONS:
- "must_have_skills": Skills that are absolutely required (explicitly stated as required/mandatory/essential).
- "nice_to_have_skills": Skills that are preferred but not mandatory (stated as nice to have/preferred/bonus).
- "required_skills": ALL skills mentioned (union of must_have and nice_to_have).
- Extract every technical skill, tool, framework, language, methodology, and domain expertise mentioned.
- Be comprehensive - do not miss any skill even if mentioned once.

Job Description Text:
<<<{text}>>>

Return ONLY the valid JSON object, no other text."""

EVALUATION_PROMPT = """You are a domain expert in candidate-job matching. Evaluate the match between the resume and job description. Return your analysis in the following exact JSON format (0-100 scores):

{
    "skill_match": {
        "score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "justification": "explanation"
    },
    "title_match": {
        "score": 0,
        "justification": "explanation"
    },
    "experience_match": {
        "score": 0,
        "justification": "explanation"
    },
    "overall_match": {
        "score": 0,
        "summary": "explanation",
        "strengths": [],
        "gaps": []
    }
}

Scoring Rules:
- 0-20: Very Poor match
- 21-40: Poor match
- 41-60: Moderate match
- 61-80: Good match
- 81-100: Excellent match

Resume Text:
<<<{resume_text}>>>

Job Description Text:
<<<{jd_text}>>>

Return ONLY the valid JSON object, no other text."""


def evaluate_match(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Call LLM to get 0-100 evaluation scores for skill, title, experience, and overall match."""
    cleaned_resume = clean_text_for_prompt(resume_text)
    cleaned_jd = clean_text_for_prompt(jd_text)

    prompt = EVALUATION_PROMPT.replace("{resume_text}", cleaned_resume).replace("{jd_text}", cleaned_jd)

    try:
        response = call_llm(prompt)
        parsed = extract_json_from_text(response)
        if parsed:
            return _normalize_evaluation(parsed)
        return _fallback_evaluation()
    except Exception as e:
        print(f"Error in LLM evaluation: {str(e)}")
        return _fallback_evaluation()


def _normalize_evaluation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all evaluation keys exist with correct types and 0-100 range."""
    skill = data.get("skill_match", {})
    title = data.get("title_match", {})
    exp = data.get("experience_match", {})
    overall = data.get("overall_match", {})

    return {
        "skill_match": {
            "score": max(0, min(100, int(skill.get("score", 0)))),
            "matched_skills": skill.get("matched_skills", []),
            "missing_skills": skill.get("missing_skills", []),
            "justification": skill.get("justification", ""),
        },
        "title_match": {
            "score": max(0, min(100, int(title.get("score", 0)))),
            "justification": title.get("justification", ""),
        },
        "experience_match": {
            "score": max(0, min(100, int(exp.get("score", 0)))),
            "justification": exp.get("justification", ""),
        },
        "overall_match": {
            "score": max(0, min(100, int(overall.get("score", 0)))),
            "summary": overall.get("summary", ""),
            "strengths": overall.get("strengths", []),
            "gaps": overall.get("gaps", []),
        },
    }


def _fallback_evaluation() -> Dict[str, Any]:
    """Return safe fallback when LLM evaluation fails."""
    return {
        "skill_match": {"score": 0, "matched_skills": [], "missing_skills": [], "justification": "Evaluation unavailable"},
        "title_match": {"score": 0, "justification": "Evaluation unavailable"},
        "experience_match": {"score": 0, "justification": "Evaluation unavailable"},
        "overall_match": {"score": 0, "summary": "Evaluation unavailable", "strengths": [], "gaps": []},
    }


def generate_summary(prompt: str) -> str:
    """Generate summary with explicit formatting instructions."""
    formatted_prompt = f"""{prompt}

    IMPORTANT: Respond in the following format:
    1. Brief overall assessment (2-3 sentences)
    2. Skills analysis
    3. Title match analysis
    4. Experience match analysis
    5. Final recommendation

    Keep responses factual and concise."""
    
    try:
        response = call_llm(formatted_prompt)
        return response.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def parse_llm_response(response: str) -> Dict[str, Any]:
    """Robustly parse LLM response to ensure valid JSON."""
    try:
        # Try to find JSON in the response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if (start_idx != -1 and end_idx != 0):
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        return {"error": "No JSON found in response"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in response"}

def call_llm(prompt: str) -> str:
    """Make LLM API call using OpenAI Chat Completions API with error handling."""
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise Exception("OPENAI_API_KEY is not set in the environment or .env file.")

    try:
        client = openai.OpenAI(api_key=openai_api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

def generate_summary_lmstudio(prompt):
    # Retained for compatibility/reference
    endpoint = "http://127.0.0.1:1234/v1/completions"
    payload = {
        "model": "deepseek-r1-distill-qwen-7b",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(endpoint, json=payload)
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                text = data["choices"][0].get("text", "")
                extracted_json = extract_json_from_text(text)
                if extracted_json:
                    return json.dumps(extracted_json)
            return json.dumps({"error": "No valid JSON found in response"})
        except JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON response: {response.text}"})
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "LMStudio server is unavailable."})

def generate_summary_ollama(prompt):
    # Retained for compatibility/reference
    endpoint = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "llama3.2:3b-instruct-fp16",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(endpoint, json=payload)
        if response.status_code != 200:
            return json.dumps({"error": f"Non-200 response: {response.status_code}"})
        data = response.json()
        completion = data.get("completion", "")
        return completion
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "Ollama server is unavailable."})

def skill_matches(candidate_skill: str, required_skill: str) -> bool:
    """Fuzzy match a candidate skill against a required skill.
    Handles case-insensitivity, partial matches, abbreviations, and common synonyms."""
    c = candidate_skill.lower().strip()
    r = required_skill.lower().strip()

    if c == r:
        return True
    if c in r or r in c:
        return True

    if SequenceMatcher(None, c, r).ratio() >= 0.8:
        return True

    _SYNONYMS = {
        "js": "javascript", "ts": "typescript", "py": "python",
        "ml": "machine learning", "ai": "artificial intelligence",
        "dl": "deep learning", "cv": "computer vision",
        "nlp": "natural language processing", "rn": "react native",
        "k8s": "kubernetes", "tf": "tensorflow", "pt": "pytorch",
        "aws": "amazon web services", "gcp": "google cloud platform",
        "azure": "microsoft azure", "rbac": "role-based access control",
        "ci/cd": "continuous integration continuous deployment",
        "devops": "development operations", "sre": "site reliability engineering",
        "oop": "object oriented programming", "rest": "restful api",
        "graphql": "graph ql", "sql": "structured query language",
        "nosql": "not only sql", "html5": "html", "css3": "css",
        "node.js": "nodejs", "react.js": "react", "angular.js": "angular",
        "vue.js": "vue", "next.js": "nextjs", "express.js": "express",
    }

    c_expanded = _SYNONYMS.get(c, c)
    r_expanded = _SYNONYMS.get(r, r)
    if c_expanded == r_expanded:
        return True
    if c_expanded in r_expanded or r_expanded in c_expanded:
        return True

    c_words = set(c.replace("/", " ").replace("-", " ").replace(".", " ").split())
    r_words = set(r.replace("/", " ").replace("-", " ").replace(".", " ").split())
    if c_words & r_words and len(r_words) <= 3:
        return True

    return False


def compare_skill_lists(
    resume_skills: List[str],
    jd_skills: List[str],
    must_have: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compare resume skills against JD skills with fuzzy matching.
    Returns matched, missing, and extra skills with a score."""
    matched = []
    missing = []

    for req_skill in jd_skills:
        found = any(skill_matches(rs, req_skill) for rs in resume_skills)
        if found:
            matched.append(req_skill)
        else:
            missing.append(req_skill)

    must_matched = []
    must_missing = []
    if must_have:
        for req_skill in must_have:
            found = any(skill_matches(rs, req_skill) for rs in resume_skills)
            if found:
                must_matched.append(req_skill)
            else:
                must_missing.append(req_skill)

    total = len(jd_skills) or 1
    score = len(matched) / total

    must_score = 1.0
    if must_have:
        must_total = len(must_have) or 1
        must_score = len(must_matched) / must_total

    final_score = 0.7 * score + 0.3 * must_score if must_have else score

    return {
        "score": final_score,
        "matched": matched,
        "missing": missing,
        "must_matched": must_matched,
        "must_missing": must_missing,
        "total_required": len(jd_skills),
        "total_matched": len(matched),
    }
from llm_integration import extract_structured_data, generate_summary, compare_skill_lists, skill_matches, evaluate_match
from typing import Dict, Any, Optional, Tuple, List

def format_experience_text(years_val: float, months_val: Optional[int] = None) -> str:
    """Format exact experience into readable text like '1 Year 6 Months', '8 Months', '2 Years'."""
    if months_val is not None and months_val > 0:
        y = months_val // 12
        m = months_val % 12
    else:
        y = int(years_val)
        m = round((years_val - y) * 12)
        if m >= 12:
            y += 1
            m = 0

    if y == 0 and m == 0:
        return "0 Months"
    if y > 0 and m > 0:
        return f"{y} Year{'s' if y > 1 else ''} {m} Month{'s' if m > 1 else ''}"
    if y > 0:
        return f"{y} Year{'s' if y > 1 else ''}"
    return f"{m} Month{'s' if m > 1 else ''}"


def compute_scores(resume_text: str, jd_text: str) -> Dict[str, Any]:
    resume_data = extract_structured_data(resume_text, extraction_type="resume")
    jd_data = extract_structured_data(jd_text, extraction_type="jd")

    if "error" in resume_data or "error" in jd_data:
        err_msg = resume_data.get("error") or jd_data.get("error")
        return {
            "skill": 0,
            "skill_explanation": f"Error in data extraction: {err_msg}",
            "title": 0,
            "title_explanation": f"Error in data extraction: {err_msg}",
            "experience": 0,
            "experience_explanation": f"Error in data extraction: {err_msg}",
            "overall": 0,
            "overall_explanation": f"Failed to extract necessary information: {err_msg}",
            "required_experience": "0 Years",
            "candidate_experience": "0 Months",
            "resume_data": resume_data,
            "jd_data": jd_data,
            "hire_recommendation": "No",
            "hire_reason": f"Error extracting data: {err_msg}"
        }

    resume_skills = resume_data.get("all_skills") or resume_data.get("candidate_skills", [])
    jd_skills = jd_data.get("required_skills", [])
    must_have = jd_data.get("must_have_skills", [])

    skill_result = compare_skill_lists(resume_skills, jd_skills, must_have)
    skill_score = skill_result["score"]

    title_score = _compare_titles(resume_data.get("job_title", ""), jd_data.get("job_title", ""))
    exp_score, exp_detail, req_exp_years, cand_exp_years, req_exp_text, cand_exp_text = _compare_experience_detailed(resume_data, jd_data)

    overall = 0.5 * skill_score + 0.3 * title_score + 0.2 * exp_score

    matched_str = ", ".join(skill_result["matched"]) if skill_result["matched"] else "None"
    missing_str = ", ".join(skill_result["missing"]) if skill_result["missing"] else "None"
    skill_explanation = (
        f"Matched {skill_result['total_matched']}/{skill_result['total_required']} required skills.\n"
        f"Matched: {matched_str}\n"
        f"Missing: {missing_str}"
    )

    title_explanation = (
        f"Candidate title: '{resume_data.get('job_title', 'N/A')}' | "
        f"Required: '{jd_data.get('job_title', 'N/A')}'. "
        f"{'Exact match.' if title_score == 1.0 else 'Partial/relevance match.' if title_score >= 0.7 else 'Low title alignment.'}"
    )

    scores = {
        "skill": round(skill_score, 2),
        "skill_explanation": skill_explanation,
        "skill_matched": skill_result["matched"],
        "skill_missing": skill_result["missing"],
        "must_matched": skill_result.get("must_matched", []),
        "must_missing": skill_result.get("must_missing", []),
        "title": round(title_score, 2),
        "title_explanation": title_explanation,
        "experience": round(exp_score, 2),
        "experience_explanation": exp_detail,
        "required_experience": req_exp_text,
        "candidate_experience": cand_exp_text,
        "required_exp_years": req_exp_years,
        "candidate_exp_years": cand_exp_years,
        "overall": round(overall, 2),
        "overall_explanation": (
            f"Weighted: Skills ({skill_score * 0.5:.2f}) + "
            f"Title ({title_score * 0.3:.2f}) + "
            f"Experience ({exp_score * 0.2:.2f}) = {overall:.2f}"
        ),
        "resume_data": resume_data,
        "jd_data": jd_data,
        "work_history": resume_data.get("work_history", []),
    }

    llm_eval = evaluate_match(resume_text, jd_text)
    scores["llm_evaluation"] = llm_eval

    hire, hire_reason = get_hire_recommendation(scores)
    scores["hire_recommendation"] = hire
    scores["hire_reason"] = hire_reason

    return scores


def get_hire_recommendation(scores: Dict[str, Any]) -> Tuple[str, str]:
    """Determine binary Yes/No hire recommendation based on experience and skills.
    MUST ONLY RETURN 'Yes' OR 'No'."""
    cand_exp_years = scores.get("candidate_exp_years", 0)
    req_exp_years = scores.get("required_exp_years", 0)
    cand_exp_text = scores.get("candidate_experience", "0 Months")
    req_exp_text = scores.get("required_experience", "0 Years")

    # RULE 1: Experience Check (Hard Prerequisite)
    # If candidate experience is less than required experience -> STRICT "No"!
    if req_exp_years > 0 and cand_exp_years < req_exp_years:
        reason = (
            f"No — Experience criteria not met. Candidate has {cand_exp_text}, "
            f"but JD requires at least {req_exp_text}."
        )
        return "No", reason

    # RULE 2: Skills Match Check
    llm_eval = scores.get("llm_evaluation", {})
    overall_llm = llm_eval.get("overall_match", {}).get("score", 0)
    must_missing = scores.get("must_missing", [])
    matched_count = len(scores.get("skill_matched", []))
    total_required = len(scores.get("skill_missing", [])) + matched_count

    if must_missing:
        reason = (
            f"No — Missing required essential skills: {', '.join(must_missing)}."
        )
        return "No", reason

    skill_ratio = matched_count / total_required if total_required else 0

    if overall_llm >= 55 and skill_ratio >= 0.4:
        reason = (
            f"Yes — Candidate meets experience requirement ({cand_exp_text}) "
            f"and matches {matched_count}/{total_required} preferred skills."
        )
        return "Yes", reason

    reason = (
        f"No — Insufficient skill match ({matched_count}/{total_required} preferred skills matched, "
        f"LLM score {overall_llm}/100)."
    )
    return "No", reason


def summarize_candidate(resume_text: str, jd_text: str, scores: Dict[str, Any]) -> str:
    work_history = scores.get("work_history", [])
    work_history_str = ""
    if work_history:
        work_history_str = "\nWork History (chronological):\n"
        for i, job in enumerate(work_history, 1):
            skills = ", ".join(job.get("skills_used", []))
            work_history_str += (
                f"  {i}. {job.get('company', 'Unknown')} — {job.get('role', 'N/A')} "
                f"({job.get('start_date', '?')} to {job.get('end_date', '?')}, "
                f"~{job.get('duration_months', 0)} months) "
                f"Skills: {skills}\n"
            )

    prompt = f"""You are an expert evaluator in candidate-job matching. Provide a detailed justification for each score.

Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Required Experience: {scores.get('required_experience')}
Candidate Experience: {scores.get('candidate_experience')}

Skills Matched: {', '.join(scores.get('skill_matched', []))}
Skills Missing: {', '.join(scores.get('skill_missing', []))}
{work_history_str}

Please justify the final decision:
1. Explain why the candidate's skills led to the decision. Reference specific matched and missing skills.
2. Explain how the candidate's experience level ({scores.get('candidate_experience')}) aligns with the required experience ({scores.get('required_experience')}).
3. Final Verdict: {scores.get('hire_recommendation')} ({scores.get('hire_reason')})

Provide your answer in detailed plain text."""
    return generate_summary(prompt)


def _compare_titles(resume_title: str, jd_title: str) -> float:
    if not resume_title or not jd_title:
        return 0.3

    r = resume_title.lower().strip()
    j = jd_title.lower().strip()

    if r == j:
        return 1.0

    r_words = set(r.split())
    j_words = set(j.split())
    overlap = r_words & j_words

    if overlap and len(overlap) / max(len(j_words), 1) >= 0.5:
        return 0.8

    if overlap:
        return 0.6

    return 0.3


def _compare_experience_detailed(resume_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Tuple[float, str, float, float, str, str]:
    work_history = resume_data.get("work_history", [])
    jd_required = 0.0
    try:
        jd_required = float(jd_data.get("required_experience", 0))
    except (ValueError, TypeError):
        pass

    req_exp_text = f"{int(jd_required)} Year{'s' if jd_required != 1 else ''}" if jd_required > 0 else "0 Years"

    total_months_from_history = sum(job.get("duration_months", 0) for job in work_history)
    try:
        total_from_field = float(resume_data.get("years_of_experience", 0)) * 12
    except (ValueError, TypeError):
        total_from_field = 0

    actual_months = int(max(total_months_from_history, total_from_field))
    actual_years = actual_months / 12.0

    cand_exp_text = format_experience_text(actual_years, actual_months)

    if jd_required == 0:
        score = 1.0
    else:
        score = min(actual_years / jd_required, 1.0)

    detail_parts = [
        f"Candidate total experience: {cand_exp_text} "
        f"(from {len(work_history)} role(s) in work history)",
        f"Required experience: {req_exp_text}",
    ]

    if work_history:
        detail_parts.append("\nWork History (most recent first):")
        for i, job in enumerate(work_history, 1):
            months = job.get("duration_months", 0)
            dur_text = format_experience_text(months / 12.0, months)
            skills_str = ", ".join(job.get("skills_used", []))
            detail_parts.append(
                f"  {i}. {job.get('company', 'Unknown')} — {job.get('role', 'N/A')} "
                f"({dur_text}) Skills: {skills_str}"
            )

    return score, "\n".join(detail_parts), jd_required, actual_years, req_exp_text, cand_exp_text

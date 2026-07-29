from llm_integration import extract_structured_data, generate_summary, compare_skill_lists, skill_matches, evaluate_match


def compute_scores(resume_text, jd_text):
    resume_data = extract_structured_data(resume_text, extraction_type="resume")
    jd_data = extract_structured_data(jd_text, extraction_type="jd")

    if "error" in resume_data or "error" in jd_data:
        return {
            "skill": 0,
            "skill_explanation": "Error in data extraction",
            "title": 0,
            "title_explanation": "Error in data extraction",
            "experience": 0,
            "experience_explanation": "Error in data extraction",
            "overall": 0,
            "overall_explanation": "Failed to extract necessary information",
            "resume_data": resume_data,
            "jd_data": jd_data,
        }

    resume_skills = resume_data.get("all_skills") or resume_data.get("candidate_skills", [])
    jd_skills = jd_data.get("required_skills", [])
    must_have = jd_data.get("must_have_skills", [])

    skill_result = compare_skill_lists(resume_skills, jd_skills, must_have)
    skill_score = skill_result["score"]

    title_score = _compare_titles(resume_data.get("job_title", ""), jd_data.get("job_title", ""))
    exp_score, exp_detail = _compare_experience_detailed(resume_data, jd_data)

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


def get_hire_recommendation(scores):
    """Determine Yes/Maybe/No hire recommendation based on combined scores.
    Returns (recommendation: str, reason: str)."""
    llm_eval = scores.get("llm_evaluation", {})
    overall_llm = llm_eval.get("overall_match", {}).get("score", 0)
    skill_llm = llm_eval.get("skill_match", {}).get("score", 0)
    exp_llm = llm_eval.get("experience_match", {}).get("score", 0)
    must_missing = scores.get("must_missing", [])
    matched_count = len(scores.get("skill_matched", []))
    total_required = len(scores.get("skill_missing", [])) + matched_count

    skill_ratio = matched_count / total_required if total_required else 0

    if overall_llm >= 60 and skill_ratio >= 0.5 and not must_missing:
        reason = (
            f"Strong match — {matched_count}/{total_required} skills matched, "
            f"LLM score {overall_llm}/100, no must-have skills missing."
        )
        return "Yes", reason

    if overall_llm >= 35 and skill_ratio >= 0.3:
        reason = (
            f"Partial match — {matched_count}/{total_required} skills matched, "
            f"LLM score {overall_llm}/100"
        )
        if must_missing:
            reason += f", but missing must-have: {', '.join(must_missing)}"
        return "Maybe", reason

    reason = (
        f"Weak match — {matched_count}/{total_required} skills matched, "
        f"LLM score {overall_llm}/100"
    )
    if must_missing:
        reason += f", missing must-have: {', '.join(must_missing)}"
    return "No", reason


def summarize_candidate(resume_text, jd_text, scores):
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

Computed Scores:
- Skill Match Score: {scores.get('skill')}
- Job Title Relevance Score: {scores.get('title')}
- Experience Match Score: {scores.get('experience')}
- Overall Match Score: {scores.get('overall')}

Skills Matched: {', '.join(scores.get('skill_matched', []))}
Skills Missing: {', '.join(scores.get('skill_missing', []))}
{work_history_str}

Please justify each score:
1. Explain why the candidate's skills (or lack thereof) led to the Skill Match Score. Reference specific matched and missing skills.
2. Explain how the candidate's job title aligns or does not align with the required job title.
3. Explain the candidate's experience level. Reference their work history and progression.
4. Summarize how the strengths and weaknesses combine to produce the overall score.

Provide your answer in detailed plain text."""
    return generate_summary(prompt)


def _compare_titles(resume_title, jd_title):
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


def _compare_experience_detailed(resume_data, jd_data):
    work_history = resume_data.get("work_history", [])
    jd_required = 0
    try:
        jd_required = float(jd_data.get("required_experience", 0))
    except (ValueError, TypeError):
        pass

    total_months_from_history = sum(job.get("duration_months", 0) for job in work_history)
    try:
        total_from_field = float(resume_data.get("years_of_experience", 0)) * 12
    except (ValueError, TypeError):
        total_from_field = 0

    actual_months = max(total_months_from_history, total_from_field)
    actual_years = actual_months / 12

    if jd_required == 0:
        score = 1.0
    else:
        score = min(actual_years / jd_required, 1.2)
        if score > 1.0:
            score = 1.0

    relevant_months = 0
    if work_history:
        all_jd_skills = set(jd_data.get("required_skills", []))
        for job in work_history:
            job_skills = set(s.lower() for s in job.get("skills_used", []))
            jd_skills_lower = set(s.lower() for s in all_jd_skills)
            if job_skills & jd_skills_lower:
                relevant_months += job.get("duration_months", 0)

    relevant_years = relevant_months / 12

    detail_parts = [
        f"Candidate total experience: ~{actual_years:.1f} years "
        f"(from {len(work_history)} role(s) in work history)",
        f"Required: {jd_required:.0f} years",
    ]

    if work_history:
        detail_parts.append("\nWork History (most recent first):")
        for i, job in enumerate(work_history, 1):
            months = job.get("duration_months", 0)
            yrs = months / 12
            skills_str = ", ".join(job.get("skills_used", []))
            detail_parts.append(
                f"  {i}. {job.get('company', 'Unknown')} — {job.get('role', 'N/A')} "
                f"(~{yrs:.1f} years) Skills: {skills_str}"
            )

    if relevant_months > 0:
        detail_parts.append(
            f"\nRelevant domain experience: ~{relevant_years:.1f} years "
            f"(roles using skills required by this JD)"
        )

    return score, "\n".join(detail_parts)

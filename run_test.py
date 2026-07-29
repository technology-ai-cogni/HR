import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from extraction import extract_text_from_file
from matching_engine import compute_scores, summarize_candidate

JD_TEXT = """Job Description – Social Media Executive

Company: Cognitute
Position: Social Media Executive
Location: Noida Sector 90 (Work from Office)
Experience: 1–1.5 Years
Salary: Up to ₹25,000 per month

About the Role

Cognitute is looking for a creative and performance-driven Social Media Executive who can manage our social media presence, grow audience engagement, and execute data-driven content strategies. The ideal candidate should have hands-on experience in Instagram management, keyword research, KPI tracking, and increasing organic reach across social media platforms.

Key Responsibilities

Manage and grow the company's social media accounts, with a strong focus on Instagram.
Plan, schedule, and publish engaging content across social media platforms.
Conduct keyword and hashtag research to improve content discoverability and reach.
Develop and execute strategies to increase organic reach, engagement, followers, and brand awareness.
Track and analyze social media KPIs such as reach, impressions, engagement rate, follower growth, CTR, and conversions.
Monitor trends, competitor activities, and platform updates to create relevant content.
Coordinate with the design and content teams to ensure high-quality social media campaigns.
Prepare weekly and monthly performance reports with actionable insights.
Respond to comments, messages, and community interactions in a timely manner.

Required Skills

Strong knowledge of Instagram management and best practices.
Experience with keyword research, hashtags, and social media SEO.
Understanding of KPI management and social media analytics.
Ability to create strategies that increase organic reach and engagement.
Knowledge of Meta Business Suite and Instagram Insights.
Excellent written and verbal communication skills.
Creative thinking with strong analytical skills.

Eligibility

1–1.5 years of experience as a Social Media Executive or in a similar role.
Bachelor's degree in Marketing, Communications, Journalism, or a related field is preferred.
Candidates must own a personal laptop.

Why Join Cognitute?

Opportunity to work with a growing and dynamic team.
Hands-on exposure to digital marketing and brand-building initiatives.
Learning-driven work environment with career growth opportunities.

Location: Noida Sector 90 (Work from Office)
Salary: Up to ₹25,000 per month"""


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "datastorage")
    cv_files = [f for f in os.listdir(data_dir) if f.lower().endswith(('.pdf', '.docx'))]
    cv_files.sort()

    print(f"Found {len(cv_files)} CVs: {cv_files}\n")
    print("=" * 80)

    results = []

    for cv_file in cv_files:
        cv_path = os.path.join(data_dir, cv_file)
        print(f"\nProcessing: {cv_file}")
        print("-" * 80)

        with open(cv_path, "rb") as f:
            resume_text = extract_text_from_file(f)

        print(f"Resume text length: {len(resume_text)} chars")

        scores = compute_scores(resume_text, JD_TEXT)

        llm_eval = scores.get("llm_evaluation", {})

        skill_m = llm_eval.get("skill_match", {})
        title_m = llm_eval.get("title_match", {})
        exp_m = llm_eval.get("experience_match", {})
        overall_m = llm_eval.get("overall_match", {})

        print(f"\n--- FUZZY SCORES (0.0-1.0) ---")
        print(f"  Skill:       {scores['skill']}")
        print(f"  Title:       {scores['title']}")
        print(f"  Experience:  {scores['experience']}")
        print(f"  Overall:     {scores['overall']}")

        print(f"\n--- LLM EVALUATION (0-100) ---")
        print(f"  Skill Match:       {skill_m.get('score', 'N/A')}/100")
        print(f"  Title Match:       {title_m.get('score', 'N/A')}/100")
        print(f"  Experience Match:  {exp_m.get('score', 'N/A')}/100")
        print(f"  Overall Match:     {overall_m.get('score', 'N/A')}/100")

        print(f"\n--- SKILLS ---")
        print(f"  Matched ({len(scores.get('skill_matched', []))}): {', '.join(scores.get('skill_matched', []))}")
        print(f"  Missing ({len(scores.get('skill_missing', []))}): {', '.join(scores.get('skill_missing', []))}")

        print(f"\n--- HIRE RECOMMENDATION ---")
        hire = scores.get("hire_recommendation", "N/A")
        hire_reason = scores.get("hire_reason", "")
        print(f"  {hire}")
        print(f"  Reason: {hire_reason}")

        if skill_m.get("matched_skills"):
            print(f"  LLM Matched: {', '.join(skill_m['matched_skills'])}")
        if skill_m.get("missing_skills"):
            print(f"  LLM Missing: {', '.join(skill_m['missing_skills'])}")

        print(f"\n--- WORK HISTORY ---")
        for i, job in enumerate(scores.get("work_history", []), 1):
            yrs = job.get("duration_months", 0) / 12
            print(f"  {i}. {job.get('role', 'N/A')} at {job.get('company', 'Unknown')} "
                  f"({job.get('start_date', '?')} - {job.get('end_date', '?')}, ~{yrs:.1f}yr)")
            if job.get("skills_used"):
                print(f"     Skills: {', '.join(job['skills_used'])}")

        print(f"\n--- JUSTIFICATIONS ---")
        print(f"  Skill:   {skill_m.get('justification', 'N/A')}")
        print(f"  Title:   {title_m.get('justification', 'N/A')}")
        print(f"  Exp:     {exp_m.get('justification', 'N/A')}")
        print(f"  Overall: {overall_m.get('summary', 'N/A')}")

        strengths = overall_m.get("strengths", [])
        gaps = overall_m.get("gaps", [])
        if strengths:
            print(f"\n  Strengths:")
            for s in strengths:
                print(f"    + {s}")
        if gaps:
            print(f"\n  Gaps:")
            for g in gaps:
                print(f"    - {g}")

        results.append((cv_file, scores))

        print("\n" + "=" * 80)

    ranked = sorted(results, key=lambda x: x[1].get("llm_evaluation", {}).get("overall_match", {}).get("score", 0), reverse=True)

    print("\n\n### FINAL RANKING (by LLM Overall Score 0-100) ###\n")
    print(f"  {'Rank':<6} {'CV':<50} {'Overall':<10} {'Fuzzy':<8} {'HIRE?'}")
    print(f"  {'-'*6} {'-'*50} {'-'*10} {'-'*8} {'-'*8}")
    for rank, (cv_file, scores) in enumerate(ranked, 1):
        llm_eval = scores.get("llm_evaluation", {})
        overall = llm_eval.get("overall_match", {}).get("score", 0)
        hire = scores.get("hire_recommendation", "N/A")
        print(f"  #{rank:<5} {cv_file:<50} {overall}/100   {scores['overall']:<8} {hire}")


if __name__ == "__main__":
    main()

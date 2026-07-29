import streamlit as st
import os
from extraction import extract_text_from_file
from matching_engine import compute_scores, summarize_candidate


def _render_skill_badges(skills, color="green"):
    """Render a list of skills as colored text."""
    if not skills:
        return
    colors = {"green": "#2ecc71", "red": "#e74c3c", "blue": "#3498db", "gray": "#95a5a6", "orange": "#e67e22"}
    c = colors.get(color, "#2ecc71")
    html = ""
    for skill in skills:
        html += f'<span style="background:{c};color:white;padding:2px 8px;border-radius:12px;margin:2px;font-size:0.85em;display:inline-block;">{skill}</span> '
    st.markdown(html, unsafe_allow_html=True)


def _render_hire_badge(scores):
    """Render a prominent hire recommendation badge."""
    hire = scores.get("hire_recommendation", "N/A")
    reason = scores.get("hire_reason", "")

    if hire == "Yes":
        bg = "#2ecc71"
        icon = "YES"
    elif hire == "Maybe":
        bg = "#f39c12"
        icon = "MAYBE"
    else:
        bg = "#e74c3c"
        icon = "NO"

    st.markdown(
        f'<div style="background:{bg};color:white;padding:12px 20px;'
        f'border-radius:8px;text-align:center;margin:8px 0;">'
        f'<span style="font-size:1.4em;font-weight:bold;">{icon}</span>'
        f'<br><span style="font-size:0.9em;">{reason}</span></div>',
        unsafe_allow_html=True,
    )


def _render_score_gauge(label, score_0_100):
    """Render a score gauge with progress bar and color coding."""
    if score_0_100 >= 80:
        color = "green"
        verdict = "Excellent"
    elif score_0_100 >= 60:
        color = "blue"
        verdict = "Good"
    elif score_0_100 >= 40:
        color = "orange"
        verdict = "Moderate"
    else:
        color = "red"
        verdict = "Poor"

    st.markdown(f"**{label}**")
    st.progress(score_0_100 / 100)
    st.markdown(f"Score: **{score_0_100}/100** — {verdict}")


def _render_llm_evaluation(llm_eval):
    """Render the full LLM evaluation section with scores, justifications, strengths, gaps."""
    if not llm_eval:
        st.info("LLM evaluation not available.")
        return

    skill = llm_eval.get("skill_match", {})
    title = llm_eval.get("title_match", {})
    exp = llm_eval.get("experience_match", {})
    overall = llm_eval.get("overall_match", {})

    st.subheader("LLM Evaluation Scores")

    col1, col2 = st.columns(2)
    with col1:
        _render_score_gauge("Skill Match", skill.get("score", 0))
    with col2:
        _render_score_gauge("Title Match", title.get("score", 0))

    col3, col4 = st.columns(2)
    with col3:
        _render_score_gauge("Experience Match", exp.get("score", 0))
    with col4:
        _render_score_gauge("Overall Match", overall.get("score", 0))

    st.divider()

    with st.expander("Skill Match Details", expanded=True):
        st.write(skill.get("justification", ""))
        matched = skill.get("matched_skills", [])
        missing = skill.get("missing_skills", [])
        if matched:
            st.markdown("**Matched Skills:**")
            _render_skill_badges(matched, color="green")
        if missing:
            st.markdown("**Missing Skills:**")
            _render_skill_badges(missing, color="red")

    with st.expander("Title Match Justification"):
        st.write(title.get("justification", ""))

    with st.expander("Experience Match Justification"):
        st.write(exp.get("justification", ""))

    with st.expander("Overall Assessment", expanded=True):
        st.write(overall.get("summary", ""))
        strengths = overall.get("strengths", [])
        gaps = overall.get("gaps", [])
        if strengths:
            st.markdown("**Strengths:**")
            for s in strengths:
                st.markdown(f"- {s}")
        if gaps:
            st.markdown("**Gaps:**")
            for g in gaps:
                st.markdown(f"- {g}")


def _render_work_history(work_history):
    """Render work history as a timeline ordered by most recent first."""
    if not work_history:
        st.info("No work history extracted.")
        return

    for i, job in enumerate(work_history):
        company = job.get("company", "Unknown")
        role = job.get("role", "N/A")
        start = job.get("start_date", "?")
        end = job.get("end_date", "?")
        months = job.get("duration_months", 0)
        yrs = months / 12
        skills_used = job.get("skills_used", [])
        responsibilities = job.get("responsibilities", [])

        with st.container():
            st.markdown(f"**{i+1}. {role}** at **{company}**")
            st.caption(f"{start} - {end} (~{yrs:.1f} years)")
            if skills_used:
                st.markdown("**Skills used:**")
                _render_skill_badges(skills_used, color="blue")
            if responsibilities:
                with st.expander(f"Responsibilities ({len(responsibilities)})"):
                    for resp in responsibilities:
                        st.markdown(f"- {resp}")
            st.divider()


def single_resume_matching():
    st.title("Single Resume & JD Matching")

    st.subheader("1. Upload Resume")
    resume_file = st.file_uploader("Upload Candidate Resume", type=["pdf", "docx"])

    st.subheader("2. Job Description")
    jd_mode = st.radio(
        "Input Method for Job Description",
        ["Upload PDF/DOCX", "Type/Paste Text"],
        horizontal=True,
        key="single_jd_mode",
    )

    jd_text = ""
    if jd_mode == "Upload PDF/DOCX":
        jd_file = st.file_uploader("Upload Job Description File", type=["pdf", "docx"])
        if jd_file:
            jd_text = extract_text_from_file(jd_file)
    else:
        jd_text = st.text_area("Paste Job Description Text Here", height=250)

    if st.button("Process"):
        if resume_file and jd_text:
            resume_text = extract_text_from_file(resume_file)

            with st.spinner("Analyzing match..."):
                scores = compute_scores(resume_text, jd_text)
                summary = summarize_candidate(resume_text, jd_text, scores)

            # Overall score
            st.markdown(f"## Overall Match: {scores['overall'] * 100:.0f}%")

            # Hire Recommendation
            _render_hire_badge(scores)

            # LLM Evaluation Scores (0-100)
            llm_eval = scores.get("llm_evaluation")
            if llm_eval:
                _render_llm_evaluation(llm_eval)

            st.divider()

            # Work History
            with st.expander("Work History (Company Order)", expanded=True):
                _render_work_history(scores.get("work_history", []))

            # Skills
            with st.expander("Skills Match Analysis (Fuzzy)", expanded=True):
                st.write(f"**Score: {scores['skill'] * 100:.0f}%**")
                if scores.get("skill_matched"):
                    st.markdown("**Matched Skills:**")
                    _render_skill_badges(scores["skill_matched"], color="green")
                if scores.get("skill_missing"):
                    st.markdown("**Missing Skills:**")
                    _render_skill_badges(scores["skill_missing"], color="red")
                if scores.get("must_missing"):
                    st.warning(
                        f"Missing {len(scores['must_missing'])} must-have skill(s): "
                        + ", ".join(scores["must_missing"])
                    )

            # Title
            with st.expander("Job Title Relevance"):
                st.write(f"**Score: {scores['title'] * 100:.0f}%**")
                st.write(scores["title_explanation"])

            # Experience
            with st.expander("Experience Match"):
                st.write(f"**Score: {scores['experience'] * 100:.0f}%**")
                st.text(scores["experience_explanation"])

            # Overall
            with st.expander("Overall Analysis"):
                st.write(scores["overall_explanation"])

            # Summary
            with st.expander("Detailed Candidate Summary"):
                st.text(summary)
        else:
            if not resume_file:
                st.warning("Please upload a resume to proceed.")
            if not jd_text:
                st.warning("Please provide a Job Description (upload file or paste text) to proceed.")


def multi_resume_ranking():
    st.title("Multiple Resumes & JD Ranking")

    st.subheader("1. Job Description")
    jd_mode = st.radio(
        "Input Method for Job Description",
        ["Upload PDF/DOCX", "Type/Paste Text"],
        horizontal=True,
        key="multi_jd_mode",
    )

    jd_text = ""
    if jd_mode == "Upload PDF/DOCX":
        jd_file = st.file_uploader("Upload Job Description File", type=["pdf", "docx"])
        if jd_file:
            jd_text = extract_text_from_file(jd_file)
    else:
        jd_text = st.text_area("Paste Job Description Text Here", height=250)

    st.subheader("2. Upload Resumes")
    resume_files = st.file_uploader(
        "Upload Resumes", type=["pdf", "docx"], accept_multiple_files=True
    )

    if st.button("Rank Resumes"):
        if jd_text and resume_files:
            all_scores = []

            with st.spinner("Ranking resumes..."):
                for file in resume_files:
                    resume_text = extract_text_from_file(file)
                    scores = compute_scores(resume_text, jd_text)
                    all_scores.append((file.name, scores["overall"], scores))

            ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)

            for item in ranked:
                with st.expander(f"Resume: {item[0]} - Overall Score: {item[1] * 100:.0f}%"):
                    scores = item[2]

                    _render_hire_badge(scores)

                    llm_eval = scores.get("llm_evaluation")
                    if llm_eval:
                        _render_llm_evaluation(llm_eval)
                    st.divider()

                    if scores.get("work_history"):
                        st.markdown("**Work History:**")
                        for i, job in enumerate(scores["work_history"], 1):
                            st.markdown(
                                f"{i}. **{job.get('role', 'N/A')}** at "
                                f"**{job.get('company', 'Unknown')}** "
                                f"({job.get('start_date', '?')} - {job.get('end_date', '?')}, "
                                f"~{job.get('duration_months', 0)/12:.1f}yr)"
                            )
                            if job.get("skills_used"):
                                _render_skill_badges(job["skills_used"], color="blue")

                    if scores.get("skill_matched"):
                        st.markdown("**Matched Skills:**")
                        _render_skill_badges(scores["skill_matched"], color="green")
                    if scores.get("skill_missing"):
                        st.markdown("**Missing Skills:**")
                        _render_skill_badges(scores["skill_missing"], color="red")

                    st.write("Skills:", scores["skill_explanation"])
                    st.write("Title:", scores["title_explanation"])
                    st.write("Experience:", scores["experience_explanation"])
                    st.write("Overall:", scores["overall_explanation"])
        else:
            if not jd_text:
                st.warning("Please provide a Job Description (upload file or paste text) to proceed.")
            if not resume_files:
                st.warning("Please upload at least one resume.")


def gdrive_resume_ranking():
    st.title("Google Drive Resume Ranking")

    st.subheader("1. Connect to Google Drive")

    sa_exists = os.path.exists("service_account.json")
    oauth_exists = os.path.exists("credentials.json")
    token_exists = os.path.exists("token.json")

    if not sa_exists and not oauth_exists and not token_exists:
        st.error(
            "Google Drive credentials not found! Please place either `service_account.json` "
            "or `credentials.json` in the project root directory to connect."
        )
        return

    folder_id = st.text_input(
        "Google Drive Folder ID",
        value=st.session_state.get("fetched_folder_id", ""),
        help="Paste the alphanumeric ID from the Google Drive folder URL",
    )

    if st.button("Fetch Resumes"):
        if folder_id:
            with st.spinner("Connecting to Google Drive and fetching files..."):
                try:
                    from gdrive_integration import list_files_in_folder

                    files = list_files_in_folder(folder_id)
                    st.session_state.gdrive_files = files
                    st.session_state.fetched_folder_id = folder_id
                    if not files:
                        st.info("No PDF or DOCX files found in this Google Drive folder.")
                    else:
                        st.success(f"Found {len(files)} files!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a Google Drive Folder ID.")

    if "gdrive_files" not in st.session_state:
        st.session_state.gdrive_files = []

    if st.session_state.gdrive_files:
        st.write("---")
        st.subheader("2. Select Resumes to Rank")

        file_map = {f["name"]: f for f in st.session_state.gdrive_files}
        selected_names = st.multiselect(
            "Select files",
            options=list(file_map.keys()),
            default=list(file_map.keys()),
            help="Select the resumes you want to download and evaluate",
        )
        selected_files = [file_map[name] for name in selected_names]

        st.subheader("3. Job Description")
        jd_mode = st.radio(
            "Input Method for Job Description",
            ["Upload PDF/DOCX", "Type/Paste Text"],
            horizontal=True,
            key="gdrive_jd_mode",
        )

        jd_text = ""
        if jd_mode == "Upload PDF/DOCX":
            jd_file = st.file_uploader(
                "Upload Job Description File", type=["pdf", "docx"], key="gdrive_jd_file"
            )
            if jd_file:
                jd_text = extract_text_from_file(jd_file)
        else:
            jd_text = st.text_area(
                "Paste Job Description Text Here", height=250, key="gdrive_jd_text"
            )

        if st.button("Rank Google Drive Resumes"):
            if not selected_files:
                st.warning("Please select at least one resume.")
            elif not jd_text:
                st.warning("Please provide a Job Description (upload file or paste text).")
            else:
                from gdrive_integration import download_file_bytes

                all_scores = []
                progress_bar = st.progress(0.0)

                with st.spinner("Downloading and parsing files from Google Drive..."):
                    for idx, f in enumerate(selected_files):
                        try:
                            file_obj = download_file_bytes(f["id"], f["name"])
                            resume_text = extract_text_from_file(file_obj)
                            scores = compute_scores(resume_text, jd_text)
                            all_scores.append((f["name"], scores["overall"], scores))
                        except Exception as e:
                            st.error(f"Failed to process {f['name']}: {str(e)}")

                        progress_bar.progress((idx + 1) / len(selected_files))

                if all_scores:
                    st.success("Analysis complete!")
                    ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)

                    st.subheader("4. Google Drive Ranking Results")
                    for item in ranked:
                        with st.expander(
                            f"Resume: {item[0]} - Overall Score: {item[1] * 100:.0f}%"
                        ):
                            scores = item[2]

                            _render_hire_badge(scores)

                            llm_eval = scores.get("llm_evaluation")
                            if llm_eval:
                                _render_llm_evaluation(llm_eval)
                            st.divider()

                            if scores.get("work_history"):
                                st.markdown("**Work History:**")
                                for i, job in enumerate(scores["work_history"], 1):
                                    st.markdown(
                                        f"{i}. **{job.get('role', 'N/A')}** at "
                                        f"**{job.get('company', 'Unknown')}** "
                                        f"({job.get('start_date', '?')} - {job.get('end_date', '?')}, "
                                        f"~{job.get('duration_months', 0)/12:.1f}yr)"
                                    )
                                    if job.get("skills_used"):
                                        _render_skill_badges(job["skills_used"], color="blue")

                            if scores.get("skill_matched"):
                                st.markdown("**Matched Skills:**")
                                _render_skill_badges(scores["skill_matched"], color="green")
                            if scores.get("skill_missing"):
                                st.markdown("**Missing Skills:**")
                                _render_skill_badges(scores["skill_missing"], color="red")

                            st.write("Skills:", scores["skill_explanation"])
                            st.write("Title:", scores["title_explanation"])
                            st.write("Experience:", scores["experience_explanation"])
                            st.write("Overall:", scores["overall_explanation"])


def main():
    page = st.sidebar.selectbox(
        "Page",
        ["Single Resume Matching", "Multiple Resumes Ranking", "Google Drive Ranking"],
    )
    if page == "Single Resume Matching":
        single_resume_matching()
    elif page == "Multiple Resumes Ranking":
        multi_resume_ranking()
    else:
        gdrive_resume_ranking()


if __name__ == "__main__":
    main()

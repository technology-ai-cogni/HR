import streamlit as st
import os
import pandas as pd
import io
from extraction import extract_text_from_file
from matching_engine import compute_scores, summarize_candidate

# Streamlit Page Config
st.set_page_config(
    page_title="AI Resume Analyser & Candidate Ranking",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Dark UI / Glassmorphism
def _inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Glassmorphism Card Container */
        .main-header {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(12px);
        }
        
        .main-header h1 {
            color: #f8fafc;
            font-weight: 700;
            font-size: 2.2rem;
            margin: 0 0 8px 0;
            background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .main-header p {
            color: #94a3b8;
            font-size: 1.05rem;
            margin: 0;
        }

        /* Metric Cards */
        .glass-card {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            backdrop-filter: blur(8px);
        }

        /* Streamlit Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: rgba(15, 23, 42, 0.6);
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stTabs [data-baseweb="tab"] {
            height: 48px;
            border-radius: 8px;
            color: #94a3b8;
            font-weight: 500;
            padding: 0 24px;
            background-color: transparent;
            border: none;
            transition: all 0.2s ease;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
            color: #ffffff !important;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }

        /* Skill Pill Badges */
        .badge-pill {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 500;
            margin: 3px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        }
        
        .badge-green { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .badge-red { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .badge-blue { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
        
        /* Hire Verdict Banner */
        .verdict-box {
            padding: 16px 24px;
            border-radius: 12px;
            text-align: center;
            margin: 12px 0;
            font-weight: 600;
        }
        .verdict-yes { background: linear-gradient(135deg, #10b981, #059669); color: white; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4); }
        .verdict-maybe { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4); }
        .verdict-no { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4); }
        </style>
    """, unsafe_allow_html=True)


POSITIONS = [
    "Select Position...",
    "Associate SEO",
    "React Developer",
    "Python Developer",
    "N8n Developer",
    "AI Automation Developer",
    "AI Python Developer",
    "Growth Ops Manager",
    "Creative and Content Head",
    "Sales Manager",
    "Content Writer",
    "Graphic and Motion Designers",
    "SEO Manager",
    "Social Media Executive",
    "Social Media/ Content Intern",
    "Sales/Marketing Intern",
    "SEO Intern",
    "HR Executive",
    "Growth Associate",
    "Finance executive",
    "AI engineer",
    "Next js developer",
    "Node js Developer",
    "Tech Intern",
    "QA Engineer",
    "Researcher"
]


def _match_default_position(cand_title):
    if not cand_title:
        return "Select Position..."
    title_lower = cand_title.lower().strip()
    for pos in POSITIONS[1:]:
        if pos.lower() in title_lower or title_lower in pos.lower():
            return pos
    return "Select Position..."


def generate_download_file(df):
    """Generate Excel bytes if openpyxl is installed, otherwise CSV bytes as fallback."""
    try:
        import openpyxl
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Candidate Rankings')
        return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
    except ImportError:
        csv_data = df.to_csv(index=False).encode('utf-8')
        return csv_data, "text/csv", "csv"


def create_ranking_dataframe(ranked_results):
    """Build a clean pandas DataFrame for grid view and export.
    ranked_results: list of tuples (file_name, overall_score_float, scores_dict)
    """
    rows = []
    for rank, (file_name, overall_score, scores) in enumerate(ranked_results, 1):
        r_data = scores.get("resume_data", {})
        cand_name = r_data.get("candidate_name") or file_name
        email = r_data.get("email", "")
        phone = r_data.get("phone_number", "")
        cand_title = r_data.get("job_title", "")
        default_pos = _match_default_position(cand_title)
        hire_rec = scores.get("hire_recommendation", "N/A")
        hire_reason = scores.get("hire_reason", "")

        matched_skills = ", ".join(scores.get("skill_matched", []))
        missing_skills = ", ".join(scores.get("skill_missing", []))

        llm_eval = scores.get("llm_evaluation", {})
        overall_llm = llm_eval.get("overall_match", {}).get("score", int(scores.get("overall", 0) * 100))
        skill_llm = llm_eval.get("skill_match", {}).get("score", int(scores.get("skill", 0) * 100))
        title_llm = llm_eval.get("title_match", {}).get("score", int(scores.get("title", 0) * 100))
        exp_llm = llm_eval.get("experience_match", {}).get("score", int(scores.get("experience", 0) * 100))

        rows.append({
            "Rank": rank,
            "Candidate Name": cand_name,
            "Email": email,
            "Phone Number": phone,
            "Position": default_pos,
            "File Name": file_name,
            "Hire Verdict": hire_rec,
            "Overall Score (%)": overall_llm,
            "Skill Score (%)": skill_llm,
            "Title Score (%)": title_llm,
            "Experience Score (%)": exp_llm,
            "Candidate Title": cand_title or "N/A",
            "Years of Experience": r_data.get("years_of_experience", 0),
            "Matched Skills": matched_skills,
            "Missing Skills": missing_skills,
            "Hiring Stage": "",
            "Remarks": "",
            "Recommendation Reason": hire_reason
        })

    return pd.DataFrame(rows)


def render_ranking_grid_and_download(ranked_results, filename_prefix="candidate_rankings"):
    """Display results in an interactive data editor grid table with a download button."""
    df = create_ranking_dataframe(ranked_results)

    st.subheader("📊 Candidate Evaluation Grid")

    # Render interactive Streamlit Data Editor grid
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Position": st.column_config.SelectboxColumn(
                "Position",
                help="Assign candidate position",
                options=POSITIONS,
                required=False,
                width="medium",
            ),
            "Hiring Stage": st.column_config.TextColumn(
                "Hiring Stage",
                help="Enter hiring stage (e.g. Interview 1, Offered, Hired)",
                width="medium",
            ),
            "Remarks": st.column_config.TextColumn(
                "Remarks",
                help="Enter remarks or notes",
                width="large",
            ),
            "Overall Score (%)": st.column_config.NumberColumn("Overall (%)", format="%d%%"),
            "Skill Score (%)": st.column_config.NumberColumn("Skill (%)", format="%d%%"),
            "Title Score (%)": st.column_config.NumberColumn("Title (%)", format="%d%%"),
            "Experience Score (%)": st.column_config.NumberColumn("Exp (%)", format="%d%%"),
            "Hire Verdict": st.column_config.TextColumn("Verdict"),
        },
        key=f"editor_{filename_prefix}"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Showing structured evaluation summary for **{len(edited_df)}** candidate(s). Edit Position, Hiring Stage, and Remarks directly in the grid above before downloading.")
    with col2:
        file_bytes, mime_type, ext = generate_download_file(edited_df)
        label_text = "📥 Export Excel (.xlsx)" if ext == "xlsx" else "📥 Export CSV (.csv)"
        st.download_button(
            label=label_text,
            data=file_bytes,
            file_name=f"{filename_prefix}.{ext}",
            mime=mime_type,
            use_container_width=True,
            type="primary"
        )


def _render_skill_badges(skills, color="green"):
    """Render a list of skills as colored text badges."""
    if not skills:
        return
    css_class = f"badge-{color}"
    html = "".join([f'<span class="badge-pill {css_class}">{skill}</span>' for skill in skills])
    st.markdown(html, unsafe_allow_html=True)


def _render_hire_badge(scores):
    """Render a prominent hire recommendation badge."""
    hire = scores.get("hire_recommendation", "N/A")
    reason = scores.get("hire_reason", "")

    if hire == "Yes":
        class_name = "verdict-yes"
        icon = "YES - RECOMMENDED"
    elif hire == "Maybe":
        class_name = "verdict-maybe"
        icon = "MAYBE - CONDITIONAL FIT"
    else:
        class_name = "verdict-no"
        icon = "NO - HIGH GAPS"

    st.markdown(
        f'<div class="verdict-box {class_name}">'
        f'<div style="font-size:1.3rem;">{icon}</div>'
        f'<div style="font-size:0.9rem; margin-top:4px; opacity:0.95;">{reason}</div></div>',
        unsafe_allow_html=True,
    )


def _render_score_gauge(label, score_0_100):
    """Render a score gauge with progress bar and color coding."""
    if score_0_100 >= 80:
        verdict = "Excellent"
    elif score_0_100 >= 60:
        verdict = "Good"
    elif score_0_100 >= 40:
        verdict = "Moderate"
    else:
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

    st.subheader("Match Breakdown")

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

    with st.expander("Skill Alignment Details", expanded=True):
        st.write(skill.get("justification", ""))
        matched = skill.get("matched_skills", [])
        missing = skill.get("missing_skills", [])
        if matched:
            st.markdown("**Matched Skills:**")
            _render_skill_badges(matched, color="green")
        if missing:
            st.markdown("**Missing Skills:**")
            _render_skill_badges(missing, color="red")

    with st.expander("Title Match Explanation"):
        st.write(title.get("justification", ""))

    with st.expander("Experience Match Explanation"):
        st.write(exp.get("justification", ""))

    with st.expander("Overall Candidate Fit", expanded=True):
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
            st.caption(f"🗓️ {start} - {end} (~{yrs:.1f} years)")
            if skills_used:
                st.markdown("**Skills Used:**")
                _render_skill_badges(skills_used, color="blue")
            if responsibilities:
                with st.expander(f"Key Responsibilities ({len(responsibilities)})"):
                    for resp in responsibilities:
                        st.markdown(f"- {resp}")
            st.divider()


def tab_batch_ranking():
    st.subheader("⚡ Batch Resume Ranking")
    st.caption("Upload multiple candidate resumes and rank them against a target Job Description.")

    col_jd, col_resumes = st.columns(2)

    with col_jd:
        st.markdown("#### 1. Job Description")
        jd_mode = st.radio(
            "Input Method for Job Description",
            ["Paste Text", "Upload File (PDF/DOCX)"],
            horizontal=True,
            key="batch_jd_mode",
        )

        jd_text = ""
        if jd_mode == "Upload File (PDF/DOCX)":
            jd_file = st.file_uploader("Upload Job Description File", type=["pdf", "docx"], key="batch_jd_file")
            if jd_file:
                jd_text = extract_text_from_file(jd_file)
        else:
            jd_text = st.text_area("Paste Job Description Text Here", height=200, key="batch_jd_text", placeholder="Paste required skills, responsibilities, and experience...")

    with col_resumes:
        st.markdown("#### 2. Candidate Resumes")
        resume_files = st.file_uploader(
            "Upload Candidate Resumes (PDF or DOCX)", type=["pdf", "docx"], accept_multiple_files=True, key="batch_resumes"
        )

    st.markdown("---")

    if st.button("🚀 Rank & Analyze Candidates", type="primary", use_container_width=True):
        if not jd_text:
            st.warning("Please provide a Job Description (paste text or upload file).")
        elif not resume_files:
            st.warning("Please upload at least one resume.")
        else:
            all_scores = []
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            for idx, file in enumerate(resume_files):
                status_text.text(f"Parsing resume {idx+1}/{len(resume_files)}: {file.name}...")
                resume_text = extract_text_from_file(file)
                scores = compute_scores(resume_text, jd_text)
                all_scores.append((file.name, scores["overall"], scores))
                progress_bar.progress((idx + 1) / len(resume_files))

            status_text.empty()
            progress_bar.empty()

            ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)

            # Grid view and download button
            render_ranking_grid_and_download(ranked, filename_prefix="batch_candidate_rankings")
            st.divider()

            st.subheader("🔍 Detailed Candidate Breakdowns")
            for item in ranked:
                scores = item[2]
                r_data = scores.get("resume_data", {})
                cand_name = r_data.get("candidate_name") or item[0]
                with st.expander(f"👤 {cand_name} ({item[0]}) — Overall Score: {item[1] * 100:.0f}%"):
                    _render_hire_badge(scores)

                    llm_eval = scores.get("llm_evaluation")
                    if llm_eval:
                        _render_llm_evaluation(llm_eval)
                    st.divider()

                    if scores.get("work_history"):
                        st.markdown("**Work History Summary:**")
                        _render_work_history(scores["work_history"])

                    if scores.get("skill_matched"):
                        st.markdown("**Matched Skills:**")
                        _render_skill_badges(scores["skill_matched"], color="green")
                    if scores.get("skill_missing"):
                        st.markdown("**Missing Skills:**")
                        _render_skill_badges(scores["skill_missing"], color="red")


def tab_single_matching():
    st.subheader("📄 Single Candidate Match")
    st.caption("Evaluate a single candidate against a Job Description.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 1. Candidate Resume")
        resume_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"], key="single_resume")

    with col2:
        st.markdown("#### 2. Job Description")
        jd_mode = st.radio(
            "Input Method for Job Description",
            ["Paste Text", "Upload File (PDF/DOCX)"],
            horizontal=True,
            key="single_jd_mode",
        )

        jd_text = ""
        if jd_mode == "Upload File (PDF/DOCX)":
            jd_file = st.file_uploader("Upload JD File", type=["pdf", "docx"], key="single_jd_file")
            if jd_file:
                jd_text = extract_text_from_file(jd_file)
        else:
            jd_text = st.text_area("Paste JD Text", height=200, key="single_jd_text", placeholder="Paste job description here...")

    st.markdown("---")

    if st.button("🚀 Analyze Candidate", type="primary", use_container_width=True):
        if not resume_file:
            st.warning("Please upload a resume file.")
        elif not jd_text:
            st.warning("Please provide a Job Description.")
        else:
            with st.spinner("Evaluating candidate..."):
                resume_text = extract_text_from_file(resume_file)
                scores = compute_scores(resume_text, jd_text)
                summary = summarize_candidate(resume_text, jd_text, scores)

            single_result = [(resume_file.name, scores["overall"], scores)]
            render_ranking_grid_and_download(single_result, filename_prefix="single_candidate_evaluation")
            st.divider()

            _render_hire_badge(scores)

            llm_eval = scores.get("llm_evaluation")
            if llm_eval:
                _render_llm_evaluation(llm_eval)

            st.divider()

            with st.expander("Work History", expanded=True):
                _render_work_history(scores.get("work_history", []))

            with st.expander("Detailed Summary Notes"):
                st.write(summary)


def tab_gdrive_import():
    st.subheader("☁️ Google Drive Resumes Import")
    st.caption("Import candidate resumes directly from a Google Drive folder.")

    sa_exists = os.path.exists("service_account.json")
    oauth_exists = os.path.exists("credentials.json")
    token_exists = os.path.exists("token.json")

    if not sa_exists and not oauth_exists and not token_exists:
        st.error(
            "Google Drive credentials not found! Place either `service_account.json` "
            "or `credentials.json` in the root folder to connect."
        )
        return

    col_id, col_btn = st.columns([3, 1])
    with col_id:
        folder_id = st.text_input(
            "Google Drive Folder ID",
            value=st.session_state.get("fetched_folder_id", ""),
            placeholder="Paste alphanumeric folder ID from URL...",
        )
    with col_btn:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        fetch_btn = st.button("📥 Fetch Files", use_container_width=True)

    if fetch_btn and folder_id:
        with st.spinner("Connecting to Google Drive..."):
            try:
                from gdrive_integration import list_files_in_folder

                files = list_files_in_folder(folder_id)
                st.session_state.gdrive_files = files
                st.session_state.fetched_folder_id = folder_id
                if not files:
                    st.info("No PDF or DOCX files found in this folder.")
                else:
                    st.success(f"Found {len(files)} files in Google Drive!")
            except Exception as e:
                st.error(f"Error connecting to Google Drive: {str(e)}")

    if "gdrive_files" not in st.session_state:
        st.session_state.gdrive_files = []

    if st.session_state.gdrive_files:
        st.divider()
        file_map = {f["name"]: f for f in st.session_state.gdrive_files}
        selected_names = st.multiselect(
            "Select Resumes to Rank",
            options=list(file_map.keys()),
            default=list(file_map.keys()),
        )
        selected_files = [file_map[name] for name in selected_names]

        st.markdown("#### Job Description")
        jd_text = st.text_area("Paste Job Description Text", height=180, key="gdrive_jd_text", placeholder="Paste job description...")

        if st.button("🚀 Rank Selected Google Drive Resumes", type="primary", use_container_width=True):
            if not selected_files:
                st.warning("Please select at least one resume.")
            elif not jd_text:
                st.warning("Please provide a Job Description.")
            else:
                from gdrive_integration import download_file_bytes

                all_scores = []
                progress_bar = st.progress(0.0)

                for idx, f in enumerate(selected_files):
                    try:
                        file_obj = download_file_bytes(f["id"], f["name"])
                        resume_text = extract_text_from_file(file_obj)
                        scores = compute_scores(resume_text, jd_text)
                        all_scores.append((f["name"], scores["overall"], scores))
                    except Exception as e:
                        st.error(f"Failed to process {f['name']}: {str(e)}")

                    progress_bar.progress((idx + 1) / len(selected_files))

                progress_bar.empty()

                if all_scores:
                    ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)
                    render_ranking_grid_and_download(ranked, filename_prefix="gdrive_candidate_rankings")


def main():
    _inject_custom_css()

    st.markdown("""
        <div class="main-header">
            <h1>💼 AI Resume Analyser & Candidate Ranking</h1>
            <p>Automated resume screening, candidate score calculation, and structured HR evaluation grids powered by LLM.</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "⚡ Batch Resume Ranking",
        "📄 Single Candidate Match",
        "☁️ Google Drive Import"
    ])

    with tab1:
        tab_batch_ranking()
    with tab2:
        tab_single_matching()
    with tab3:
        tab_gdrive_import()


if __name__ == "__main__":
    main()

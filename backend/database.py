import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db_connection():
    """Create a database connection with dict-like row formatting."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database schema and migrate columns if needed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE,
            candidate_name TEXT,
            email TEXT,
            phone_number TEXT,
            job_title TEXT,
            position TEXT DEFAULT 'Select Position...',
            hire_verdict TEXT,
            overall_score INTEGER,
            skill_score INTEGER,
            title_score INTEGER,
            exp_score INTEGER,
            years_of_experience REAL DEFAULT 0,
            required_experience TEXT DEFAULT '0 Years',
            candidate_experience TEXT DEFAULT '0 Months',
            matched_skills TEXT,
            missing_skills TEXT,
            hiring_stage TEXT DEFAULT 'Applied',
            remarks TEXT DEFAULT '',
            recommendation_reason TEXT,
            full_scores_json TEXT,
            resume_link TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    for col, default_val in [("resume_link", "''"), ("required_experience", "'0 Years'"), ("candidate_experience", "'0 Months'")]:
        try:
            cursor.execute(f"ALTER TABLE evaluations ADD COLUMN {col} TEXT DEFAULT {default_val};")
        except Exception:
            pass # Column already exists

    conn.commit()
    conn.close()

def save_candidate_evaluation(res: Dict[str, Any]) -> int:
    """Save or update candidate evaluation from LLM scoring result."""
    conn = get_db_connection()
    cursor = conn.cursor()

    scores = res.get("scores", {})
    rdata = scores.get("resume_data", {})
    llm_eval = scores.get("llm_evaluation", {})

    file_name = res.get("file_name", "unknown")
    cand_name = res.get("candidate_name") or rdata.get("candidate_name") or file_name
    email = res.get("email") or rdata.get("email") or ""
    phone = res.get("phone_number") or rdata.get("phone_number") or ""
    job_title = rdata.get("job_title") or ""
    verdict = scores.get("hire_recommendation") or "No"
    # Ensure binary Yes/No verdict only
    if verdict not in ["Yes", "No"]:
        verdict = "Yes" if verdict == "Maybe" and float(res.get("overall_score", 0)) >= 0.6 else "No"

    overall = int((res.get("overall_score") or 0) * (1 if res.get("overall_score", 0) > 1 else 100))
    skill_sc = int(llm_eval.get("skill_match", {}).get("score", 0))
    title_sc = int(llm_eval.get("title_match", {}).get("score", 0))
    exp_sc = int(llm_eval.get("experience_match", {}).get("score", 0))
    years_exp = float(rdata.get("years_of_experience") or 0)
    req_exp = scores.get("required_experience") or "0 Years"
    cand_exp = scores.get("candidate_experience") or "0 Months"

    matched_skills = json.dumps(scores.get("skill_matched", []))
    missing_skills = json.dumps(scores.get("skill_missing", []))
    reason = scores.get("hire_reason") or ""
    resume_link = res.get("resume_link") or scores.get("resume_link") or ""
    position = res.get("position") or "Select Position..."
    full_json = json.dumps(res)

    cursor.execute("""
        INSERT INTO evaluations (
            file_name, candidate_name, email, phone_number, job_title, position,
            hire_verdict, overall_score, skill_score, title_score, exp_score,
            years_of_experience, required_experience, candidate_experience,
            matched_skills, missing_skills, recommendation_reason,
            full_scores_json, resume_link, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(file_name) DO UPDATE SET
            candidate_name=excluded.candidate_name,
            email=excluded.email,
            phone_number=excluded.phone_number,
            job_title=excluded.job_title,
            position=CASE WHEN excluded.position != 'Select Position...' THEN excluded.position ELSE evaluations.position END,
            hire_verdict=excluded.hire_verdict,
            overall_score=excluded.overall_score,
            skill_score=excluded.skill_score,
            title_score=excluded.title_score,
            exp_score=excluded.exp_score,
            years_of_experience=excluded.years_of_experience,
            required_experience=excluded.required_experience,
            candidate_experience=excluded.candidate_experience,
            matched_skills=excluded.matched_skills,
            missing_skills=excluded.missing_skills,
            recommendation_reason=excluded.recommendation_reason,
            full_scores_json=excluded.full_scores_json,
            resume_link=CASE WHEN excluded.resume_link != '' THEN excluded.resume_link ELSE evaluations.resume_link END,
            updated_at=CURRENT_TIMESTAMP;
    """, (
        file_name, cand_name, email, phone, job_title, position,
        verdict, overall, skill_sc, title_sc, exp_sc,
        years_exp, req_exp, cand_exp,
        matched_skills, missing_skills, reason,
        full_json, resume_link
    ))

    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def get_all_candidates() -> List[Dict[str, Any]]:
    """Retrieve all candidates stored in SQLite database in natural chronological order (1, 2, 3...)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM evaluations ORDER BY id ASC;
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for rank, row in enumerate(rows, 1):
        item = dict(row)
        full_json = {}
        if item.get("full_scores_json"):
            try:
                full_json = json.loads(item["full_scores_json"])
            except Exception:
                pass

        scores_dict = full_json.get("scores", {})
        verdict = item["hire_verdict"]
        if verdict not in ["Yes", "No"]:
            verdict = "No"

        req_exp = item.get("required_experience") or scores_dict.get("required_experience") or "0 Years"
        cand_exp = item.get("candidate_experience") or scores_dict.get("candidate_experience") or "0 Months"

        # Update scores dict with exact experience
        scores_dict["required_experience"] = req_exp
        scores_dict["candidate_experience"] = cand_exp
        scores_dict["hire_recommendation"] = verdict

        results.append({
            "id": item["id"],
            "rank": rank,
            "file_name": item["file_name"],
            "candidate_name": item["candidate_name"],
            "email": item["email"],
            "phone_number": item["phone_number"],
            "position": item["position"],
            "hire_verdict": verdict,
            "required_experience": req_exp,
            "candidate_experience": cand_exp,
            "hiring_stage": item["hiring_stage"],
            "remarks": item["remarks"],
            "resume_link": item.get("resume_link") or "",
            "overall_score": item["overall_score"] / 100.0,
            "scores": scores_dict
        })
    return results

def update_candidate_grid_fields(cand_id: int, position: Optional[str] = None, hiring_stage: Optional[str] = None, remarks: Optional[str] = None) -> bool:
    """Update user edits (position, hiring_stage, remarks) in SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    params = []
    if position is not None:
        updates.append("position = ?")
        params.append(position)
    if hiring_stage is not None:
        updates.append("hiring_stage = ?")
        params.append(hiring_stage)
    if remarks is not None:
        updates.append("remarks = ?")
        params.append(remarks)

    if not updates:
        conn.close()
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(cand_id)

    query = f"UPDATE evaluations SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def delete_candidate_record(cand_id: int) -> bool:
    """Delete candidate record from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluations WHERE id = ?", (cand_id,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def clear_all_evaluations() -> bool:
    """Clear all candidate evaluations from local SQLite database without affecting Google Sheets."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluations;")
    conn.commit()
    conn.close()
    return True

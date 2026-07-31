import os
import json
import requests
from typing import List, Dict, Any, Optional

HEADERS = [
    "Rank",
    "Candidate Name",
    "Email",
    "Phone Number",
    "Position",
    "File Name",
    "Verdict",
    "Required Experience",
    "Candidate Experience",
    "Hiring Stage",
    "Remarks",
    "Recommendation Reason",
    "Resume Link"
]

def get_webhook_url():
    return os.getenv("GOOGLE_SHEET_WEBHOOK_URL")

def get_gspread_client(target_worksheet: Optional[str] = None):
    """Create and authenticate a gspread client, opening a specific worksheet if requested."""
    from dotenv import load_dotenv
    load_dotenv(override=True)

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None, "gspread or google-auth package is not installed."

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    json_path_or_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not sheet_id:
        return None, "GOOGLE_SHEET_ID environment variable is not set in backend/.env"

    creds = None
    if json_path_or_str:
        try:
            if os.path.exists(json_path_or_str):
                creds = Credentials.from_service_account_file(
                    json_path_or_str,
                    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                )
            else:
                json_data = json.loads(json_path_or_str)
                creds = Credentials.from_service_account_info(
                    json_data,
                    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                )
        except Exception as e:
            return None, f"Failed to load service account credentials: {e}"

    if not creds:
        possible_files = ["service_account.json", "credentials.json"] + [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".json")]
        for p in possible_files:
            full_path = os.path.join(os.path.dirname(__file__), p)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as fp:
                        data = json.load(fp)
                        if isinstance(data, dict) and data.get("type") == "service_account":
                            creds = Credentials.from_service_account_file(
                                full_path,
                                scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                            )
                            break
                except Exception:
                    pass

    if not creds:
        return None, "No valid Google Service Account JSON key found in backend directory."

    try:
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)

        ws_name = target_worksheet or os.getenv("GOOGLE_WORKSHEET_NAME")
        worksheet = None
        if ws_name:
            try:
                worksheet = sh.worksheet(ws_name)
            except Exception:
                pass

        if not worksheet:
            try:
                worksheet = sh.sheet1
            except Exception:
                worksheets = sh.worksheets()
                if worksheets:
                    worksheet = worksheets[0]

        return worksheet, None
    except Exception as e:
        return None, f"Failed to open Google Sheet: {e}"


def get_available_worksheets() -> List[str]:
    """Fetch all worksheet tab names inside the Google Spreadsheet."""
    sheet, err = get_gspread_client()
    if err or not sheet:
        return []
    try:
        sh = sheet.spreadsheet
        return [w.title for w in sh.worksheets()]
    except Exception as e:
        print(f"Error fetching worksheet tab titles: {e}")
        return []


def init_gsheet_headers() -> bool:
    """Initialize headers in Google Sheet if empty."""
    webhook_url = get_webhook_url()
    if webhook_url:
        print("Google Sheet Apps Script Webhook configured!")
        return True

    sheet, err = get_gspread_client()
    if err or not sheet:
        print(f"Google Sheet Init Notice: {err}")
        return False

    try:
        first_row = sheet.row_values(1)
        if not first_row:
            sheet.append_row(HEADERS)
        return True
    except Exception as e:
        print(f"Error setting Google Sheet headers: {e}")
        return False


def sync_candidates_to_gsheet(candidates: List[Dict[str, Any]]) -> bool:
    """Sync list of candidates to Google Sheet (supports Apps Script Webhook & Service Account)."""
    webhook_url = get_webhook_url()
    
    rows = [HEADERS]
    for c in candidates:
        rData = c.get("scores", {}).get("resume_data", {})

        cand_name = c.get("candidate_name") or rData.get("candidate_name") or c.get("file_name", "")
        email = c.get("email") or rData.get("email") or ""
        phone = c.get("phone_number") or rData.get("phone_number") or ""
        pos = c.get("position") or rData.get("job_title") or "Select Position..."
        file_name = c.get("file_name", "")
        verdict = c.get("hire_verdict") or c.get("scores", {}).get("hire_recommendation") or "No"
        if verdict not in ["Yes", "No"]:
            verdict = "No"

        req_exp = c.get("required_experience") or c.get("scores", {}).get("required_experience") or "0 Years"
        cand_exp = c.get("candidate_experience") or c.get("scores", {}).get("candidate_experience") or "0 Months"
        stage = c.get("hiring_stage") or ""
        remarks = c.get("remarks") or ""
        reason = c.get("scores", {}).get("hire_reason") or ""
        resume_link = c.get("resume_link") or ""

        rows.append([
            c.get("rank", 1),
            cand_name,
            email,
            phone,
            pos,
            file_name,
            verdict,
            req_exp,
            cand_exp,
            stage,
            remarks,
            reason,
            resume_link
        ])

    if webhook_url:
        try:
            res = requests.post(webhook_url, json={"action": "sync_all", "rows": rows}, timeout=10)
            return res.ok
        except Exception as e:
            print(f"Webhook Sync Error: {e}")
            return False

    sheet, err = get_gspread_client()
    if err or not sheet:
        print(f"Google Sheet Sync Notice: {err}")
        return False

    try:
        existing_rows = sheet.get_all_values()
        if not existing_rows:
            # Sheet is completely empty, safe to write headers and rows
            sheet.update("A1", rows)
            return True

        # Sheet already has headers and data! NEVER CLEAR THE SHEET!
        # Append candidate evaluation rows safely without wiping custom columns
        existing_file_names = set()
        for r in existing_rows[1:]:
            if len(r) >= 6 and r[5]:
                existing_file_names.add(r[5].strip().lower())

        for row_data in rows[1:]:
            file_name = row_data[5] if len(row_data) > 5 else ""
            if file_name and file_name.strip().lower() in existing_file_names:
                continue # Candidate already exists in sheet, avoid duplicate overwrite

            sheet.append_row(row_data)
        return True
    except Exception as e:
        print(f"Failed to sync candidates to Google Sheet: {e}")
        return False


def fetch_candidates_from_gsheet() -> List[Dict[str, Any]]:
    """Read all rows from Google Sheet to reflect external edits back into dashboard."""
    webhook_url = get_webhook_url()
    if webhook_url:
        try:
            res = requests.get(webhook_url, timeout=10)
            if not res.ok:
                return []
            raw_data = res.json()
            if not raw_data or len(raw_data) < 2:
                return []
            
            headers = raw_data[0]
            candidates = []
            for idx, row in enumerate(raw_data[1:], 1):
                if not row or len(row) < 6:
                    continue
                row_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                candidates.append({
                    "rank": row_dict.get("Rank") or idx,
                    "candidate_name": row_dict.get("Candidate Name", ""),
                    "email": row_dict.get("Email", ""),
                    "phone_number": row_dict.get("Phone Number", ""),
                    "position": row_dict.get("Position", "Select Position..."),
                    "file_name": row_dict.get("File Name", ""),
                    "hire_verdict": row_dict.get("Verdict", "N/A"),
                    "overall_score": float(row_dict.get("Overall Score (%)") or 0) / 100.0,
                    "skill_score": row_dict.get("Skill Score (%)", 0),
                    "title_score": row_dict.get("Title Score (%)", 0),
                    "exp_score": row_dict.get("Exp Score (%)", 0),
                    "hiring_stage": row_dict.get("Hiring Stage", ""),
                    "remarks": row_dict.get("Remarks", ""),
                    "recommendation_reason": row_dict.get("Recommendation Reason", "")
                })
            return candidates
        except Exception as e:
            print(f"Webhook Fetch Error: {e}")
            return []

    sheet, err = get_gspread_client()
    if err or not sheet:
        print(f"Google Sheet Fetch Notice: {err}")
        return []

    try:
        all_values = sheet.get_all_records()
        candidates = []
        for idx, row in enumerate(all_values, 1):
            verdict = row.get("Verdict") or "No"
            if verdict not in ["Yes", "No"]:
                verdict = "No"

            candidates.append({
                "rank": row.get("Rank") or idx,
                "candidate_name": row.get("Candidate Name", ""),
                "email": row.get("Email", ""),
                "phone_number": row.get("Phone Number", ""),
                "position": row.get("Position", "Select Position..."),
                "file_name": row.get("File Name", ""),
                "hire_verdict": verdict,
                "required_experience": row.get("Required Experience", "0 Years"),
                "candidate_experience": row.get("Candidate Experience", "0 Months"),
                "hiring_stage": row.get("Hiring Stage", ""),
                "remarks": row.get("Remarks", ""),
                "recommendation_reason": row.get("Recommendation Reason", ""),
                "resume_link": row.get("Resume Link", "")
            })
        return candidates
    except Exception as e:
        print(f"Error fetching candidates from Google Sheet: {e}")
        return []


def update_gsheet_row_by_filename(file_name: str, position: Optional[str] = None, hiring_stage: Optional[str] = None, remarks: Optional[str] = None) -> bool:
    """Find row matching file_name and update Position, Hiring Stage, and Remarks."""
    webhook_url = get_webhook_url()
    if webhook_url:
        try:
            res = requests.post(webhook_url, json={
                "action": "update_cell",
                "file_name": file_name,
                "position": position,
                "hiring_stage": hiring_stage,
                "remarks": remarks
            }, timeout=10)
            return res.ok
        except Exception as e:
            print(f"Webhook Cell Update Error: {e}")
            return False

    sheet, err = get_gspread_client()
    if err or not sheet:
        return False

    try:
        cell = sheet.find(file_name, in_column=6)
        if not cell:
            return False

        row_idx = cell.row
        if position is not None:
            sheet.update_cell(row_idx, 5, position)
        if hiring_stage is not None:
            sheet.update_cell(row_idx, 12, hiring_stage)
        if remarks is not None:
            sheet.update_cell(row_idx, 13, remarks)
        return True
    except Exception as e:
        print(f"Error updating cell in Google Sheet: {e}")
        return False


def fetch_raw_gsheet_rows(target_worksheet: Optional[str] = None):
    """Fetch raw headers and values directly from a specific Google Sheet tab."""
    sheet, err = get_gspread_client(target_worksheet=target_worksheet)
    if err or not sheet:
        return [], []
    
    try:
        all_values = sheet.get_all_values()
        if not all_values:
            return [], []
        headers = all_values[0]
        rows = all_values[1:]
        return headers, rows
    except Exception as e:
        print(f"Error fetching raw Google Sheet values: {e}")
        return [], []

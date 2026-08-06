import os
import io
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from extraction import extract_text_from_file
from matching_engine import compute_scores, summarize_candidate
from app import create_ranking_dataframe, generate_download_file, POSITIONS
from database import (
    init_db,
    save_candidate_evaluation,
    get_all_candidates,
    update_candidate_grid_fields,
    delete_candidate_record,
    clear_all_evaluations
)
from gsheet_integration import (
    init_gsheet_headers,
    sync_candidates_to_gsheet,
    fetch_candidates_from_gsheet,
    update_gsheet_row_by_filename
)

app = FastAPI(title="Resume Analyser API", version="1.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Initialize SQLite database & Google Sheets headers on FastAPI startup."""
    init_db()
    init_gsheet_headers()


class ExportRequest(BaseModel):
    candidates: List[dict]


class GDriveRankRequest(BaseModel):
    folder_id: str
    selected_files: List[dict]
    jd_text: str
    target_position: Optional[str] = None


class UpdateCandidateRequest(BaseModel):
    position: Optional[str] = None
    hiring_stage: Optional[str] = None
    remarks: Optional[str] = None


@app.get("/")
def read_root():
    return {"status": "online", "message": "Resume Analyser FastAPI Backend Running"}


@app.get("/api/positions")
def get_positions():
    return {"positions": POSITIONS}


@app.get("/api/candidates")
def list_candidates():
    """Fetch all saved candidate evaluations from SQLite database & auto-sync to Google Sheet."""
    try:
        candidates = get_all_candidates()
        try:
            sync_candidates_to_gsheet(candidates)
        except Exception as sheet_err:
            print(f"Auto Google Sheet sync error: {sheet_err}")
        return {"status": "success", "candidates": candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch candidates: {str(e)}")


@app.get("/api/gsheet/sync")
def sync_gsheet():
    """Fetch latest candidate changes made directly in Google Sheets and sync to SQLite DB & Dashboard."""
    try:
        sheet_candidates = fetch_candidates_from_gsheet()
        if sheet_candidates:
            all_c = get_all_candidates()
            for c in sheet_candidates:
                if c.get("file_name"):
                    matched = next((item for item in all_c if item["file_name"] == c["file_name"]), None)
                    if matched:
                        update_candidate_grid_fields(
                            matched["id"],
                            position=c.get("position"),
                            hiring_stage=c.get("hiring_stage"),
                            remarks=c.get("remarks")
                        )

        all_candidates = get_all_candidates()
        sync_candidates_to_gsheet(all_candidates)
        return {"status": "success", "candidates": all_candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Sheet sync failed: {str(e)}")


@app.get("/api/gsheet/worksheets")
def get_worksheets():
    """Fetch list of all available worksheet tabs in the Google Spreadsheet."""
    try:
        from gsheet_integration import get_available_worksheets
        worksheets = get_available_worksheets()
        return {"status": "success", "worksheets": worksheets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch worksheets: {str(e)}")


@app.get("/api/gsheet/live")
def get_live_gsheet(worksheet: Optional[str] = None):
    """Fetch live headers and rows directly from a specific Google Sheet tab."""
    try:
        from gsheet_integration import fetch_raw_gsheet_rows
        headers, rows = fetch_raw_gsheet_rows(target_worksheet=worksheet)
        sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else ""
        return {
            "status": "success",
            "sheet_id": sheet_id,
            "sheet_url": sheet_url,
            "active_worksheet": worksheet or os.getenv("GOOGLE_WORKSHEET_NAME", "Sheet1"),
            "headers": headers,
            "rows": rows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch live Google Sheet data: {str(e)}")


class ExportRequest(BaseModel):
    candidates: List[Dict[str, Any]]


@app.post("/api/export")
def export_excel(req: ExportRequest):
    """Export candidate evaluations or spreadsheet rows to a downloadable Excel (.xlsx) file."""
    try:
        from io import BytesIO
        from fastapi.responses import StreamingResponse
        import pandas as pd

        if not req.candidates:
            raise HTTPException(status_code=400, detail="No candidate data provided for export.")

        df = pd.DataFrame(req.candidates)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Candidate Evaluations")
        output.seek(0)

        headers = {
            "Content-Disposition": "attachment; filename=Candidate_Rankings.xlsx",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel export: {str(e)}")


@app.put("/api/candidates/{candidate_id}")
def update_candidate(candidate_id: int, req: UpdateCandidateRequest):
    """Update candidate grid fields (position, hiring_stage, remarks) in SQLite & Google Sheet."""
    try:
        success = update_candidate_grid_fields(
            candidate_id,
            position=req.position,
            hiring_stage=req.hiring_stage,
            remarks=req.remarks
        )
        if not success:
            raise HTTPException(status_code=404, detail="Candidate not found or no changes made.")

        # Update Google Sheet cell in background/realtime
        cand_list = get_all_candidates()
        target = next((c for c in cand_list if c["id"] == candidate_id), None)
        if target:
            update_gsheet_row_by_filename(
                target["file_name"],
                position=req.position,
                hiring_stage=req.hiring_stage,
                remarks=req.remarks
            )

        return {"status": "success", "message": "Candidate updated in DB & Google Sheet"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update candidate: {str(e)}")


@app.delete("/api/candidates")
def clear_all_candidates():
    """Clear all local candidate evaluation records from SQLite database cache. Does NOT touch Google Sheets."""
    try:
        clear_all_evaluations()
        return {"status": "success", "message": "Cleared local candidate evaluation records."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear candidate records: {str(e)}")


@app.delete("/api/candidates/{candidate_id}")
def delete_candidate(candidate_id: int):
    """Delete a candidate record from SQLite database."""
    try:
        success = delete_candidate_record(candidate_id)
        if not success:
            raise HTTPException(status_code=404, detail="Candidate not found.")

        # Re-sync Google Sheet after deletion
        sync_candidates_to_gsheet(get_all_candidates())
        return {"status": "success", "message": "Candidate deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete candidate: {str(e)}")


from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))


def _process_local_resume_worker(file_name: str, file_bytes: bytes, final_jd_text: str):
    """Worker function to process text extraction & score evaluation for a local resume file."""
    try:
        file_obj = io.BytesIO(file_bytes)
        file_obj.name = file_name
        resume_text = extract_text_from_file(file_obj)
        scores = compute_scores(resume_text, final_jd_text)
        return (file_name, scores["overall"], scores, "")
    except Exception as err:
        print(f"Error parsing resume {file_name}: {err}")
        return None


def _process_gdrive_resume_worker(f_info: dict, final_jd_text: str):
    """Worker function to process download, text extraction & score evaluation for a GDrive resume file."""
    try:
        from gdrive_integration import download_file_bytes
        file_obj = download_file_bytes(f_info["id"], f_info["name"])
        resume_link = f_info.get("web_view_link") or getattr(file_obj, "web_view_link", "") or f"https://drive.google.com/file/d/{f_info['id']}/view"
        resume_text = extract_text_from_file(file_obj)
        scores = compute_scores(resume_text, final_jd_text)
        return (f_info["name"], scores["overall"], scores, resume_link)
    except Exception as err:
        print(f"Error parsing GDrive resume {f_info.get('name')}: {err}")
        return None


@app.post("/api/rank")
async def rank_resumes(
    resumes: List[UploadFile] = File(default=[]),
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    target_position: Optional[str] = Form(None),
    gdrive_files_json: Optional[str] = Form(None),
):
    try:
        final_jd_text = ""
        if jd_file:
            final_jd_text = extract_text_from_file(jd_file.file)
        elif jd_text:
            final_jd_text = jd_text.strip()

        if not final_jd_text:
            raise HTTPException(status_code=400, detail="Job Description text or file is required.")

        all_scores = []
        tasks = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            if resumes:
                for file in resumes:
                    if not file.filename:
                        continue
                    content = await file.read()
                    tasks.append(
                        executor.submit(_process_local_resume_worker, file.filename, content, final_jd_text)
                    )

            if gdrive_files_json:
                try:
                    gdrive_list = json.loads(gdrive_files_json)
                    for f in gdrive_list:
                        tasks.append(
                            executor.submit(_process_gdrive_resume_worker, f, final_jd_text)
                        )
                except Exception as gerr:
                    print(f"Error parsing Google Drive JSON payload: {gerr}")

            for future in as_completed(tasks):
                res = future.result()
                if res:
                    all_scores.append(res)

        if not all_scores:
            raise HTTPException(status_code=400, detail="At least one candidate resume file or Google Drive file must be selected.")

        ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)

        results = []
        for rank, item in enumerate(ranked, 1):
            res_obj = {
                "rank": rank,
                "file_name": item[0],
                "overall_score": item[1],
                "scores": item[2],
                "resume_link": item[3] if len(item) > 3 else ""
            }
            if target_position and target_position.strip() and target_position.strip() != "Select Position...":
                res_obj["position"] = target_position.strip()

            try:
                db_id = save_candidate_evaluation(res_obj)
                res_obj["id"] = db_id
            except Exception as db_err:
                print(f"Database save error: {db_err}")

            results.append(res_obj)

        # Sync all candidates to Google Sheet
        try:
            sync_candidates_to_gsheet(get_all_candidates())
        except Exception as sheet_err:
            print(f"Google Sheet sync error: {sheet_err}")

        return {"status": "success", "total": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")


@app.post("/api/export")
async def export_excel(req: ExportRequest):
    try:
        if not req.candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for export.")

        ranked_tuples = []
        for c in req.candidates:
            file_name = c.get("file_name", "candidate.pdf")
            overall = c.get("overall_score", 0.0)
            scores = c.get("scores", {})

            if "resume_data" not in scores:
                scores["resume_data"] = {}
            if c.get("position"):
                scores["resume_data"]["job_title"] = c["position"]
            if c.get("hiring_stage"):
                scores["hiring_stage"] = c["hiring_stage"]
            if c.get("remarks"):
                scores["remarks"] = c["remarks"]

            ranked_tuples.append((file_name, overall, scores))

        df = create_ranking_dataframe(ranked_tuples)

        for idx, c in enumerate(req.candidates):
            if idx < len(df):
                if c.get("position"):
                    df.at[idx, "Position"] = c["position"]
                if c.get("hiring_stage"):
                    df.at[idx, "Hiring Stage"] = c["hiring_stage"]
                if c.get("remarks"):
                    df.at[idx, "Remarks"] = c["remarks"]

        file_bytes, mime_type, ext = generate_download_file(df)

        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=candidate_rankings.{ext}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/api/gdrive/list")
async def gdrive_list(folder_id: str):
    try:
        from gdrive_integration import list_files_in_folder
        files = list_files_in_folder(folder_id)
        return {"status": "success", "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive Error: {str(e)}")


@app.post("/api/gdrive/rank")
async def gdrive_rank(req: GDriveRankRequest):
    try:
        if not req.selected_files:
            raise HTTPException(status_code=400, detail="No Google Drive files selected.")
        if not req.jd_text:
            raise HTTPException(status_code=400, detail="Job Description text is required.")

        all_scores = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(_process_gdrive_resume_worker, f, req.jd_text)
                for f in req.selected_files
            ]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    all_scores.append(res)

        ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)
        results = []
        for rank, item in enumerate(ranked, 1):
            res_obj = {
                "rank": rank,
                "file_name": item[0],
                "overall_score": item[1],
                "scores": item[2],
                "resume_link": item[3]
            }
            if req.target_position and req.target_position.strip() and req.target_position.strip() != "Select Position...":
                res_obj["position"] = req.target_position.strip()

            try:
                db_id = save_candidate_evaluation(res_obj)
                res_obj["id"] = db_id
            except Exception as db_err:
                print(f"Database save error: {db_err}")

            results.append(res_obj)

        # Sync all candidates to Google Sheet
        try:
            sync_candidates_to_gsheet(get_all_candidates())
        except Exception as sheet_err:
            print(f"Google Sheet sync error: {sheet_err}")

        return {"status": "success", "total": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive Ranking failed: {str(e)}")

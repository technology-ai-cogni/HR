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

app = FastAPI(title="Resume Analyser API", version="1.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExportRequest(BaseModel):
    candidates: List[dict]


class GDriveRankRequest(BaseModel):
    folder_id: str
    selected_files: List[dict]
    jd_text: str


@app.get("/")
def read_root():
    return {"status": "online", "message": "Resume Analyser FastAPI Backend Running"}


@app.get("/api/positions")
def get_positions():
    return {"positions": POSITIONS}


@app.post("/api/rank")
async def rank_resumes(
    resumes: List[UploadFile] = File(...),
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
):
    try:
        # Determine JD Text
        final_jd_text = ""
        if jd_file:
            final_jd_text = extract_text_from_file(jd_file.file)
        elif jd_text:
            final_jd_text = jd_text.strip()

        if not final_jd_text:
            raise HTTPException(status_code=400, detail="Job Description text or file is required.")

        if not resumes:
            raise HTTPException(status_code=400, detail="At least one resume file must be uploaded.")

        all_scores = []
        for file in resumes:
            # Wrap content in a NamedBytesIO so filename extension is available
            content = await file.read()
            file_obj = io.BytesIO(content)
            file_obj.name = file.filename

            resume_text = extract_text_from_file(file_obj)
            scores = compute_scores(resume_text, final_jd_text)
            all_scores.append((file.filename, scores["overall"], scores))

        ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)

        results = []
        for rank, item in enumerate(ranked, 1):
            results.append({
                "rank": rank,
                "file_name": item[0],
                "overall_score": item[1],
                "scores": item[2]
            })

        return {"status": "success", "total": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")


@app.post("/api/export")
async def export_excel(req: ExportRequest):
    try:
        if not req.candidates:
            raise HTTPException(status_code=400, detail="No candidates provided for export.")

        # Reconstruct ranked_results tuple list for create_ranking_dataframe
        ranked_tuples = []
        for c in req.candidates:
            file_name = c.get("file_name", "candidate.pdf")
            overall = c.get("overall_score", 0.0)
            scores = c.get("scores", {})

            # Overwrite position / hiring stage / remarks if user edited them in Next.js grid
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

        # Apply user edited fields directly into DataFrame if passed
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
        from gdrive_integration import download_file_bytes

        if not req.selected_files:
            raise HTTPException(status_code=400, detail="No Google Drive files selected.")
        if not req.jd_text:
            raise HTTPException(status_code=400, detail="Job Description text is required.")

        all_scores = []
        for f in req.selected_files:
            file_obj = download_file_bytes(f["id"], f["name"])
            resume_text = extract_text_from_file(file_obj)
            scores = compute_scores(resume_text, req.jd_text)
            all_scores.append((f["name"], scores["overall"], scores))

        ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)
        results = []
        for rank, item in enumerate(ranked, 1):
            results.append({
                "rank": rank,
                "file_name": item[0],
                "overall_score": item[1],
                "scores": item[2]
            })

        return {"status": "success", "total": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive Ranking failed: {str(e)}")

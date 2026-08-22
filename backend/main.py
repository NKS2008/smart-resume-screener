"""
main.py
Entry point for the Smart Resume Screener API.

Run with:
    uvicorn backend.main:app --reload

Endpoints:
    POST /resumes/upload        -> upload + parse a resume, store it
    POST /jobs                  -> create a job description
    POST /match                 -> run LLM match for one candidate + job
    GET  /shortlist/{job_id}    -> get all candidates for a job, ranked by score
    GET  /candidates            -> list all uploaded candidates
"""

import os
import shutil
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import get_connection, init_db
from resume_parser import parse_resume
from llm_matcher import match_resume
from backend.models import JobDescriptionIn, MatchRequest

app = FastAPI(title="Smart Resume Screener")

# allow the frontend (served separately / opened as a static file) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


@app.get("/")
def root():
    return {"message": "Smart Resume Screener API is running"}


@app.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT resumes are supported")

    # save to a temp file so pdfplumber can read it
    suffix = ".pdf" if file.filename.endswith(".pdf") else ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        parsed = parse_resume(tmp_path)
    finally:
        os.remove(tmp_path)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO candidates (filename, name, email, phone, skills, experience, education, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file.filename,
            parsed["name"],
            parsed["email"],
            parsed["phone"],
            ", ".join(parsed["skills"]),
            parsed["experience"],
            parsed["education"],
            parsed["raw_text"],
        ),
    )
    conn.commit()
    candidate_id = cur.lastrowid
    conn.close()

    return {
        "candidate_id": candidate_id,
        "name": parsed["name"],
        "email": parsed["email"],
        "phone": parsed["phone"],
        "skills": parsed["skills"],
        "experience": parsed["experience"],
        "education": parsed["education"],
    }


@app.post("/jobs")
def create_job(job: JobDescriptionIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO job_descriptions (title, description) VALUES (?, ?)",
        (job.title, job.description),
    )
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return {"job_id": job_id, "title": job.title}


@app.post("/match")
def run_match(req: MatchRequest):
    conn = get_connection()
    cur = conn.cursor()

    candidate = cur.execute(
        "SELECT * FROM candidates WHERE id = ?", (req.candidate_id,)
    ).fetchone()
    job = cur.execute(
        "SELECT * FROM job_descriptions WHERE id = ?", (req.job_id,)
    ).fetchone()

    if not candidate or not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    result = get_match_score(candidate["raw_text"], job["description"])

    cur.execute(
        """
        INSERT INTO matches (candidate_id, job_id, score, justification)
        VALUES (?, ?, ?, ?)
        """,
        (req.candidate_id, req.job_id, result["score"], result["justification"]),
    )
    conn.commit()
    conn.close()

    return {
        "candidate_id": req.candidate_id,
        "job_id": req.job_id,
        "score": result["score"],
        "justification": result["justification"],
    }


@app.get("/shortlist/{job_id}")
def get_shortlist(job_id: int):
    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT c.id as candidate_id, c.name, c.email, c.skills,
               m.score, m.justification
        FROM matches m
        JOIN candidates c ON c.id = m.candidate_id
        WHERE m.job_id = ?
        ORDER BY m.score DESC
        """,
        (job_id,),
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/candidates")
def list_candidates():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, name, email, phone, skills FROM candidates ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# serve the frontend as static files so the whole thing can run from one server
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")

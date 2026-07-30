# Cognitute HR - Resume Analyser & Candidate Ranking System

A modern AI-powered candidate screening and resume evaluation platform with a **Next.js 14** web application frontend and a Python **FastAPI** backend server.

---

## 📁 Repository Structure

```
Resume_analyser/
├── backend/                  # Python FastAPI Backend Server & LLM Engine
│   ├── server.py             # FastAPI REST Endpoints (/api/rank, /api/export, /api/gdrive)
│   ├── matching_engine.py    # Scoring & candidate evaluation logic
│   ├── llm_integration.py    # Groq LLM API prompts & contact info extraction
│   ├── extraction.py         # PDF & DOCX text extraction parser
│   ├── gdrive_integration.py # Google Drive folder integration
│   ├── .env                  # Environment config & Groq API keys
│   └── requirements.txt      # Python dependencies
│
└── frontend/                 # Next.js 14 Web Application Frontend
    ├── src/
    │   ├── app/              # Next.js App Router layout & page components
    │   └── components/       # Sidebar, Navbar, CandidateGrid, CandidateCard
    ├── public/               # Static assets
    └── package.json          # Node.js dependencies
```

---

## 🚀 Quick Start Guide

### 1. Launch FastAPI Backend (Terminal 1)
```bash
cd backend
python3 -m uvicorn server:app --reload --port 8000
```
*Backend runs on `http://localhost:8000`*

### 2. Launch Next.js Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
*Frontend runs on `http://localhost:3000`*

---

## ✨ Features

- **⚡ Batch Resume Ranking**: Upload multiple PDF/DOCX resumes (via file picker or drag & drop) and rank them against a target Job Description.
- **📄 Single Candidate Match**: Quick 1-on-1 resume evaluation.
- **☁️ Google Drive Sync**: Fetch candidate resumes directly from a Google Drive Folder ID.
- **📊 Interactive Candidate Grid**: Assign candidate Position (25 roles dropdown), edit Hiring Stage & Remarks.
- **📥 Excel Export**: Export live candidate grid evaluation data to `.xlsx`.

"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import CandidateGrid from "@/components/CandidateGrid";
import CandidateCard from "@/components/CandidateCard";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const POSITIONS = [
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
];

export default function Home() {
  const [activeTab, setActiveTab] = useState("batch");
  const [backendOnline, setBackendOnline] = useState(false);
  const [loading, setLoading] = useState(false);

  // Initialize results state from localStorage cache so data NEVER vanishes on page refresh
  const [results, setResults] = useState(() => {
    if (typeof window !== "undefined") {
      const cached = localStorage.getItem("cognitute_candidate_results");
      if (cached) {
        try {
          return JSON.parse(cached);
        } catch {}
      }
    }
    return [];
  });

  const [error, setError] = useState("");

  // Target Position for all uploaded resumes
  const [targetPosition, setTargetPosition] = useState("");

  // Batch Form State
  const [batchResumes, setBatchResumes] = useState([]);
  const [batchJdText, setBatchJdText] = useState("");
  const [batchJdFile, setBatchJdFile] = useState(null);
  const [batchJdMode, setBatchJdMode] = useState("text");

  // GDrive Form State
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveFiles, setGdriveFiles] = useState([]);
  const [selectedGdriveFiles, setSelectedGdriveFiles] = useState([]);
  const [gdriveJdText, setGdriveJdText] = useState("");
  const [fetchingGdrive, setFetchingGdrive] = useState(false);

  // Dynamic Live Sheet State
  const [worksheetsList, setWorksheetsList] = useState([]);
  const [selectedWorksheet, setSelectedWorksheet] = useState("Sheet1");
  const [liveSheetHeaders, setLiveSheetHeaders] = useState([]);
  const [liveSheetRows, setLiveSheetRows] = useState([]);
  const [liveSheetUrl, setLiveSheetUrl] = useState("");
  const [fetchingLiveSheet, setFetchingLiveSheet] = useState(false);

  // Helper to fetch master candidate list from SQLite database & sync with localStorage
  const fetchAllCandidates = async () => {
    try {
      const candRes = await fetch(`${BACKEND_URL}/api/candidates`);
      if (candRes.ok) {
        const data = await candRes.json();
        if (data.candidates && data.candidates.length > 0) {
          setResults(data.candidates);
          if (typeof window !== "undefined") {
            localStorage.setItem("cognitute_candidate_results", JSON.stringify(data.candidates));
          }
        }
      }
    } catch (err) {
      console.error("Failed to fetch candidates from backend:", err);
    }
  };

  // Fetch available worksheet tabs in the Google Spreadsheet
  const fetchWorksheetsList = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/gsheet/worksheets`);
      const data = await res.json();
      if (res.ok && data.worksheets && data.worksheets.length > 0) {
        setWorksheetsList(data.worksheets);
        if (!data.worksheets.includes(selectedWorksheet)) {
          if (data.worksheets.includes("Sheet1")) {
            setSelectedWorksheet("Sheet1");
          } else {
            setSelectedWorksheet(data.worksheets[0]);
          }
        }
      }
    } catch (err) {
      console.error("Failed to fetch worksheets list:", err);
    }
  };

  // Helper to fetch raw live headers & rows directly from Google Sheets API for selected worksheet
  const fetchLiveSheetData = async (targetWs) => {
    const wsToFetch = targetWs || selectedWorksheet;
    setFetchingLiveSheet(true);
    try {
      const url = `${BACKEND_URL}/api/gsheet/live${wsToFetch ? `?worksheet=${encodeURIComponent(wsToFetch)}` : ""}`;
      const res = await fetch(url);
      const data = await res.json();
      if (res.ok) {
        setLiveSheetHeaders(data.headers || []);
        setLiveSheetRows(data.rows || []);
        setLiveSheetUrl(data.sheet_url || "");
        if (data.active_worksheet) {
          setSelectedWorksheet(data.active_worksheet);
        }
      }
    } catch (err) {
      console.error("Failed to fetch live sheet data:", err);
    } finally {
      setFetchingLiveSheet(false);
    }
  };

  // Sync results to localStorage whenever updated
  useEffect(() => {
    if (results.length > 0 && typeof window !== "undefined") {
      localStorage.setItem("cognitute_candidate_results", JSON.stringify(results));
    }
  }, [results]);

  // Fetch live sheet data when user opens Live Sheet Data tab
  useEffect(() => {
    if (activeTab === "live") {
      fetchWorksheetsList();
      fetchLiveSheetData(selectedWorksheet);
    }
  }, [activeTab]);

  // Check Backend Health & Load Saved Candidates on mount
  useEffect(() => {
    async function checkHealthAndLoadCandidates() {
      try {
        const res = await fetch(`${BACKEND_URL}/`);
        if (res.ok) {
          setBackendOnline(true);
          await fetchAllCandidates();
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    }
    checkHealthAndLoadCandidates();
  }, []);

  // Multi-File Selection Handler (Appends new files, avoids overwriting)
  const handleBatchFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setBatchResumes((prev) => {
        const combined = [...prev];
        for (const file of newFiles) {
          if (!combined.some((f) => f.name === file.name && f.size === file.size)) {
            combined.push(file);
          }
        }
        return combined;
      });
      e.target.value = "";
    }
  };

  // Drag & Drop Handler for Multiple Files
  const handleBatchDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files).filter(
        (f) => f.name.toLowerCase().endsWith(".pdf") || f.name.toLowerCase().endsWith(".docx")
      );
      if (droppedFiles.length > 0) {
        setBatchResumes((prev) => {
          const combined = [...prev];
          for (const file of droppedFiles) {
            if (!combined.some((f) => f.name === file.name && f.size === file.size)) {
              combined.push(file);
            }
          }
          return combined;
        });
      }
    }
  };

  const removeBatchFile = (indexToRemove) => {
    setBatchResumes((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  // Handle Batch Submit
  const handleBatchSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (batchResumes.length === 0) {
      setError("Please select at least one candidate resume file.");
      return;
    }
    if (batchJdMode === "text" && !batchJdText.trim()) {
      setError("Please enter Job Description text.");
      return;
    }
    if (batchJdMode === "file" && !batchJdFile) {
      setError("Please upload a Job Description file.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      for (const file of batchResumes) {
        formData.append("resumes", file);
      }

      if (batchJdMode === "file" && batchJdFile) {
        formData.append("jd_file", batchJdFile);
      } else {
        formData.append("jd_text", batchJdText);
      }

      if (targetPosition.trim()) {
        formData.append("target_position", targetPosition.trim());
      }

      const res = await fetch(`${BACKEND_URL}/api/rank`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to process resumes.");

      await fetchAllCandidates();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch GDrive Files
  const handleFetchGDrive = async () => {
    if (!gdriveFolderId.trim()) {
      setError("Please enter a Google Drive Folder ID.");
      return;
    }

    setFetchingGdrive(true);
    setError("");
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/gdrive/list?folder_id=${encodeURIComponent(gdriveFolderId.trim())}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to fetch files from Google Drive.");

      setGdriveFiles(data.files || []);
      setSelectedGdriveFiles((data.files || []).map((f) => f.id));
    } catch (err) {
      setError(err.message);
    } finally {
      setFetchingGdrive(false);
    }
  };

  // Rank GDrive Resumes
  const handleGDriveRankSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (selectedGdriveFiles.length === 0) {
      setError("Please select at least one Google Drive resume.");
      return;
    }
    if (!gdriveJdText.trim()) {
      setError("Please enter Job Description text.");
      return;
    }

    setLoading(true);

    try {
      const selectedObjList = gdriveFiles.filter((f) => selectedGdriveFiles.includes(f.id));
      const res = await fetch(`${BACKEND_URL}/api/gdrive/rank`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          folder_id: gdriveFolderId,
          selected_files: selectedObjList,
          jd_text: gdriveJdText,
          target_position: targetPosition.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Google Drive ranking failed.");

      await fetchAllCandidates();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getTabHeader = () => {
    if (activeTab === "batch") {
      return {
        title: "Batch Resume Ranking",
        description: "Upload multiple candidate resumes and rank them against your Job Description.",
      };
    } else if (activeTab === "gdrive") {
      return {
        title: "Google Drive Folder Import",
        description: "Fetch candidate resumes directly from a Google Drive Folder ID.",
      };
    } else {
      return {
        title: "Live Google Sheet View",
        description: "Real-time dynamic synchronization view of your connected Google Sheet.",
      };
    }
  };

  const header = getTabHeader();

  return (
    <div className="app-container">
      {/* Side Column with Features and Logo */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setError("");
        }}
        backendOnline={backendOnline}
      />

      {/* Main Content Area */}
      <main className="main-content">
        <Navbar title={header.title} description={header.description} />

        {error && (
          <div
            className="glass-panel"
            style={{
              borderLeft: "4px solid #dc2626",
              background: "#fef2f2",
              color: "#b91c1c",
              padding: "14px 20px",
              marginBottom: "20px",
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* TAB 1: BATCH RANKING */}
        {activeTab === "batch" && (
          <div className="glass-panel">
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              Batch Processing
            </h3>
            <p style={{ fontSize: "0.88rem", color: "#64748b", marginBottom: "24px" }}>
              Upload resumes in PDF or DOCX format to parse and rank candidate qualifications.
            </p>

            <form onSubmit={handleBatchSubmit}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px", alignItems: "start" }}>
                {/* Left Column: Job Description */}
                <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", minHeight: "36px", marginBottom: "10px" }}>
                    <label style={{ fontWeight: 700, color: "#334155", fontSize: "0.9rem" }}>
                      1. Job Description
                    </label>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button
                        type="button"
                        style={{
                          padding: "5px 12px",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          background: batchJdMode === "text" ? "#2563eb" : "#f1f5f9",
                          color: batchJdMode === "text" ? "#fff" : "#334155",
                          fontSize: "0.82rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                        onClick={() => setBatchJdMode("text")}
                      >
                        Paste Text
                      </button>
                      <button
                        type="button"
                        style={{
                          padding: "5px 12px",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          background: batchJdMode === "file" ? "#2563eb" : "#f1f5f9",
                          color: batchJdMode === "file" ? "#fff" : "#334155",
                          fontSize: "0.82rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                        onClick={() => setBatchJdMode("file")}
                      >
                        Upload File
                      </button>
                    </div>
                  </div>

                  {batchJdMode === "text" ? (
                    <textarea
                      className="form-textarea"
                      style={{ flex: 1, minHeight: "220px", margin: 0 }}
                      rows={9}
                      placeholder="Paste job description requirements..."
                      value={batchJdText}
                      onChange={(e) => setBatchJdText(e.target.value)}
                    />
                  ) : (
                    <input
                      type="file"
                      className="form-input"
                      style={{ minHeight: "220px" }}
                      accept=".pdf,.docx"
                      onChange={(e) => setBatchJdFile(e.target.files[0])}
                    />
                  )}
                </div>

                {/* Right Column: Candidate Resumes with Position Field */}
                <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", minHeight: "36px", marginBottom: "10px" }}>
                    <label style={{ fontWeight: 700, color: "#334155", fontSize: "0.9rem" }}>
                      2. Candidate Resumes ({batchResumes.length} selected)
                    </label>
                    {batchResumes.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setBatchResumes([])}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#dc2626",
                          fontSize: "0.8rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        Clear All
                      </button>
                    )}
                  </div>

                  {/* Position Input Field above Dropzone */}
                  <div style={{ marginBottom: "12px" }}>
                    <input
                      type="text"
                      list="batch-positions-list"
                      className="form-input"
                      placeholder="Type or select Position name for all candidates (e.g. AI Engineer, SEO Intern)..."
                      value={targetPosition}
                      onChange={(e) => setTargetPosition(e.target.value)}
                      style={{ fontSize: "0.85rem", padding: "8px 12px", width: "100%" }}
                    />
                    <datalist id="batch-positions-list">
                      {POSITIONS.map((pos, idx) => (
                        <option key={idx} value={pos} />
                      ))}
                    </datalist>
                  </div>

                  {/* Dropzone with Drag & Drop */}
                  <div
                    className="dropzone"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleBatchDrop}
                    style={{
                      flex: 1,
                      minHeight: "160px",
                      display: "flex",
                      flexDirection: "column",
                      justify: "center",
                      alignItems: "center",
                      margin: 0
                    }}
                  >
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.docx"
                      style={{ display: "none" }}
                      id="batch-file-input"
                      onChange={handleBatchFileSelect}
                    />
                    <label htmlFor="batch-file-input" style={{ cursor: "pointer", width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
                      <div style={{ fontWeight: 700, color: "#059669", fontSize: "1.05rem" }}>
                        Click to Choose or Drag & Drop Resumes
                      </div>
                      <div style={{ fontSize: "0.82rem", color: "#64748b", marginTop: "4px" }}>
                        Select multiple PDF or DOCX files at once (or add more)
                      </div>
                    </label>
                  </div>

                  {/* Selected Resumes Badges */}
                  {batchResumes.length > 0 && (
                    <div style={{ marginTop: "12px", maxHeight: "120px", overflowY: "auto", display: "flex", flexWrap: "wrap", gap: "6px", padding: "6px", background: "#ffffff", borderRadius: "8px", border: "1px solid #d1fae5" }}>
                      {batchResumes.map((f, idx) => (
                        <span
                          key={idx}
                          className="badge badge-blue"
                          style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "4px 10px" }}
                        >
                          {f.name}
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              removeBatchFile(idx);
                            }}
                            style={{
                              cursor: "pointer",
                              fontWeight: 800,
                              marginLeft: "4px",
                              color: "#ef4444",
                              fontSize: "0.85rem",
                            }}
                            title="Remove file"
                          >
                            ✕
                          </span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <button type="submit" className="btn-primary" style={{ width: "100%" }} disabled={loading}>
                {loading ? "Evaluating Candidate Resumes..." : "Rank & Analyze Candidates"}
              </button>
            </form>
          </div>
        )}

        {/* TAB 2: GDRIVE IMPORT */}
        {activeTab === "gdrive" && (
          <div className="glass-panel">
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              Google Drive Folder Sync
            </h3>
            <p style={{ fontSize: "0.88rem", color: "#64748b", marginBottom: "24px" }}>
              Sync candidate resumes directly from a Google Drive Folder ID.
            </p>

            <div style={{ display: "flex", gap: "12px", marginBottom: "24px" }}>
              <input
                type="text"
                className="form-input"
                placeholder="Paste Google Drive Folder ID..."
                value={gdriveFolderId}
                onChange={(e) => setGdriveFolderId(e.target.value)}
              />
              <button
                type="button"
                className="btn-primary"
                onClick={handleFetchGDrive}
                disabled={fetchingGdrive}
                style={{ whiteSpace: "nowrap" }}
              >
                {fetchingGdrive ? "Fetching..." : "Fetch Files"}
              </button>
            </div>

            {gdriveFiles.length > 0 && (
              <form onSubmit={handleGDriveRankSubmit}>
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ display: "block", fontWeight: 600, color: "#475569", fontSize: "0.85rem", marginBottom: "4px" }}>
                    Target Position Title
                  </label>
                  <input
                    type="text"
                    list="gdrive-positions-list"
                    className="form-input"
                    placeholder="Type or select Position name for all Google Drive resumes..."
                    value={targetPosition}
                    onChange={(e) => setTargetPosition(e.target.value)}
                  />
                  <datalist id="gdrive-positions-list">
                    {POSITIONS.map((pos, idx) => (
                      <option key={idx} value={pos} />
                    ))}
                  </datalist>
                </div>

                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontWeight: 700, marginBottom: "8px", color: "#334155", fontSize: "0.9rem" }}>
                    Select Files ({selectedGdriveFiles.length}/{gdriveFiles.length} selected)
                  </label>
                  <div
                    style={{
                      maxHeight: "180px",
                      overflowY: "auto",
                      background: "#f8fafc",
                      padding: "12px",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    {gdriveFiles.map((file) => (
                      <label
                        key={file.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          padding: "4px 0",
                          cursor: "pointer",
                          color: "#334155",
                          fontSize: "0.9rem",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={selectedGdriveFiles.includes(file.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedGdriveFiles([...selectedGdriveFiles, file.id]);
                            } else {
                              setSelectedGdriveFiles(selectedGdriveFiles.filter((id) => id !== file.id));
                            }
                          }}
                        />
                        <span>{file.name}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div style={{ marginBottom: "24px" }}>
                  <label style={{ display: "block", fontWeight: 700, marginBottom: "8px", color: "#334155", fontSize: "0.9rem" }}>
                    Job Description Text
                  </label>
                  <textarea
                    className="form-textarea"
                    rows={5}
                    placeholder="Paste Job Description..."
                    value={gdriveJdText}
                    onChange={(e) => setGdriveJdText(e.target.value)}
                  />
                </div>

                <button type="submit" className="btn-primary" style={{ width: "100%" }} disabled={loading}>
                  {loading ? "Ranking Google Drive Resumes..." : "Rank Selected Google Drive Resumes"}
                </button>
              </form>
            )}
          </div>
        )}

        {/* TAB 3: DYNAMIC LIVE SHEET DATA WITH WORKSHEET SELECTOR */}
        {activeTab === "live" && (
          <div className="glass-panel">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <div>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
                  Live Google Sheet Data
                </h3>
                <p style={{ fontSize: "0.88rem", color: "#64748b" }}>
                  Showing all {liveSheetHeaders.length} live columns from sheet tab (<span style={{ fontFamily: "monospace", fontWeight: 700, color: "#2563eb" }}>{selectedWorksheet}</span>).
                </p>
              </div>

              <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                {/* Worksheet Tab Selector Dropdown */}
                {worksheetsList.length > 0 && (
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <label style={{ fontSize: "0.85rem", fontWeight: 700, color: "#475569" }}>
                      Sheet Tab:
                    </label>
                    <select
                      className="form-input"
                      value={selectedWorksheet}
                      onChange={(e) => {
                        const newWs = e.target.value;
                        setSelectedWorksheet(newWs);
                        fetchLiveSheetData(newWs);
                      }}
                      style={{ fontSize: "0.85rem", padding: "6px 12px", cursor: "pointer", fontWeight: 600 }}
                    >
                      {worksheetsList.map((ws, idx) => (
                        <option key={idx} value={ws}>
                          {ws}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {liveSheetUrl && (
                  <a
                    href={liveSheetUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary"
                    style={{ fontSize: "0.85rem", padding: "8px 16px", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px" }}
                  >
                    Open Google Sheet ↗
                  </a>
                )}
                <button
                  type="button"
                  className="btn-success"
                  onClick={() => fetchLiveSheetData(selectedWorksheet)}
                  disabled={fetchingLiveSheet}
                  style={{ fontSize: "0.85rem", padding: "8px 16px" }}
                >
                  {fetchingLiveSheet ? "Refreshing..." : "Refresh Live Data"}
                </button>
              </div>
            </div>

            {liveSheetHeaders.length > 0 ? (
              <div style={{ overflowX: "auto", borderRadius: "10px", border: "1px solid #cbd5e1" }}>
                <table className="custom-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                  <thead>
                    <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0" }}>
                      {liveSheetHeaders.map((header, idx) => (
                        <th
                          key={idx}
                          style={{
                            padding: "12px 14px",
                            textAlign: "left",
                            fontWeight: 700,
                            color: "#334155",
                            whiteSpace: "nowrap",
                            borderRight: "1px solid #f1f5f9"
                          }}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {liveSheetRows.length > 0 ? (
                      liveSheetRows.map((row, rIdx) => (
                        <tr
                          key={rIdx}
                          style={{
                            borderBottom: "1px solid #e2e8f0",
                            background: rIdx % 2 === 0 ? "#ffffff" : "#f8fafc",
                          }}
                        >
                          {liveSheetHeaders.map((_, cIdx) => {
                            const val = row[cIdx] !== undefined ? String(row[cIdx]).trim() : "";
                            const isUrl = val.startsWith("http://") || val.startsWith("https://");
                            return (
                              <td
                                key={cIdx}
                                style={{
                                  padding: "10px 14px",
                                  color: "#1e293b",
                                  whiteSpace: "nowrap",
                                  borderRight: "1px solid #f1f5f9"
                                }}
                              >
                                {isUrl ? (
                                  <a
                                    href={val}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{
                                      color: "#2563eb",
                                      fontWeight: 600,
                                      textDecoration: "none",
                                      display: "inline-flex",
                                      alignItems: "center",
                                      gap: "4px"
                                    }}
                                  >
                                    View Link ↗
                                  </a>
                                ) : (
                                  val || "-"
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={liveSheetHeaders.length}
                          style={{ padding: "32px", textAlign: "center", color: "#64748b" }}
                        >
                          No data rows present in tab '{selectedWorksheet}'.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ padding: "32px", textAlign: "center", color: "#64748b" }}>
                {fetchingLiveSheet ? `Fetching live data for '${selectedWorksheet}'...` : `No headers found in worksheet '${selectedWorksheet}'.`}
              </div>
            )}
          </div>
        )}

        {/* RESULTS SECTION FOR BATCH & GDRIVE TABS */}
        {activeTab !== "live" && results.length > 0 && (
          <>
            <CandidateGrid candidates={results} />

            <div style={{ marginTop: "32px" }}>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", marginBottom: "16px" }}>
                Detailed Candidate Breakdowns
              </h3>
              {results.map((cand, idx) => (
                <CandidateCard key={idx} candidate={cand} />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

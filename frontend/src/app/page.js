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

  const [results, setResults] = useState([]);
  const [mounted, setMounted] = useState(false);

  // Load localStorage after initial client hydration to prevent SSR mismatch
  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      const cached = localStorage.getItem("cognitute_candidate_results");
      if (cached) {
        try {
          setResults(JSON.parse(cached));
        } catch {}
      }
    }
  }, []);

  const [error, setError] = useState("");

  // Target Position for all uploaded resumes
  const [targetPosition, setTargetPosition] = useState("");

  // Batch Form State
  const [batchResumeSource, setBatchResumeSource] = useState("local");
  const [batchResumes, setBatchResumes] = useState([]);
  const [batchJdText, setBatchJdText] = useState("");
  const [batchJdFile, setBatchJdFile] = useState(null);
  const [batchJdMode, setBatchJdMode] = useState("text");

  // GDrive Form State
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveFiles, setGdriveFiles] = useState([]);
  const [selectedGdriveFiles, setSelectedGdriveFiles] = useState([]);
  const [folderStack, setFolderStack] = useState([]);
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

  // Export Live Sheet Data to Excel
  const handleExportLiveSheetExcel = async () => {
    if (!liveSheetHeaders || liveSheetHeaders.length === 0 || !liveSheetRows || liveSheetRows.length === 0) {
      alert("No data available to export.");
      return;
    }

    try {
      const candidatesData = liveSheetRows.map((row) => {
        const obj = {};
        liveSheetHeaders.forEach((h, idx) => {
          obj[h] = row[idx] !== undefined ? row[idx] : "";
        });
        return obj;
      });

      const res = await fetch(`${BACKEND_URL}/api/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidates: candidatesData }),
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Live_Sheet_${selectedWorksheet}_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        return;
      }
    } catch (err) {
      console.warn("Backend Excel export endpoint notice:", err);
    }

    // Client-side Fallback
    try {
      const csvRows = [liveSheetHeaders.map((h) => `"${(h || "").replace(/"/g, '""')}"`).join(",")];
      for (const row of liveSheetRows) {
        const values = liveSheetHeaders.map((_, idx) => {
          const val = row[idx] !== undefined ? String(row[idx]) : "";
          return `"${val.replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(","));
      }

      const csvContent = "\uFEFF" + csvRows.join("\n");
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Live_Sheet_${selectedWorksheet}_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (fallbackErr) {
      alert("Failed to download file: " + fallbackErr.message);
    }
  };

  const handleClearGrid = async () => {
    if (!window.confirm("Are you sure you want to clear the Candidate Evaluation Grid list?\n\n(Your Google Sheet data will remain completely safe and untouched!)")) {
      return;
    }
    try {
      await fetch(`${BACKEND_URL}/api/candidates`, { method: "DELETE" });
    } catch (err) {
      console.error("Failed to clear local SQLite candidate evaluations:", err);
    }
    setResults([]);
    if (typeof window !== "undefined") {
      localStorage.removeItem("cognitute_candidate_results");
    }
  };

  // Sync results to localStorage whenever updated
  useEffect(() => {
    if (results && results.length > 0 && typeof window !== "undefined") {
      try {
        localStorage.setItem("cognitute_candidate_results", JSON.stringify(results));
      } catch {}
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

    if (batchResumes.length === 0 && selectedGdriveFiles.length === 0) {
      setError("Please select at least one candidate resume file or Google Drive resume.");
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

      if (selectedGdriveFiles.length > 0) {
        const selectedObjList = gdriveFiles.filter((f) => selectedGdriveFiles.includes(f.id));
        formData.append("gdrive_files_json", JSON.stringify(selectedObjList));
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

  // Fetch GDrive Files (Supports Subfolders & Breadcrumbs)
  const handleFetchGDrive = async (targetFolderId, folderName) => {
    const validFolderId = (typeof targetFolderId === "string" && targetFolderId.trim()) ? targetFolderId.trim() : gdriveFolderId.trim();
    if (!validFolderId) {
      setError("Please enter a Google Drive Folder ID.");
      return;
    }
    const validFolderName = (typeof folderName === "string") ? folderName : "Root Folder";

    setFetchingGdrive(true);
    setError("");
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/gdrive/list?folder_id=${encodeURIComponent(validFolderId)}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to fetch files from Google Drive.");

      const rawFiles = data.files || [];
      setGdriveFiles(rawFiles);

      // Auto-select all resume files (excluding subfolders)
      const resumeIds = rawFiles.filter((f) => !f.is_folder).map((f) => f.id);
      setSelectedGdriveFiles(resumeIds);

      // Update folder navigation history stack
      if (typeof targetFolderId === "string" && validFolderName) {
        setFolderStack((prev) => {
          if (prev.some((f) => f.id === validFolderId)) return prev;
          return [...prev, { id: validFolderId, name: validFolderName }];
        });
      } else {
        setFolderStack([{ id: validFolderId, name: "Root Folder" }]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setFetchingGdrive(false);
    }
  };

  const navigateBackGDrive = (targetIndex) => {
    if (targetIndex < 0 || targetIndex >= folderStack.length) return;
    const targetFolder = folderStack[targetIndex];
    setFolderStack(folderStack.slice(0, targetIndex + 1));
    handleFetchGDrive(targetFolder.id, targetFolder.name);
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
                      2. Candidate Resumes ({batchResumes.length + selectedGdriveFiles.length} selected)
                    </label>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <button
                        type="button"
                        style={{
                          padding: "5px 12px",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          background: batchResumeSource === "local" ? "#2563eb" : "#f1f5f9",
                          color: batchResumeSource === "local" ? "#fff" : "#334155",
                          fontSize: "0.82rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                        onClick={() => setBatchResumeSource("local")}
                      >
                        Local Upload
                      </button>
                      <button
                        type="button"
                        style={{
                          padding: "5px 12px",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          background: batchResumeSource === "gdrive" ? "#2563eb" : "#f1f5f9",
                          color: batchResumeSource === "gdrive" ? "#fff" : "#334155",
                          fontSize: "0.82rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                        onClick={() => setBatchResumeSource("gdrive")}
                      >
                        Google Drive
                      </button>
                      {(batchResumes.length > 0 || selectedGdriveFiles.length > 0) && (
                        <button
                          type="button"
                          onClick={() => {
                            setBatchResumes([]);
                            setSelectedGdriveFiles([]);
                          }}
                          style={{
                            background: "transparent",
                            border: "none",
                            color: "#dc2626",
                            fontSize: "0.8rem",
                            fontWeight: 600,
                            cursor: "pointer",
                            marginLeft: "4px"
                          }}
                        >
                          Clear All
                        </button>
                      )}
                    </div>
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

                  {batchResumeSource === "local" ? (
                    <>
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

                      {/* Selected Local Resumes Badges */}
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
                    </>
                  ) : (
                    <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "8px", border: "1px solid #e2e8f0", flex: 1, minHeight: "160px" }}>
                      <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="Paste Google Drive Folder ID..."
                          value={gdriveFolderId}
                          onChange={(e) => setGdriveFolderId(e.target.value)}
                          style={{ fontSize: "0.85rem" }}
                        />
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={() => handleFetchGDrive()}
                          disabled={fetchingGdrive}
                          style={{ fontSize: "0.82rem", padding: "6px 14px", whiteSpace: "nowrap" }}
                        >
                          {fetchingGdrive ? "Fetching..." : "Fetch Folder"}
                        </button>
                      </div>

                      {gdriveFiles.length > 0 ? (
                        <div>
                          {/* Folder Breadcrumbs & Back Button */}
                          {folderStack.length > 1 && (
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px", background: "#eff6ff", padding: "6px 12px", borderRadius: "6px", border: "1px solid #bfdbfe" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.82rem", flexWrap: "wrap" }}>
                                <span style={{ fontWeight: 700, color: "#1e40af" }}>Folder Path:</span>
                                {folderStack.map((folder, idx) => (
                                  <span key={folder.id} style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                                    {idx > 0 && <span style={{ color: "#93c5fd" }}>/</span>}
                                    <button
                                      type="button"
                                      onClick={() => navigateBackGDrive(idx)}
                                      style={{ background: "none", border: "none", color: idx === folderStack.length - 1 ? "#1e293b" : "#2563eb", fontWeight: idx === folderStack.length - 1 ? 700 : 500, cursor: "pointer", textDecoration: idx === folderStack.length - 1 ? "none" : "underline", padding: 0 }}
                                    >
                                      📁 {folder.name}
                                    </button>
                                  </span>
                                ))}
                              </div>
                              <button
                                type="button"
                                onClick={() => navigateBackGDrive(folderStack.length - 2)}
                                style={{ background: "#2563eb", color: "#ffffff", border: "none", padding: "4px 10px", borderRadius: "6px", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: "4px", whiteSpace: "nowrap" }}
                              >
                                ⬅ Back
                              </button>
                            </div>
                          )}

                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#334155" }}>
                              Selected {selectedGdriveFiles.length} of {gdriveFiles.filter((f) => !f.is_folder).length} Resumes ({gdriveFiles.filter((f) => f.is_folder).length} Subfolders):
                            </div>
                            <div style={{ display: "flex", gap: "8px" }}>
                              <button
                                type="button"
                                onClick={() => setSelectedGdriveFiles(gdriveFiles.filter((f) => !f.is_folder).map((f) => f.id))}
                                style={{ background: "none", border: "none", color: "#2563eb", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer" }}
                              >
                                Select All
                              </button>
                              <button
                                type="button"
                                onClick={() => setSelectedGdriveFiles([])}
                                style={{ background: "none", border: "none", color: "#dc2626", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer" }}
                              >
                                Deselect All
                              </button>
                            </div>
                          </div>

                          <div style={{ maxHeight: "380px", minHeight: "240px", overflowY: "auto", background: "#ffffff", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}>
                            {/* Render Subfolders First */}
                            {gdriveFiles.filter((f) => f.is_folder).map((folder) => (
                              <div
                                key={folder.id}
                                onClick={() => handleFetchGDrive(folder.id, folder.name)}
                                style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 10px", cursor: "pointer", fontSize: "0.82rem", color: "#1d4ed8", background: "#eff6ff", borderRadius: "6px", marginBottom: "6px", fontWeight: 700, border: "1px solid #bfdbfe" }}
                                title="Click to open subfolder"
                              >
                                📁 <span>{folder.name}</span>
                                <span style={{ marginLeft: "auto", fontSize: "0.75rem", color: "#2563eb", fontWeight: 700 }}>Open Subfolder ➔</span>
                              </div>
                            ))}

                            {/* Render Resumes Next */}
                            {gdriveFiles.filter((f) => !f.is_folder).map((file) => (
                              <label key={file.id} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "4px 6px", cursor: "pointer", fontSize: "0.82rem", color: "#1e293b" }}>
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
                                📄 <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div style={{ fontSize: "0.82rem", color: "#64748b", textAlign: "center", padding: "20px 0" }}>
                          {fetchingGdrive ? "Fetching all Google Drive files and subfolders..." : "Enter a Google Drive Folder ID above and click Fetch Folder to list available resumes."}
                        </div>
                      )}
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
                onClick={() => handleFetchGDrive()}
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
                  {/* Folder Breadcrumbs & Back Button */}
                  {folderStack.length > 1 && (
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", background: "#eff6ff", padding: "6px 12px", borderRadius: "6px", border: "1px solid #bfdbfe" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.82rem", flexWrap: "wrap" }}>
                        <span style={{ fontWeight: 700, color: "#1e40af" }}>Folder Path:</span>
                        {folderStack.map((folder, idx) => (
                          <span key={folder.id} style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                            {idx > 0 && <span style={{ color: "#93c5fd" }}>/</span>}
                            <button
                              type="button"
                              onClick={() => navigateBackGDrive(idx)}
                              style={{ background: "none", border: "none", color: idx === folderStack.length - 1 ? "#1e293b" : "#2563eb", fontWeight: idx === folderStack.length - 1 ? 700 : 500, cursor: "pointer", textDecoration: idx === folderStack.length - 1 ? "none" : "underline", padding: 0 }}
                            >
                              📁 {folder.name}
                            </button>
                          </span>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={() => navigateBackGDrive(folderStack.length - 2)}
                        style={{ background: "#2563eb", color: "#ffffff", border: "none", padding: "4px 10px", borderRadius: "6px", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: "4px", whiteSpace: "nowrap" }}
                      >
                        ⬅ Back
                      </button>
                    </div>
                  )}

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: 700, color: "#334155", fontSize: "0.95rem", cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={gdriveFiles.length > 0 && selectedGdriveFiles.length === gdriveFiles.filter((f) => !f.is_folder).length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedGdriveFiles(gdriveFiles.filter((f) => !f.is_folder).map((f) => f.id));
                          } else {
                            setSelectedGdriveFiles([]);
                          }
                        }}
                        style={{ width: "18px", height: "18px", cursor: "pointer" }}
                      />
                      <span>Select Files ({selectedGdriveFiles.length}/{gdriveFiles.filter((f) => !f.is_folder).length} selected)</span>
                    </label>
                    <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                      <button
                        type="button"
                        onClick={() => setSelectedGdriveFiles(gdriveFiles.filter((f) => !f.is_folder).map((f) => f.id))}
                        style={{ background: "#eff6ff", border: "1px solid #bfdbfe", color: "#2563eb", fontSize: "0.82rem", fontWeight: 700, padding: "4px 12px", borderRadius: "6px", cursor: "pointer" }}
                      >
                        Select All ({gdriveFiles.filter((f) => !f.is_folder).length})
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelectedGdriveFiles([])}
                        style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626", fontSize: "0.82rem", fontWeight: 700, padding: "4px 12px", borderRadius: "6px", cursor: "pointer" }}
                      >
                        Deselect All
                      </button>
                    </div>
                  </div>

                  <div
                    style={{
                      maxHeight: "380px",
                      minHeight: "240px",
                      overflowY: "auto",
                      background: "#ffffff",
                      padding: "14px",
                      borderRadius: "8px",
                      border: "1px solid #cbd5e1",
                      boxShadow: "inset 0 1px 3px rgba(0,0,0,0.05)"
                    }}
                  >
                    {/* Render Subfolders First */}
                    {gdriveFiles.filter((f) => f.is_folder).map((folder) => (
                      <div
                        key={folder.id}
                        onClick={() => handleFetchGDrive(folder.id, folder.name)}
                        style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 12px", cursor: "pointer", fontSize: "0.88rem", color: "#1d4ed8", background: "#eff6ff", borderRadius: "6px", marginBottom: "6px", fontWeight: 700, border: "1px solid #bfdbfe" }}
                        title="Click to open subfolder"
                      >
                        📁 <span>{folder.name}</span>
                        <span style={{ marginLeft: "auto", fontSize: "0.78rem", color: "#2563eb", fontWeight: 700 }}>Open Subfolder ➔</span>
                      </div>
                    ))}

                    {/* Render Resumes */}
                    {gdriveFiles.filter((f) => !f.is_folder).map((file) => (
                      <label
                        key={file.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          padding: "6px 8px",
                          cursor: "pointer",
                          color: "#334155",
                          fontSize: "0.88rem",
                          borderRadius: "4px",
                          transition: "background 0.15s ease",
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "#f1f5f9"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
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
                          style={{ width: "16px", height: "16px", cursor: "pointer" }}
                        />
                        📄 <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</span>
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

                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleExportLiveSheetExcel}
                  disabled={fetchingLiveSheet || liveSheetRows.length === 0}
                  style={{ fontSize: "0.85rem", padding: "8px 16px", background: "#059669" }}
                >
                  Download Excel
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
                          {liveSheetHeaders.map((headerName, cIdx) => {
                            let val = row[cIdx] !== undefined ? String(row[cIdx]).trim() : "";
                            const normHeader = (headerName || "").toLowerCase();
                            const isRankCol = cIdx === 0 && (normHeader.includes("rank") || normHeader.includes("s.no") || normHeader.includes("s no") || normHeader.includes("s_no"));
                            if (isRankCol) {
                              val = String(rIdx + 1);
                            }
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
            <CandidateGrid candidates={results} onClearGrid={handleClearGrid} />

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

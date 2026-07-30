"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import CandidateGrid from "@/components/CandidateGrid";
import CandidateCard from "@/components/CandidateCard";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState("batch");
  const [backendOnline, setBackendOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  // Batch Form State
  const [batchResumes, setBatchResumes] = useState([]);
  const [batchJdText, setBatchJdText] = useState("");
  const [batchJdFile, setBatchJdFile] = useState(null);
  const [batchJdMode, setBatchJdMode] = useState("text");

  // Single Form State
  const [singleResume, setSingleResume] = useState(null);
  const [singleJdText, setSingleJdText] = useState("");
  const [singleJdFile, setSingleJdFile] = useState(null);
  const [singleJdMode, setSingleJdMode] = useState("text");

  // GDrive Form State
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveFiles, setGdriveFiles] = useState([]);
  const [selectedGdriveFiles, setSelectedGdriveFiles] = useState([]);
  const [gdriveJdText, setGdriveJdText] = useState("");
  const [fetchingGdrive, setFetchingGdrive] = useState(false);

  // Check Backend Health
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch(`${BACKEND_URL}/`);
        if (res.ok) setBackendOnline(true);
        else setBackendOnline(false);
      } catch {
        setBackendOnline(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
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
      e.target.value = ""; // Reset input so user can add more files
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
    setResults([]);

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

      const res = await fetch("${BACKEND_URL}/api/rank", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to process resumes.");

      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle Single Submit
  const handleSingleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!singleResume) {
      setError("Please select a candidate resume file.");
      return;
    }
    if (singleJdMode === "text" && !singleJdText.trim()) {
      setError("Please enter Job Description text.");
      return;
    }
    if (singleJdMode === "file" && !singleJdFile) {
      setError("Please upload a Job Description file.");
      return;
    }

    setLoading(true);
    setResults([]);

    try {
      const formData = new FormData();
      formData.append("resumes", singleResume);

      if (singleJdMode === "file" && singleJdFile) {
        formData.append("jd_file", singleJdFile);
      } else {
        formData.append("jd_text", singleJdText);
      }

      const res = await fetch("${BACKEND_URL}/api/rank", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to evaluate candidate.");

      setResults(data.results || []);
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
    setResults([]);

    try {
      const selectedObjList = gdriveFiles.filter((f) => selectedGdriveFiles.includes(f.id));
      const res = await fetch("${BACKEND_URL}/api/gdrive/rank", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          folder_id: gdriveFolderId,
          selected_files: selectedObjList,
          jd_text: gdriveJdText,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Google Drive ranking failed.");

      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Tab Header Details
  const getTabHeader = () => {
    if (activeTab === "batch") {
      return {
        title: "Batch Resume Ranking",
        description: "Upload multiple candidate resumes and rank them against your Job Description.",
      };
    } else if (activeTab === "single") {
      return {
        title: "Single Candidate Match",
        description: "Evaluate 1 candidate resume against a target role description.",
      };
    } else {
      return {
        title: "Google Drive Folder Import",
        description: "Fetch candidate resumes directly from a Google Drive Folder ID.",
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
          setResults([]);
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
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontWeight: 700,
                      marginBottom: "8px",
                      color: "#334155",
                      fontSize: "0.9rem",
                    }}
                  >
                    1. Job Description
                  </label>
                  <div style={{ display: "flex", gap: "10px", marginBottom: "12px" }}>
                    <button
                      type="button"
                      style={{
                        padding: "6px 14px",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        background: batchJdMode === "text" ? "#2563eb" : "#f1f5f9",
                        color: batchJdMode === "text" ? "#fff" : "#334155",
                        fontSize: "0.85rem",
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
                        padding: "6px 14px",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        background: batchJdMode === "file" ? "#2563eb" : "#f1f5f9",
                        color: batchJdMode === "file" ? "#fff" : "#334155",
                        fontSize: "0.85rem",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                      onClick={() => setBatchJdMode("file")}
                    >
                      Upload File
                    </button>
                  </div>

                  {batchJdMode === "text" ? (
                    <textarea
                      className="form-textarea"
                      rows={8}
                      placeholder="Paste job description requirements..."
                      value={batchJdText}
                      onChange={(e) => setBatchJdText(e.target.value)}
                    />
                  ) : (
                    <input
                      type="file"
                      className="form-input"
                      accept=".pdf,.docx"
                      onChange={(e) => setBatchJdFile(e.target.files[0])}
                    />
                  )}
                </div>

                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
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

                  {/* Dropzone with Drag & Drop */}
                  <div
                    className="dropzone"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleBatchDrop}
                    style={{ minHeight: "180px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}
                  >
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.docx"
                      style={{ display: "none" }}
                      id="batch-file-input"
                      onChange={handleBatchFileSelect}
                    />
                    <label htmlFor="batch-file-input" style={{ cursor: "pointer", width: "100%", height: "100%" }}>
                      <div style={{ fontWeight: 700, color: "#059669", fontSize: "1.05rem" }}>
                        Click to Choose or Drag & Drop Resumes
                      </div>
                      <div style={{ fontSize: "0.82rem", color: "#64748b", marginTop: "4px" }}>
                        Select multiple PDF or DOCX files at once (or add more)
                      </div>
                    </label>
                  </div>

                  {/* Selected Resumes Badges with Remove (✕) Button */}
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

        {/* TAB 2: SINGLE CANDIDATE */}
        {activeTab === "single" && (
          <div className="glass-panel">
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              Single Match Evaluation
            </h3>
            <p style={{ fontSize: "0.88rem", color: "#64748b", marginBottom: "24px" }}>
              Evaluate 1 candidate resume against a Job Description.
            </p>

            <form onSubmit={handleSingleSubmit}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
                <div>
                  <label style={{ display: "block", fontWeight: 700, marginBottom: "8px", color: "#334155", fontSize: "0.9rem" }}>
                    1. Candidate Resume (PDF/DOCX)
                  </label>
                  <input
                    type="file"
                    className="form-input"
                    accept=".pdf,.docx"
                    onChange={(e) => setSingleResume(e.target.files[0])}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontWeight: 700, marginBottom: "8px", color: "#334155", fontSize: "0.9rem" }}>
                    2. Job Description
                  </label>
                  <div style={{ display: "flex", gap: "10px", marginBottom: "12px" }}>
                    <button
                      type="button"
                      style={{
                        padding: "6px 14px",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        background: singleJdMode === "text" ? "#2563eb" : "#f1f5f9",
                        color: singleJdMode === "text" ? "#fff" : "#334155",
                        fontSize: "0.85rem",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                      onClick={() => setSingleJdMode("text")}
                    >
                      Paste Text
                    </button>
                    <button
                      type="button"
                      style={{
                        padding: "6px 14px",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        background: singleJdMode === "file" ? "#2563eb" : "#f1f5f9",
                        color: singleJdMode === "file" ? "#fff" : "#334155",
                        fontSize: "0.85rem",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                      onClick={() => setSingleJdMode("file")}
                    >
                      Upload File
                    </button>
                  </div>

                  {singleJdMode === "text" ? (
                    <textarea
                      className="form-textarea"
                      rows={6}
                      placeholder="Paste job description requirements..."
                      value={singleJdText}
                      onChange={(e) => setSingleJdText(e.target.value)}
                    />
                  ) : (
                    <input
                      type="file"
                      className="form-input"
                      accept=".pdf,.docx"
                      onChange={(e) => setSingleJdFile(e.target.files[0])}
                    />
                  )}
                </div>
              </div>

              <button type="submit" className="btn-primary" style={{ width: "100%" }} disabled={loading}>
                {loading ? "Analyzing Candidate..." : "Analyze Candidate"}
              </button>
            </form>
          </div>
        )}

        {/* TAB 3: GDRIVE IMPORT */}
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

        {/* RESULTS SECTION */}
        {results.length > 0 && (
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

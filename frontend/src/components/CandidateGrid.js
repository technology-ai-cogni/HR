import React, { useState, useEffect } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const POSITIONS = [
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
];

export default function CandidateGrid({ candidates, onClearGrid }) {
  const mapCandidatesToGrid = (cands) => {
    const totalCount = cands.length;
    return cands.map((c, idx) => {
      const rData = c.scores?.resume_data || {};

      let defaultPos = c.position || "Select Position...";
      if (defaultPos === "Select Position..." && rData.job_title) {
        const found = POSITIONS.find((p) => p.toLowerCase() === rData.job_title.toLowerCase());
        if (found) {
          defaultPos = found;
        }
      }

      let verdict = c.hire_verdict || c.scores?.hire_recommendation || "No";
      if (verdict !== "Yes") verdict = "No";

      const reqExp = c.required_experience || c.scores?.required_experience || "0 Years";
      const candExp = c.candidate_experience || c.scores?.candidate_experience || "0 Months";

      return {
        id: c.id || null,
        rank: idx + 1,
        candidate_name: c.candidate_name || rData.candidate_name || c.file_name,
        email: c.email || rData.email || "",
        phone_number: c.phone_number || rData.phone_number || "",
        position: defaultPos,
        file_name: c.file_name,
        hire_verdict: verdict,
        required_experience: reqExp,
        candidate_experience: candExp,
        hiring_stage: c.hiring_stage || "",
        remarks: c.remarks || "",
        recommendation_reason: c.scores?.hire_reason || "",
        resume_link: c.resume_link || c.scores?.resume_link || "",
        scores: c.scores
      };
    });
  };

  const [gridData, setGridData] = useState(() => mapCandidatesToGrid(candidates));

  useEffect(() => {
    setGridData(mapCandidatesToGrid(candidates));
  }, [candidates]);

  const handleFieldChange = async (index, field, value) => {
    const updated = [...gridData];
    updated[index][field] = value;
    setGridData(updated);

    const candId = updated[index].id;
    if (candId) {
      try {
        await fetch(`${BACKEND_URL}/api/candidates/${candId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [field]: value }),
        });
      } catch (err) {
        console.error(`Auto-save error for candidate ${candId}:`, err);
      }
    }
  };

  const handleDelete = async (index, candId) => {
    if (!window.confirm("Are you sure you want to delete this candidate record?")) return;

    if (candId) {
      try {
        await fetch(`${BACKEND_URL}/api/candidates/${candId}`, {
          method: "DELETE",
        });
      } catch (err) {
        console.error(`Delete error for candidate ${candId}:`, err);
      }
    }

    setGridData((prev) => prev.filter((_, i) => i !== index));
  };

  const handleExportExcel = async () => {
    try {
      const payload = {
        candidates: gridData.map((row) => ({
          Rank: row.rank,
          "Candidate Name": row.candidate_name,
          Email: row.email,
          "Phone Number": row.phone_number,
          Position: row.position,
          "File Name": row.file_name,
          Verdict: row.hire_verdict,
          "Required Experience": row.required_experience,
          "Candidate Experience": row.candidate_experience,
          "Hiring Stage": row.hiring_stage,
          Remarks: row.remarks,
          "Recommendation Reason": row.recommendation_reason,
          "Resume Link": row.resume_link,
        })),
      };

      const res = await fetch(`${BACKEND_URL}/api/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Candidate_Rankings_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        return;
      }
    } catch (err) {
      console.warn("Backend Excel export endpoint notice:", err);
    }

    // Client-side Fallback (Generates downloadable Excel/CSV file instantly)
    try {
      const headers = [
        "Rank", "Candidate Name", "Email", "Phone Number", "Position",
        "File Name", "Verdict", "Required Experience", "Candidate Experience",
        "Hiring Stage", "Remarks", "Recommendation Reason", "Resume Link"
      ];

      const csvRows = [headers.join(",")];
      for (const row of gridData) {
        const values = [
          row.rank,
          `"${(row.candidate_name || "").replace(/"/g, '""')}"`,
          `"${(row.email || "").replace(/"/g, '""')}"`,
          `"${(row.phone_number || "").replace(/"/g, '""')}"`,
          `"${(row.position || "").replace(/"/g, '""')}"`,
          `"${(row.file_name || "").replace(/"/g, '""')}"`,
          `"${(row.hire_verdict || "").replace(/"/g, '""')}"`,
          `"${(row.required_experience || "").replace(/"/g, '""')}"`,
          `"${(row.candidate_experience || "").replace(/"/g, '""')}"`,
          `"${(row.hiring_stage || "").replace(/"/g, '""')}"`,
          `"${(row.remarks || "").replace(/"/g, '""')}"`,
          `"${(row.recommendation_reason || "").replace(/"/g, '""')}"`,
          `"${(row.resume_link || "").replace(/"/g, '""')}"`,
        ];
        csvRows.push(values.join(","));
      }

      const csvContent = "\uFEFF" + csvRows.join("\n");
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Candidate_Rankings_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (fallbackErr) {
      alert("Failed to download file: " + fallbackErr.message);
    }
  };

  if (!gridData || gridData.length === 0) return null;

  return (
    <div className="glass-panel" style={{ marginTop: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a" }}>
            Candidate Evaluation Grid
          </h3>
          <p style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "2px" }}>
            Showing {gridData.length} evaluated candidate(s). Edits auto-sync with Google Sheets.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {onClearGrid && (
            <button
              type="button"
              onClick={onClearGrid}
              style={{
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#dc2626",
                fontSize: "0.85rem",
                fontWeight: 700,
                padding: "8px 16px",
                borderRadius: "8px",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                transition: "all 0.15s ease"
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "#fee2e2"}
              onMouseLeave={(e) => e.currentTarget.style.background = "#fef2f2"}
            >
              🗑️ Clear Grid List
            </button>
          )}

          <button className="btn-success" onClick={handleExportExcel} style={{ fontSize: "0.85rem", padding: "8px 16px" }}>
            Download Excel (.xlsx)
          </button>
        </div>
      </div>

      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Candidate Name</th>
              <th>Email</th>
              <th>Phone Number</th>
              <th style={{ minWidth: "190px" }}>Position</th>
              <th>File Name</th>
              <th>Verdict</th>
              <th>Required Exp</th>
              <th>Candidate Exp</th>
              <th style={{ minWidth: "150px" }}>Hiring Stage</th>
              <th style={{ minWidth: "180px" }}>Remarks</th>
              <th>Resume Link</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {gridData.map((row, idx) => (
              <tr key={row.id || idx}>
                <td style={{ fontWeight: 800, color: "#2563eb" }}>#{row.rank}</td>
                <td style={{ fontWeight: 600, color: "#0f172a" }}>{row.candidate_name}</td>
                <td style={{ color: "#2563eb", fontWeight: 500 }}>{row.email || "-"}</td>
                <td style={{ color: "#334155" }}>{row.phone_number || "-"}</td>
                <td>
                  <select
                    className="form-select"
                    value={row.position}
                    onChange={(e) => handleFieldChange(idx, "position", e.target.value)}
                    style={{ fontSize: "0.82rem", padding: "6px 8px" }}
                  >
                    {POSITIONS.map((pos, pIdx) => (
                      <option key={pIdx} value={pos}>
                        {pos}
                      </option>
                    ))}
                  </select>
                </td>
                <td style={{ color: "#64748b", fontSize: "0.8rem" }}>{row.file_name}</td>
                <td>
                  <span className={`verdict-tag ${
                    row.hire_verdict === "Yes" ? "verdict-yes" : "verdict-no"
                  }`}>
                    {row.hire_verdict}
                  </span>
                </td>
                <td style={{ color: "#475569", fontWeight: 600 }}>{row.required_experience}</td>
                <td style={{ color: "#0f172a", fontWeight: 700 }}>{row.candidate_experience}</td>
                <td>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Interview 1"
                    value={row.hiring_stage}
                    onChange={(e) => handleFieldChange(idx, "hiring_stage", e.target.value)}
                    style={{ fontSize: "0.82rem", padding: "4px 8px" }}
                  />
                </td>
                <td>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Good comms"
                    value={row.remarks}
                    onChange={(e) => handleFieldChange(idx, "remarks", e.target.value)}
                    style={{ fontSize: "0.82rem", padding: "4px 8px" }}
                  />
                </td>
                <td>
                  {row.resume_link ? (
                    <a
                      href={row.resume_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "#2563eb", fontWeight: 700, fontSize: "0.82rem", textDecoration: "underline", whiteSpace: "nowrap" }}
                    >
                      View PDF ↗
                    </a>
                  ) : (
                    <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>N/A</span>
                  )}
                </td>
                <td>
                  <button
                    onClick={() => handleDelete(idx, row.id)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#ef4444",
                      fontWeight: 800,
                      cursor: "pointer",
                      fontSize: "1.1rem",
                      padding: "2px 8px",
                    }}
                    title="Delete row"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

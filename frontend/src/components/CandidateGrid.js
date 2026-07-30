"use client";

import { useState } from "react";

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

export default function CandidateGrid({ candidates }) {
  const [gridData, setGridData] = useState(
    candidates.map((c) => {
      const rData = c.scores?.resume_data || {};
      const candTitle = rData.job_title || "";
      
      let defaultPos = "Select Position...";
      if (candTitle) {
        const titleLower = candTitle.toLowerCase();
        for (const pos of POSITIONS.slice(1)) {
          if (pos.toLowerCase().includes(titleLower) || titleLower.includes(pos.toLowerCase())) {
            defaultPos = pos;
            break;
          }
        }
      }

      const llmEval = c.scores?.llm_evaluation || {};
      const overallLlm = llmEval.overall_match?.score ?? Math.round((c.overall_score || 0) * 100);
      const skillLlm = llmEval.skill_match?.score ?? Math.round((c.scores?.skill || 0) * 100);
      const titleLlm = llmEval.title_match?.score ?? Math.round((c.scores?.title || 0) * 100);
      const expLlm = llmEval.experience_match?.score ?? Math.round((c.scores?.experience || 0) * 100);

      return {
        rank: c.rank,
        candidate_name: rData.candidate_name || c.file_name,
        email: rData.email || "",
        phone_number: rData.phone_number || "",
        position: defaultPos,
        file_name: c.file_name,
        hire_verdict: c.scores?.hire_recommendation || "N/A",
        overall_score: overallLlm,
        skill_score: skillLlm,
        title_score: titleLlm,
        exp_score: expLlm,
        years_of_experience: rData.years_of_experience || 0,
        matched_skills: (c.scores?.skill_matched || []).join(", "),
        missing_skills: (c.scores?.skill_missing || []).join(", "),
        hiring_stage: "",
        remarks: "",
        recommendation_reason: c.scores?.hire_reason || "",
        scores: c.scores
      };
    })
  );

  const handleFieldChange = (index, field, value) => {
    const updated = [...gridData];
    updated[index][field] = value;
    setGridData(updated);
  };

  const handleExportExcel = async () => {
    try {
      const candidatesPayload = gridData.map((item) => ({
        file_name: item.file_name,
        overall_score: item.overall_score / 100,
        position: item.position,
        hiring_stage: item.hiring_stage,
        remarks: item.remarks,
        scores: item.scores
      }));

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidates: candidatesPayload })
      });

      if (!res.ok) throw new Error("Failed to export Excel file.");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "candidate_rankings.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert("Export failed: " + err.message);
    }
  };

  return (
    <div className="glass-panel" style={{ marginTop: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a" }}>
            Candidate Evaluation Grid
          </h3>
          <p style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "2px" }}>
            Showing {gridData.length} evaluated candidate(s). Edit Position, Hiring Stage, and Remarks directly in the table.
          </p>
        </div>

        <button className="btn-success" onClick={handleExportExcel}>
          Download Excel (.xlsx)
        </button>
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
              <th>Overall</th>
              <th>Skill</th>
              <th>Title</th>
              <th>Exp</th>
              <th style={{ minWidth: "150px" }}>Hiring Stage</th>
              <th style={{ minWidth: "180px" }}>Remarks</th>
            </tr>
          </thead>
          <tbody>
            {gridData.map((row, idx) => (
              <tr key={idx}>
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
                    row.hire_verdict === "Yes" ? "verdict-yes" :
                    row.hire_verdict === "Maybe" ? "verdict-maybe" : "verdict-no"
                  }`}>
                    {row.hire_verdict}
                  </span>
                </td>
                <td style={{ fontWeight: 800, color: "#059669" }}>{row.overall_score}%</td>
                <td>{row.skill_score}%</td>
                <td>{row.title_score}%</td>
                <td>{row.exp_score}%</td>
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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";

export default function CandidateCard({ candidate }) {
  const [expanded, setExpanded] = useState(false);
  const scores = candidate.scores || {};
  const rData = scores.resume_data || {};

  const candName = candidate.candidate_name || rData.candidate_name || candidate.file_name;
  let verdict = candidate.hire_verdict || scores.hire_recommendation || "No";
  if (verdict !== "Yes") verdict = "No";

  const reason = candidate.recommendation_reason || scores.hire_reason || "";
  const reqExp = candidate.required_experience || scores.required_experience || "0 Years";
  const candExp = candidate.candidate_experience || scores.candidate_experience || "0 Months";

  const matchedSkills = scores.skill_matched || [];
  const missingSkills = scores.skill_missing || [];
  const workHistory = scores.work_history || [];

  return (
    <div className="glass-panel" style={{ padding: "20px", marginBottom: "16px" }}>
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <span style={{ fontSize: "1.3rem", fontWeight: 800, color: "#2563eb" }}>#{candidate.rank}</span>
          <div>
            <h4 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#0f172a" }}>
              {candName} <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 400 }}>({candidate.file_name})</span>
            </h4>
            <div style={{ display: "flex", gap: "16px", fontSize: "0.85rem", color: "#475569", marginTop: "4px" }}>
              {candidate.email && <span>Email: {candidate.email}</span>}
              {candidate.phone_number && <span>Phone: {candidate.phone_number}</span>}
              {candidate.position && candidate.position !== "Select Position..." && (
                <span>Position: <strong>{candidate.position}</strong></span>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "0.85rem", color: "#64748b" }}>
              Required Exp: <strong style={{ color: "#475569" }}>{reqExp}</strong>
            </div>
            <div style={{ fontSize: "0.95rem", color: "#0f172a", fontWeight: 700 }}>
              Candidate Exp: <span>{candExp}</span>
            </div>
          </div>

          <span className={`verdict-tag ${verdict === "Yes" ? "verdict-yes" : "verdict-no"}`}>
            {verdict === "Yes" ? "YES — MATCH" : "NO — NO MATCH"}
          </span>

          <button style={{ background: "transparent", border: "none", color: "#64748b", fontSize: "1.1rem" }}>
            {expanded ? "▲" : "▼"}
          </button>
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid #e2e8f0" }}>
          {reason && (
            <div
              style={{
                background: verdict === "Yes" ? "#f0fdf4" : "#fef2f2",
                borderLeft: `4px solid ${verdict === "Yes" ? "#16a34a" : "#dc2626"}`,
                padding: "12px 16px",
                borderRadius: "6px",
                marginBottom: "20px",
                fontSize: "0.9rem",
                color: verdict === "Yes" ? "#14532d" : "#991b1b",
              }}
            >
              <strong>Verdict Rationale:</strong> {reason}
            </div>
          )}

          {/* Skills Badges */}
          <div style={{ marginBottom: "20px" }}>
            <h5 style={{ fontSize: "0.88rem", color: "#334155", marginBottom: "8px", fontWeight: 700 }}>Matched Skills:</h5>
            {matchedSkills.length > 0 ? (
              matchedSkills.map((s, idx) => (
                <span key={idx} className="badge badge-green">
                  {s}
                </span>
              ))
            ) : (
              <span style={{ color: "#94a3b8", fontSize: "0.85rem" }}>None</span>
            )}

            <h5 style={{ fontSize: "0.88rem", color: "#334155", marginTop: "12px", marginBottom: "8px", fontWeight: 700 }}>
              Missing Skills:
            </h5>
            {missingSkills.length > 0 ? (
              missingSkills.map((s, idx) => (
                <span key={idx} className="badge badge-red">
                  {s}
                </span>
              ))
            ) : (
              <span style={{ color: "#94a3b8", fontSize: "0.85rem" }}>None</span>
            )}
          </div>

          {/* Work History Timeline */}
          {workHistory.length > 0 && (
            <div>
              <h5 style={{ fontSize: "0.9rem", color: "#0f172a", marginBottom: "12px", fontWeight: 700 }}>Work History Timeline:</h5>
              {workHistory.map((job, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "#f8fafc",
                    padding: "12px",
                    borderRadius: "8px",
                    marginBottom: "8px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontWeight: 700, color: "#0f172a", fontSize: "0.9rem" }}>
                    {job.role || "Role"} at <span style={{ color: "#2563eb" }}>{job.company || "Company"}</span>
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "2px" }}>
                    Duration: {job.start_date || "?"} - {job.end_date || "?"} (~
                    {job.duration_months
                      ? `${Math.floor(job.duration_months / 12)} yrs ${job.duration_months % 12} mos`
                      : "?"}
                    )
                  </div>
                  {job.skills_used && job.skills_used.length > 0 && (
                    <div style={{ marginTop: "6px" }}>
                      {job.skills_used.map((sk, skIdx) => (
                        <span key={skIdx} className="badge badge-blue">
                          {sk}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";

export default function CandidateCard({ candidate }) {
  const [expanded, setExpanded] = useState(false);
  const scores = candidate.scores || {};
  const rData = scores.resume_data || {};
  const llmEval = scores.llm_evaluation || {};
  
  const candName = rData.candidate_name || candidate.file_name;
  const overall = Math.round((candidate.overall_score || 0) * 100);
  const verdict = scores.hire_recommendation || "N/A";
  const reason = scores.hire_reason || "";

  const skillMatch = llmEval.skill_match || {};
  const titleMatch = llmEval.title_match || {};
  const expMatch = llmEval.experience_match || {};

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
              {rData.email && <span>Email: {rData.email}</span>}
              {rData.phone_number && <span>Phone: {rData.phone_number}</span>}
              {rData.job_title && <span>Title: {rData.job_title}</span>}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <span className={`verdict-tag ${
            verdict === "Yes" ? "verdict-yes" :
            verdict === "Maybe" ? "verdict-maybe" : "verdict-no"
          }`}>
            {verdict === "Yes" ? "RECOMMENDED" : verdict === "Maybe" ? "CONDITIONAL" : "HIGH GAPS"}
          </span>

          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#059669" }}>{overall}%</div>
            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Overall Score</div>
          </div>

          <button style={{ background: "transparent", border: "none", color: "#64748b", fontSize: "1.1rem" }}>
            {expanded ? "▲" : "▼"}
          </button>
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid #e2e8f0" }}>
          {reason && (
            <div style={{ background: "#eff6ff", borderLeft: "4px solid #2563eb", padding: "12px 16px", borderRadius: "6px", marginBottom: "20px", fontSize: "0.9rem", color: "#1e3a8a" }}>
              <strong>Verdict Rationale:</strong> {reason}
            </div>
          )}

          {/* Scores Breakdown */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "20px" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#475569", fontWeight: 600 }}>
                <span>Skill Match</span>
                <span>{skillMatch.score ?? 0}%</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill progress-green" style={{ width: `${skillMatch.score ?? 0}%` }}></div>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#475569", fontWeight: 600 }}>
                <span>Title Match</span>
                <span>{titleMatch.score ?? 0}%</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill progress-blue" style={{ width: `${titleMatch.score ?? 0}%` }}></div>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#475569", fontWeight: 600 }}>
                <span>Experience Match</span>
                <span>{expMatch.score ?? 0}%</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill progress-orange" style={{ width: `${expMatch.score ?? 0}%` }}></div>
              </div>
            </div>
          </div>

          {/* Skills Badges */}
          <div style={{ marginBottom: "20px" }}>
            <h5 style={{ fontSize: "0.88rem", color: "#334155", marginBottom: "8px", fontWeight: 700 }}>Matched Skills:</h5>
            {matchedSkills.length > 0 ? (
              matchedSkills.map((s, idx) => <span key={idx} className="badge badge-green">{s}</span>)
            ) : <span style={{ color: "#94a3b8", fontSize: "0.85rem" }}>None</span>}

            <h5 style={{ fontSize: "0.88rem", color: "#334155", marginTop: "12px", marginBottom: "8px", fontWeight: 700 }}>Missing Skills:</h5>
            {missingSkills.length > 0 ? (
              missingSkills.map((s, idx) => <span key={idx} className="badge badge-red">{s}</span>)
            ) : <span style={{ color: "#94a3b8", fontSize: "0.85rem" }}>None</span>}
          </div>

          {/* Work History */}
          {workHistory.length > 0 && (
            <div>
              <h5 style={{ fontSize: "0.9rem", color: "#0f172a", marginBottom: "12px", fontWeight: 700 }}>Work History Timeline:</h5>
              {workHistory.map((job, idx) => (
                <div key={idx} style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px", marginBottom: "8px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontWeight: 700, color: "#0f172a", fontSize: "0.9rem" }}>
                    {job.role || "Role"} at <span style={{ color: "#2563eb" }}>{job.company || "Company"}</span>
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "2px" }}>
                    Duration: {job.start_date || "?"} - {job.end_date || "?"} (~{((job.duration_months || 0) / 12).toFixed(1)} yrs)
                  </div>
                  {job.skills_used && job.skills_used.length > 0 && (
                    <div style={{ marginTop: "6px" }}>
                      {job.skills_used.map((sk, skIdx) => (
                        <span key={skIdx} className="badge badge-blue">{sk}</span>
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

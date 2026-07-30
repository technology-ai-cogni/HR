"use client";

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="sidebar">
      {/* Top Section: Official COGNITUTE Logo + Crazy Animated HR */}
      <div>
        <div style={{ marginBottom: "32px", padding: "4px 8px" }}>
          {/* Logo Row: Green SVG Symbol + Bold COGNITUTE */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <svg width="36" height="32" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M 35 15 L 90 15 L 90 40 L 40 40 L 40 75 L 20 75 L 20 30 Z" fill="#7cc587" />
              <path d="M 40 55 L 90 55 L 90 85 L 35 85 L 35 70 L 65 70 L 65 55 Z" fill="#66ba72" />
              <path d="M 5 55 L 30 55 L 30 80 L 5 80 Z" fill="#96d6a0" />
            </svg>
            <span style={{
              fontSize: "1.45rem",
              fontWeight: 900,
              color: "#000000",
              letterSpacing: "0.5px",
              fontFamily: "'Inter', sans-serif"
            }}>
              COGNITUTE
            </span>
          </div>

          {/* Crazy Animated HR Directly Below COGNITUTE */}
          <div style={{ marginTop: "4px", paddingLeft: "46px" }}>
            <span className="brand-hr-crazy">HR</span>
          </div>
        </div>

        <div className="nav-group-title">Core Features</div>
        <nav>
          <button
            className={`nav-item ${activeTab === "batch" ? "active" : ""}`}
            onClick={() => setActiveTab("batch")}
          >
            <span>Batch Resume Ranking</span>
          </button>

          <button
            className={`nav-item ${activeTab === "single" ? "active" : ""}`}
            onClick={() => setActiveTab("single")}
          >
            <span>Single Candidate Match</span>
          </button>

          <button
            className={`nav-item ${activeTab === "gdrive" ? "active" : ""}`}
            onClick={() => setActiveTab("gdrive")}
          >
            <span>Google Drive Import</span>
          </button>
        </nav>
      </div>
    </aside>
  );
}

"use client";

export default function Navbar({ title, description }) {
  return (
    <header className="glass-panel" style={{ padding: "20px 28px", marginBottom: "28px" }}>
      <div>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#0f172a", letterSpacing: "-0.5px" }}>
          {title}
        </h1>
        <p style={{ color: "#475569", fontSize: "0.92rem", marginTop: "4px" }}>
          {description}
        </p>
      </div>
    </header>
  );
}

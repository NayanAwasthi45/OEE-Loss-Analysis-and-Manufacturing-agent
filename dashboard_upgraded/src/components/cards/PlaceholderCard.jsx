import { Lock } from "lucide-react";

export default function PlaceholderCard({ title, phase, icon: Icon }) {
  return (
    <div className="placeholder-card" style={{ padding: "24px", textAlign: "center" }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <div
          style={{
            width: "40px",
            height: "40px",
            borderRadius: "10px",
            background: "var(--bg-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {Icon ? (
            <Icon size={20} style={{ color: "var(--text-muted)" }} />
          ) : (
            <Lock size={20} style={{ color: "var(--text-muted)" }} />
          )}
        </div>
        <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          {title}
        </div>
        <div
          style={{
            fontSize: "0.7rem",
            color: "var(--text-muted)",
            background: "var(--bg-primary)",
            padding: "4px 12px",
            borderRadius: "9999px",
          }}
        >
          {phase}
        </div>
      </div>
    </div>
  );
}

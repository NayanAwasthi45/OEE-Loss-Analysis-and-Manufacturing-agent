import { useState, useEffect } from "react";
import { Factory, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { checkHealth } from "../../services/api";

export default function Navbar() {
  const [health, setHealth] = useState(null);
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    checkHealth()
      .then((h) => setHealth(h))
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(t);
  }, []);

  const dateLabel = now.toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
  const timeLabel = now.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <nav
      style={{
        background: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border-color)",
        boxShadow: "0 1px 2px rgba(16,24,40,0.04)",
        padding: "0 24px",
        height: "60px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 50,
        overflow: "hidden",
      }}
    >
      {/* Top accent line */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "3px",
          background: "linear-gradient(90deg, var(--accent-brand), var(--accent-rose), var(--accent-amber))",
        }}
      />

      {/* Left — Brand */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div
          style={{
            background: "linear-gradient(135deg, var(--accent-rose), var(--accent-brand))",
            borderRadius: "9px",
            width: "34px",
            height: "34px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 3px 8px rgba(159, 28, 46, 0.28)",
          }}
        >
          <Factory size={18} color="white" />
        </div>
        <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.2 }}>
          <span
            style={{
              fontWeight: 700,
              fontSize: "0.95rem",
              color: "var(--text-primary)",
              letterSpacing: "-0.01em",
            }}
          >
            OEE Manufacturing Intelligence
          </span>
          <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontWeight: 500 }}>
            Plant Performance &amp; Loss Analytics
          </span>
        </div>
      </div>

      {/* Right — Date + Status */}
      <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
        <div style={{ textAlign: "right", lineHeight: 1.2 }}>
          <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            {dateLabel}
          </div>
          <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>{timeLabel}</div>
        </div>

        <div
          style={{
            width: "1px",
            height: "28px",
            background: "var(--border-color)",
          }}
        />

        {/* System Status */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "0.75rem",
            fontWeight: 600,
            color: health ? "var(--accent-emerald)" : "var(--accent-rose)",
            background: health ? "rgba(14, 164, 114, 0.1)" : "rgba(217, 45, 60, 0.1)",
            padding: "6px 12px",
            borderRadius: "9999px",
          }}
        >
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            style={{ display: "flex" }}
          >
            <Activity size={13} />
          </motion.div>
          <span>{health ? "System Online" : "Connecting..."}</span>
        </div>
      </div>
    </nav>
  );
}

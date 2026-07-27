import { useState, useEffect } from "react";
import { Factory, Activity, Bell, User } from "lucide-react";
import { motion } from "framer-motion";
import { checkHealth } from "../../services/api";

export default function Navbar({ activeTab, setActiveTab }) {
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

      {/* Center — Navigation Tabs */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "var(--bg-primary)", padding: "4px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
        <button
          onClick={() => setActiveTab("dashboard")}
          style={{
            padding: "6px 16px",
            borderRadius: "6px",
            border: "none",
            background: activeTab === "dashboard" ? "var(--bg-secondary)" : "transparent",
            color: activeTab === "dashboard" ? "var(--text-primary)" : "var(--text-muted)",
            fontWeight: activeTab === "dashboard" ? 600 : 500,
            fontSize: "0.85rem",
            cursor: "pointer",
            boxShadow: activeTab === "dashboard" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
            transition: "all 0.2s ease"
          }}
        >
          OEE Analytics
        </button>
        <button
          onClick={() => setActiveTab("scenarios")}
          style={{
            padding: "6px 16px",
            borderRadius: "6px",
            border: "none",
            background: activeTab === "scenarios" ? "var(--bg-secondary)" : "transparent",
            color: activeTab === "scenarios" ? "var(--text-primary)" : "var(--text-muted)",
            fontWeight: activeTab === "scenarios" ? 600 : 500,
            fontSize: "0.85rem",
            cursor: "pointer",
            boxShadow: activeTab === "scenarios" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
            transition: "all 0.2s ease"
          }}
        >
          Scenario Simulations
        </button>
        <button
          onClick={() => setActiveTab("recommendations")}
          style={{
            padding: "6px 16px",
            borderRadius: "6px",
            border: "none",
            background: activeTab === "recommendations" ? "var(--bg-secondary)" : "transparent",
            color: activeTab === "recommendations" ? "var(--text-primary)" : "var(--text-muted)",
            fontWeight: activeTab === "recommendations" ? 600 : 500,
            fontSize: "0.85rem",
            cursor: "pointer",
            boxShadow: activeTab === "recommendations" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
            transition: "all 0.2s ease"
          }}
        >
          AI Recommendations
        </button>
      </div>

      {/* Right — Date + Status */}
      <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
        <div style={{ textAlign: "right", lineHeight: 1.2 }}>
          <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            {dateLabel}
          </div>
          <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>{timeLabel}</div>
        </div>

        <div style={{ textAlign: "right", lineHeight: 1.2 }}>
          <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            Last Sync
          </div>
          <div style={{ fontSize: "0.68rem", color: "var(--accent-emerald)" }}>{timeLabel}</div>
        </div>

        <div
          style={{
            width: "1px",
            height: "28px",
            background: "var(--border-color)",
            margin: "0 4px"
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

        <div
          style={{
            width: "1px",
            height: "28px",
            background: "var(--border-color)",
            margin: "0 4px"
          }}
        />

        {/* Notifications & Profile */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px", color: "var(--text-secondary)" }}>
          <button style={{ background: "none", border: "none", cursor: "pointer", position: "relative" }}>
            <Bell size={18} color="var(--text-secondary)" />
            <span style={{ position: "absolute", top: -2, right: -2, width: 8, height: 8, background: "var(--accent-rose)", borderRadius: "50%" }}></span>
          </button>
          
          <div style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "var(--bg-primary)", border: "1px solid var(--border-color)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <User size={16} color="var(--text-muted)" />
            </div>
            <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.1 }}>
              <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-primary)" }}>Admin User</span>
              <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Plant Manager</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

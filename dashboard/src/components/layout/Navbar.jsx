import { useState, useEffect } from "react";
import { Factory, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { checkHealth } from "../../services/api";

export default function Navbar() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth()
      .then((h) => setHealth(h))
      .catch(() => setHealth(null));
  }, []);

  return (
    <nav
      style={{
        background: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border-color)",
        padding: "0 24px",
        height: "56px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Left — Brand */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          style={{
            background: "linear-gradient(135deg, var(--accent-rose), var(--accent-brand))",
            borderRadius: "8px",
            width: "32px",
            height: "32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 4px rgba(220, 38, 38, 0.2)",
          }}
        >
          <Factory size={18} color="white" />
        </div>
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
      </div>

      {/* Right — Status + Theme */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        {/* System Status */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "0.75rem",
            color: "var(--text-secondary)",
          }}
        >
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            <Activity size={14} color={health ? "#10b981" : "#f43f5e"} />
          </motion.div>
          <span>{health ? "System Online" : "Connecting..."}</span>
        </div>
      </div>
    </nav>
  );
}

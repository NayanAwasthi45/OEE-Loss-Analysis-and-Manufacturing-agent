import { motion } from "framer-motion";
import { Brain, ShieldCheck, AlertTriangle, Search, MessageSquareText } from "lucide-react";
import { getValidationBadge } from "../../lib/utils";

export default function AiInsightPanel({ records }) {
  if (!records || records.length === 0) return null;

  const capabilities = [
    "Analyzes manufacturing error codes",
    "Identifies dominant loss categories",
    "Detects recurring failure patterns",
    "Predicts likely root causes",
    "Validates manufacturing anomalies",
    "Prioritizes maintenance actions",
    "Generates recommendations to improve OEE and reduce downtime"
  ];

  return (
    <motion.div
      className="ai-panel"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      style={{ padding: "24px" }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, var(--accent-rose), var(--accent-brand))",
            borderRadius: "8px",
            width: "32px",
            height: "32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 2px 4px rgba(220, 38, 38, 0.2)",
          }}
        >
          <Brain size={18} color="white" />
        </div>
        <div>
          <div
            style={{
              fontWeight: 700,
              fontSize: "0.95rem",
              color: "var(--text-primary)",
            }}
          >
            Manufacturing AI Intelligence
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
            Groq-powered manufacturing analysis
          </div>
        </div>
      </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "12px", background: "var(--bg-primary)", padding: "16px", borderRadius: "12px", border: "1px solid var(--border-color)" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
            Engine Capabilities
          </div>
          {capabilities.map((cap, idx) => (
            <div key={idx} style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
              <div style={{ marginTop: "5px", width: "5px", height: "5px", borderRadius: "50%", background: "var(--accent-rose)", flexShrink: 0 }} />
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{cap}</span>
            </div>
          ))}
        </div>
    </motion.div>
  );
}

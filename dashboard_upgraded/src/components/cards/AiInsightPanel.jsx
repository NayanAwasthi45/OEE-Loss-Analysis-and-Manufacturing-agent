import { motion } from "framer-motion";
import { Brain, ShieldCheck, AlertTriangle, Search, MessageSquareText } from "lucide-react";
import { getValidationBadge } from "../../lib/utils";

export default function AiInsightPanel({ records }) {
  if (!records || records.length === 0) return null;

  // Show the first non-skipped AI record, or fallback to first record
  const aiRecord =
    records.find((r) => r["AI Validation"] !== "Skipped") || records[0];

  const validation = aiRecord["AI Validation"] || "Skipped";
  const reason = aiRecord["Validation Reason"] || "—";
  const rootCause = aiRecord["Likely Root Cause"] || "—";
  const insight = aiRecord["Manufacturing Insight"] || "—";

  const validationIcon = {
    Verified: <ShieldCheck size={16} />,
    "Partially Verified": <AlertTriangle size={16} />,
    Mismatch: <AlertTriangle size={16} />,
    Skipped: <Search size={16} />,
  };

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
        <div style={{ marginLeft: "auto" }}>
          <span className={`badge ${getValidationBadge(validation)}`}>
            {validationIcon[validation]}
            {validation}
          </span>
        </div>
      </div>

      {/* Content Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "16px",
        }}
      >
        {/* Validation Reason */}
        <InfoBlock
          icon={<ShieldCheck size={14} />}
          label="Validation Reason"
          text={reason}
        />
        {/* Root Cause */}
        <InfoBlock
          icon={<Search size={14} />}
          label="Likely Root Cause"
          text={rootCause}
          highlight
        />
        {/* Manufacturing Insight */}
        <div style={{ gridColumn: "1 / -1" }}>
          <InfoBlock
            icon={<MessageSquareText size={14} />}
            label="Manufacturing Insight"
            text={insight}
          />
        </div>
      </div>
    </motion.div>
  );
}

function InfoBlock({ icon, label, text, highlight = false }) {
  return (
    <div
      style={{
        background: "var(--bg-primary)",
        border: "1px solid var(--border-color)",
        borderLeft: highlight ? "3px solid var(--accent-cyan)" : "3px solid var(--border-accent)",
        borderRadius: "8px",
        padding: "14px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          marginBottom: "6px",
          color: "var(--text-muted)",
          fontSize: "0.7rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {icon}
        {label}
      </div>
      <div
        style={{
          fontSize: "0.85rem",
          color: highlight ? "var(--accent-cyan)" : "var(--text-primary)",
          lineHeight: 1.55,
        }}
      >
        {text}
      </div>
    </div>
  );
}

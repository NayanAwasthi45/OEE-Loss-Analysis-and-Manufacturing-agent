import { motion } from "framer-motion";
import { getOeeClass, formatPercent } from "../../lib/utils";

export default function KpiCard({ title, value, icon: Icon, subtitle, delay = 0 }) {
  const numValue = typeof value === "number" ? value : parseFloat(value) || 0;
  const kpiClass = getOeeClass(numValue);

  return (
    <motion.div
      className={`card ${kpiClass}`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
      style={{ padding: "20px" }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "8px",
        }}
      >
        <span
          style={{
            fontSize: "0.72rem",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "var(--text-secondary)",
          }}
        >
          {title}
        </span>
        {Icon && <Icon size={16} style={{ color: "var(--text-muted)" }} />}
      </div>
      <div
        style={{
          fontSize: "1.75rem",
          fontWeight: 700,
          letterSpacing: "-0.02em",
          color: "var(--text-primary)",
        }}
      >
        {formatPercent(numValue)}
      </div>
      {subtitle && (
        <div
          style={{
            fontSize: "0.72rem",
            color: "var(--text-muted)",
            marginTop: "4px",
          }}
        >
          {subtitle}
        </div>
      )}
    </motion.div>
  );
}

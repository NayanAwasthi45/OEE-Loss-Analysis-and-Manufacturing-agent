import { motion } from "framer-motion";
import { getOeeClass, getOeeColor, formatPercent } from "../../lib/utils";

export default function KpiCard({ title, value, icon: Icon, subtitle, delay = 0 }) {
  const numValue = typeof value === "number" ? value : parseFloat(value) || 0;
  const kpiClass = getOeeClass(numValue);
  const color = getOeeColor(numValue);

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
          marginBottom: "14px",
        }}
      >
        <span
          style={{
            fontSize: "0.72rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "var(--text-secondary)",
          }}
        >
          {title}
        </span>
        {Icon && (
          <div
            style={{
              width: "30px",
              height: "30px",
              borderRadius: "8px",
              background: `${color}1a`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Icon size={15} style={{ color }} />
          </div>
        )}
      </div>
      <div
        style={{
          fontSize: "1.9rem",
          fontWeight: 800,
          letterSpacing: "-0.03em",
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
            marginTop: "6px",
          }}
        >
          {subtitle}
        </div>
      )}
    </motion.div>
  );
}

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";
import { getOeeClass, getOeeColor, formatPercent } from "../../lib/utils";

export default function KpiCard({ title, value, icon: Icon, subtitle, delay = 0, trend = 0, trendLabel = "vs last week", showProgress = false }) {
  const numValue = typeof value === "number" ? value : parseFloat(value) || 0;
  const kpiClass = getOeeClass(numValue);
  const color = getOeeColor(numValue);
  const isPositive = trend >= 0;
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;
  const trendColor = isPositive ? "var(--accent-emerald)" : "var(--accent-rose)";

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
          marginBottom: showProgress ? "12px" : "4px"
        }}
      >
        {formatPercent(numValue)}
      </div>

      {showProgress && (
        <div style={{ width: "100%", height: "6px", background: "var(--bg-primary)", borderRadius: "3px", overflow: "hidden", marginBottom: "12px" }}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${numValue}%` }}
            transition={{ duration: 0.8, delay: delay + 0.2, ease: "easeOut" }}
            style={{ height: "100%", background: color, borderRadius: "3px" }}
          />
        </div>
      )}

      {(trend !== 0 || subtitle || trendLabel) && (
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.72rem" }}>
          {trend !== 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: "2px", color: trendColor, fontWeight: 600 }}>
              <TrendIcon size={12} />
              {isPositive ? "+" : ""}{trend}%
            </div>
          )}
          <span style={{ color: "var(--text-muted)" }}>{trendLabel || subtitle}</span>
        </div>
      )}
    </motion.div>
  );
}

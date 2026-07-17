import { motion } from "framer-motion";
import { DollarSign, AlertCircle, TrendingDown, Factory } from "lucide-react";
import { formatCurrency } from "../../lib/utils";

export default function BusinessImpactCard({ summary, records }) {
  if (!summary || summary.total_business_loss === undefined) return null;

  // Find the record with the highest loss to get the machine name
  let highestMachine = "N/A";
  if (records && records.length > 0) {
    const sorted = [...records].sort(
      (a, b) => (b["Estimated Business Loss"] || 0) - (a["Estimated Business Loss"] || 0)
    );
    if (sorted[0]["Estimated Business Loss"] > 0) {
      highestMachine = sorted[0]["Machine ID"] || "Unknown";
    }
  }

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      style={{
        padding: "24px",
        background: "linear-gradient(135deg, rgba(244, 63, 94, 0.05), rgba(245, 158, 11, 0.05))",
        border: "1px solid rgba(244, 63, 94, 0.15)",
        gridColumn: "span 2",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            background: "rgba(244, 63, 94, 0.1)",
            padding: "6px",
            borderRadius: "6px",
            color: "var(--accent-rose)",
          }}
        >
          <DollarSign size={20} />
        </div>
        <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--text-primary)" }}>
          Business Impact (Phase B)
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
        }}
      >
        {/* Total Loss */}
        <div>
          <div
            style={{
              fontSize: "0.7rem",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: "4px",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <AlertCircle size={12} /> Total Loss
          </div>
          <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--accent-rose)" }}>
            {formatCurrency(summary.total_business_loss)}
          </div>
        </div>

        {/* Avg Loss */}
        <div>
          <div
            style={{
              fontSize: "0.7rem",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: "4px",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <TrendingDown size={12} /> Average Loss
          </div>
          <div style={{ fontSize: "1.2rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {formatCurrency(summary.avg_business_loss)}
          </div>
        </div>

        {/* Highest Loss Machine */}
        <div>
          <div
            style={{
              fontSize: "0.7rem",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: "4px",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <Factory size={12} /> Max Loss (Machine)
          </div>
          <div style={{ fontSize: "1.2rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {formatCurrency(summary.max_business_loss)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
            {highestMachine}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

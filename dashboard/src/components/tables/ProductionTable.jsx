import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight } from "lucide-react";
import { getValidationBadge, formatPercent } from "../../lib/utils";

export default function ProductionTable({ records }) {
  const [expandedRow, setExpandedRow] = useState(null);

  if (!records || records.length === 0) return null;

  const toggleRow = (idx) => setExpandedRow(expandedRow === idx ? null : idx);

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid var(--border-color)",
          fontSize: "0.72rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--text-secondary)",
        }}
      >
        Production Details
      </div>
      <div style={{ overflowX: "auto", maxHeight: "400px", overflowY: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 28 }}></th>
              <th>Date</th>
              <th>Machine</th>
              <th>Shift</th>
              <th>OEE</th>
              <th>Avail.</th>
              <th>Perf.</th>
              <th>Quality</th>
              <th>Dominant Loss</th>
              <th>AI Validation</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r, idx) => (
              <TableRow
                key={idx}
                record={r}
                idx={idx}
                isExpanded={expandedRow === idx}
                onToggle={() => toggleRow(idx)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TableRow({ record, idx, isExpanded, onToggle }) {
  const r = record;
  const validation = r["AI Validation"] || "Skipped";

  return (
    <>
      <tr onClick={onToggle}>
        <td>
          {isExpanded ? (
            <ChevronDown size={14} style={{ color: "var(--text-muted)" }} />
          ) : (
            <ChevronRight size={14} style={{ color: "var(--text-muted)" }} />
          )}
        </td>
        <td style={{ fontSize: "0.8rem" }}>{r["Date"] || "—"}</td>
        <td style={{ fontWeight: 600, fontSize: "0.8rem" }}>{r["Machine ID"] || "—"}</td>
        <td style={{ fontSize: "0.8rem" }}>{r["Shift"] || "—"}</td>
        <td style={{ fontWeight: 700, fontSize: "0.8rem" }}>{formatPercent(r["OEE"])}</td>
        <td style={{ fontSize: "0.8rem" }}>{formatPercent(r["Availability"])}</td>
        <td style={{ fontSize: "0.8rem" }}>{formatPercent(r["Performance"])}</td>
        <td style={{ fontSize: "0.8rem" }}>{formatPercent(r["Quality"])}</td>
        <td style={{ fontSize: "0.78rem" }}>
          {(r["Dominant Loss"] || "—").length > 25
            ? (r["Dominant Loss"] || "").slice(0, 25) + "…"
            : r["Dominant Loss"] || "—"}
        </td>
        <td>
          <span className={`badge ${getValidationBadge(validation)}`}>
            {validation}
          </span>
        </td>
      </tr>
      <AnimatePresence>
        {isExpanded && (
          <tr>
            <td colSpan={10} style={{ padding: 0 }}>
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                style={{ overflow: "hidden" }}
              >
                <div
                  style={{
                    padding: "16px 24px",
                    background: "var(--bg-primary)",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "12px",
                    fontSize: "0.8rem",
                  }}
                >
                  <DetailItem label="Error Code" value={r["Error Code"]} />
                  <DetailItem label="Likely Root Cause" value={r["Likely Root Cause"]} />
                  <DetailItem label="Validation Reason" value={r["Validation Reason"]} />
                  <DetailItem label="Manufacturing Insight" value={r["Manufacturing Insight"]} />
                  <DetailItem label="Dominant Loss" value={r["Dominant Loss"]} />
                  <DetailItem label="Priority" value={`${r["Priority"] || "—"} (Score: ${r["Priority Score"] || 0})`} />
                </div>
              </motion.div>
            </td>
          </tr>
        )}
      </AnimatePresence>
    </>
  );
}

function DetailItem({ label, value }) {
  return (
    <div>
      <div
        style={{
          fontSize: "0.68rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          color: "var(--text-muted)",
          marginBottom: "4px",
        }}
      >
        {label}
      </div>
      <div style={{ color: "var(--text-primary)", lineHeight: 1.5 }}>
        {value || "—"}
      </div>
    </div>
  );
}

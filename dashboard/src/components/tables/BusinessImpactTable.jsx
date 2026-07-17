import { useState } from "react";
import { DollarSign } from "lucide-react";
import { formatCurrency } from "../../lib/utils";

export default function BusinessImpactTable({ records }) {
  if (!records || records.length === 0) return null;

  // Filter only records that have financial data
  const financialRecords = records.filter(r => r["Estimated Business Loss"] !== undefined);
  if (financialRecords.length === 0) return null;

  return (
    <div className="card" style={{ overflow: "hidden", marginTop: "24px", gridColumn: "1 / -1" }}>
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid var(--border-color)",
          fontSize: "0.72rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--text-secondary)",
          display: "flex",
          alignItems: "center",
          gap: "8px"
        }}
      >
        <DollarSign size={14} style={{ color: "var(--accent-rose)" }} />
        Detailed Business Impact
      </div>
      <div style={{ overflowX: "auto", maxHeight: "400px", overflowY: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Machine</th>
              <th>Availability Loss (₹)</th>
              <th>Performance Loss (₹)</th>
              <th>Quality (Scrap) Loss (₹)</th>
              <th>Primary Driver</th>
              <th>Total Loss (₹)</th>
              <th>Priority Score</th>
            </tr>
          </thead>
          <tbody>
            {financialRecords.map((r, idx) => (
              <tr key={idx}>
                <td style={{ fontSize: "0.8rem" }}>{r["Date"] || "—"}</td>
                <td style={{ fontWeight: 600, fontSize: "0.8rem" }}>{r["Machine ID"] || "—"}</td>
                <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{formatCurrency(r["Downtime Cost"])}</td>
                <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{formatCurrency(r["Production Loss Cost"])}</td>
                <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{formatCurrency(r["Scrap Cost"])}</td>
                <td style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                  {r["Primary Business Driver"] || "—"}
                </td>
                <td style={{ fontWeight: 700, fontSize: "0.85rem", color: "var(--accent-rose)" }}>
                  {formatCurrency(r["Estimated Business Loss"])}
                </td>
                <td style={{ fontSize: "0.8rem" }}>
                  <span style={{ 
                    background: "rgba(0,0,0,0.05)", 
                    padding: "2px 8px", 
                    borderRadius: "4px",
                    fontWeight: 700
                  }}>
                    {r["Priority Score"] || 0}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

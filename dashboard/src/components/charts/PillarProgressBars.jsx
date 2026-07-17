import { getOeeColor } from "../../lib/utils";

function ProgressBar({ label, value }) {
  const numValue = Number(value) || 0;
  const color = getOeeColor(numValue);

  return (
    <div style={{ marginBottom: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
        <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {label}
        </span>
        <span style={{ fontSize: "0.85rem", fontWeight: 700, color }}>
          {numValue.toFixed(1)}%
        </span>
      </div>
      <div style={{ width: "100%", height: "8px", background: "var(--gauge-track)", borderRadius: "4px", overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            background: color,
            width: `${Math.min(100, Math.max(0, numValue))}%`,
            transition: "width 1s ease-in-out",
          }}
        />
      </div>
    </div>
  );
}

export default function PillarProgressBars({ availability, performance, quality }) {
  return (
    <div className="card" style={{ padding: "24px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <ProgressBar label="Availability" value={availability} />
      <ProgressBar label="Performance" value={performance} />
      <ProgressBar label="Quality" value={quality} />
    </div>
  );
}

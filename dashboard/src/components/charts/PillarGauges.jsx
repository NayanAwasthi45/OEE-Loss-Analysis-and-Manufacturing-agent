import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { getOeeColor } from "../../lib/utils";

function MiniGauge({ label, value }) {
  const numValue = Number(value) || 0;
  const color = getOeeColor(numValue);
  const data = [
    { value: numValue },
    { value: Math.max(0, 100 - numValue) },
  ];

  return (
    <div style={{ textAlign: "center", flex: 1 }}>
      <div
        style={{
          fontSize: "0.68rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          color: "var(--text-secondary)",
          marginBottom: "4px",
        }}
      >
        {label}
      </div>
      <div style={{ width: "100%", height: 100, position: "relative" }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="55%"
              startAngle={220}
              endAngle={-40}
              innerRadius="65%"
              outerRadius="90%"
              paddingAngle={0}
              dataKey="value"
              stroke="none"
            >
              <Cell fill={color} />
              <Cell fill="var(--gauge-track)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div
          style={{
            position: "absolute",
            top: "52%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            fontSize: "1rem",
            fontWeight: 700,
            color,
          }}
        >
          {numValue.toFixed(1)}%
        </div>
      </div>
    </div>
  );
}

export default function PillarGauges({ availability, performance, quality }) {
  return (
    <div className="card" style={{ padding: "16px" }}>
      <div style={{ display: "flex", gap: "4px" }}>
        <MiniGauge label="Availability" value={availability} />
        <MiniGauge label="Performance" value={performance} />
        <MiniGauge label="Quality" value={quality} />
      </div>
    </div>
  );
}

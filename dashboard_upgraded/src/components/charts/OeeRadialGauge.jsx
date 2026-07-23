import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { getOeeColor } from "../../lib/utils";

export default function OeeRadialGauge({ value }) {
  const numValue = Number(value) || 0;
  const color = getOeeColor(numValue);
  const data = [
    { name: "OEE", value: numValue },
    { name: "Remaining", value: Math.max(0, 100 - numValue) },
  ];

  const status = numValue >= 85 ? "Excellent" : numValue >= 65 ? "Good" : "Critical";

  return (
    <div className="card" style={{ padding: "20px", textAlign: "center", position: "relative" }}>
      <div
        style={{
          fontSize: "0.72rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--text-secondary)",
          marginBottom: "8px",
        }}
      >
        Overall OEE
      </div>
      <div style={{ width: "100%", height: 180, position: "relative" }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              startAngle={220}
              endAngle={-40}
              innerRadius="75%"
              outerRadius="90%"
              paddingAngle={0}
              dataKey="value"
              stroke="none"
              animationBegin={0}
              animationDuration={1500}
              animationEasing="ease-out"
            >
              <Cell fill={color} />
              <Cell fill="var(--gauge-track)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2rem", fontWeight: 800, color, letterSpacing: "-0.03em", lineHeight: 1, marginBottom: "4px" }}>
            {numValue.toFixed(1)}%
          </div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color, marginTop: "2px" }}>
            {status}
          </div>
        </div>
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px", fontWeight: 500 }}>
        Target: 90%
      </div>
    </div>
  );
}

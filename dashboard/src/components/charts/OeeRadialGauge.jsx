import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { getOeeColor } from "../../lib/utils";

export default function OeeRadialGauge({ value }) {
  const numValue = Number(value) || 0;
  const color = getOeeColor(numValue);
  const data = [
    { name: "OEE", value: numValue },
    { name: "Remaining", value: Math.max(0, 100 - numValue) },
  ];

  return (
    <div className="card" style={{ padding: "20px", textAlign: "center" }}>
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
              innerRadius="70%"
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
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2rem", fontWeight: 800, color, letterSpacing: "-0.03em" }}>
            {numValue.toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
}

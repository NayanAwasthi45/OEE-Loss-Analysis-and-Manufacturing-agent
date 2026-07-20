import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const STATUS_COLORS = {
  Verified: "#10b981",
  "Partially Verified": "#f59e0b",
  Mismatch: "#f43f5e",
  Skipped: "#64748b",
};

export default function AiValidationPie({ aiDistribution }) {
  if (!aiDistribution || Object.keys(aiDistribution).length === 0) return null;

  const data = Object.entries(aiDistribution).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="card" style={{ padding: "20px" }}>
      <div
        style={{
          fontSize: "0.72rem",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--text-secondary)",
          marginBottom: "16px",
        }}
      >
        AI Validation Distribution
      </div>
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              outerRadius="80%"
              paddingAngle={2}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={STATUS_COLORS[entry.name] || "#64748b"}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export default function LossBreakdownBar({ records }) {
  if (!records || records.length === 0) return null;

  const data = records.slice(0, 10).map((r) => ({
    name: `${r["Date"] || ""}`.slice(5) || r["Machine ID"] || "—",
    Availability: Number(r["Availability Loss"]) || 0,
    Performance: Number(r["Performance Loss"]) || 0,
    Quality: Number(r["Quality Loss"]) || 0,
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
        Loss Breakdown
      </div>
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 40, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={[0, "dataMax"]}
            />
            <YAxis
              dataKey="name"
              type="category"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={48}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: "0.7rem" }} />
            <Bar dataKey="Availability" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} />
            <Bar dataKey="Performance" stackId="a" fill="#f59e0b" />
            <Bar dataKey="Quality" stackId="a" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

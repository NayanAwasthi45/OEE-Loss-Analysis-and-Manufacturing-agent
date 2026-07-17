import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

export default function DominantLossBar({ lossDistribution }) {
  if (!lossDistribution || Object.keys(lossDistribution).length === 0) return null;

  // Convert dictionary into array and sort by value descending
  const data = Object.entries(lossDistribution)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

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
        Dominant Loss Drivers
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
              width={60}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
                borderRadius: 8,
                fontSize: 12,
              }}
              cursor={{ fill: "var(--bg-card-hover)" }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill="var(--accent-rose)" />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

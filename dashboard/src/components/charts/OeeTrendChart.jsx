import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area,
} from "recharts";

export default function OeeTrendChart({ records }) {
  if (!records || records.length === 0) return null;

  // Sort records chronologically by Date
  const sortedRecords = [...records].sort((a, b) => {
    return new Date(a["Date"]) - new Date(b["Date"]);
  });

  const data = sortedRecords.map((r, i) => ({
    name: r["Date"] || `Record ${i + 1}`,
    OEE: Number(r["OEE"]) || 0,
    Availability: Number(r["Availability"]) || 0,
    Performance: Number(r["Performance"]) || 0,
    Quality: Number(r["Quality"]) || 0,
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
        OEE Trend
      </div>
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis
              dataKey="name"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              axisLine={{ stroke: "var(--border-color)" }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <defs>
              <linearGradient id="oeeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="OEE" fill="url(#oeeGrad)" stroke="none" />
            <Line type="monotone" dataKey="OEE" stroke="#10b981" strokeWidth={2.5} dot={{ r: 4, fill: "#10b981" }} />
            <Line type="monotone" dataKey="Availability" stroke="#3b82f6" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
            <Line type="monotone" dataKey="Performance" stroke="#f59e0b" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
            <Line type="monotone" dataKey="Quality" stroke="#8b5cf6" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

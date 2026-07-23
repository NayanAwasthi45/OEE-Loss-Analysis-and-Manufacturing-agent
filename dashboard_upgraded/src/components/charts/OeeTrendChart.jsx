import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ReferenceLine, Legend
} from "recharts";

export default function OeeTrendChart({ records }) {
  if (!records || records.length === 0) return null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: 8, padding: "10px", fontSize: 12, boxShadow: "var(--shadow-card)" }}>
          <div style={{ fontWeight: 600, marginBottom: "8px", color: "var(--text-primary)" }}>{label}</div>
          <div style={{ color: "var(--accent-rose)", margin: "4px 0", fontWeight: 600 }}>OEE: {data.OEE}%</div>
          <div style={{ color: "var(--text-secondary)", margin: "4px 0" }}>Availability: {data.Availability}%</div>
          <div style={{ color: "var(--text-secondary)", margin: "4px 0" }}>Performance: {data.Performance}%</div>
          <div style={{ color: "var(--text-secondary)", margin: "4px 0" }}>Quality: {data.Quality}%</div>
        </div>
      );
    }
    return null;
  };

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
          <ComposedChart data={data} margin={{ top: 20, right: 20, bottom: 5, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              axisLine={{ stroke: "var(--border-color)" }}
              tickLine={false}
              dy={10}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "var(--border-color)", strokeWidth: 1, strokeDasharray: "4 4" }} />
            <defs>
              <linearGradient id="oeeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-rose)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="var(--accent-rose)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <ReferenceLine 
              y={90} 
              stroke="var(--accent-emerald)" 
              strokeDasharray="4 4"
              label={{ position: "insideTopRight", value: "Target: 90%", fill: "var(--accent-emerald)", fontSize: 11, fontWeight: 600 }}
            />
            <Area type="monotone" dataKey="OEE" fill="url(#oeeGrad)" stroke="none" activeDot={false} />
            <Line 
              type="monotone" 
              dataKey="OEE" 
              stroke="var(--accent-rose)" 
              strokeWidth={3} 
              dot={{ r: 5, fill: "var(--accent-rose)", strokeWidth: 2, stroke: "#fff" }} 
              activeDot={{ r: 7, fill: "var(--accent-brand)", strokeWidth: 0 }}
              animationDuration={1500}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

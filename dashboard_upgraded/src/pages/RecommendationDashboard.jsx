import React, { useState } from "react";
import { motion } from "framer-motion";
import { Play, Activity, TrendingUp, AlertCircle, FileText, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function RecommendationDashboard({ analysisProps }) {
  const { data } = analysisProps;
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [citations, setCitations] = useState([]);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");

  const analysisData = data;

  const generateRecommendations = async () => {
    if (!analysisData || !analysisData.summary) {
      setError("No base data found. Please run an OEE Analytics query first.");
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);

    const mode = "recommendation";
    const text = query.trim() || "Please provide AI recommendations to reduce the primary losses based on the current data.";

    const analyticsContext = {
      "Average OEE": analysisData.summary.avg_oee,
      "Average Availability": analysisData.summary.avg_availability,
      "Average Performance": analysisData.summary.avg_performance,
      "Average Quality": analysisData.summary.avg_quality,
      "Total Records": analysisData.summary.records_count,
    };
    
    if (analysisData.records && analysisData.records.length > 0) {
      const topLoss = analysisData.records.reduce((prev, current) => 
        (prev["Estimated Business Loss"] > current["Estimated Business Loss"]) ? prev : current
      );
      analyticsContext["Machine"] = topLoss["Machine ID"];
      analyticsContext["AI Root Cause"] = topLoss["AI Root Cause"];
      analyticsContext["Estimated Business Loss"] = topLoss["Estimated Business Loss"];
    }

    try {
      const token = localStorage.getItem("oee_token");
      const res = await fetch("/api/chat/message", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          ...(token && { "Authorization": `Bearer ${token}` })
        },
        body: JSON.stringify({
          session_id: "dashboard-rec",
          message: text,
          mode: mode,
          analytics_context: analyticsContext
        }),
      });

      if (!res.ok) throw new Error("Failed to generate recommendations");
      const data = await res.json();
      setResult(data.reply);
      setCitations(data.citations || []);
      setQuery(""); // clear query after sending
    } catch (err) {
      setError("Failed to generate recommendations. Please ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "32px", maxWidth: "1200px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: "1.8rem", fontWeight: 700, margin: "0 0 8px 0", color: "var(--text-primary)" }}>AI Recommendations</h1>
          <p style={{ color: "var(--text-muted)", margin: 0 }}>Actionable insights and corrective actions driven by your manufacturing data.</p>
        </div>
      </div>

      {!analysisData?.summary && (
        <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid var(--accent-amber)", padding: "16px", borderRadius: "8px", display: "flex", gap: "12px", color: "var(--accent-amber)" }}>
          <AlertCircle />
          <span>You need to load data in the OEE Analytics dashboard first before generating recommendations.</span>
        </div>
      )}

      {/* Results Area */}
      <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "40px", minHeight: "500px" }}>
        {error && <div style={{ color: "var(--accent-rose)", marginBottom: "16px" }}>{error}</div>}
        
        {!result && !loading && !error && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)", gap: "16px", marginTop: "100px" }}>
            <FileText size={64} opacity={0.3} />
            <p style={{ fontSize: "1.1rem" }}>Click "Generate Action Plan" to request an AI-driven strategy to reduce top losses.</p>
          </div>
        )}

        {loading && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--accent-emerald)", gap: "16px", marginTop: "100px" }}>
            <motion.div animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 1.5 }}>
              <TrendingUp size={64} />
            </motion.div>
            <p style={{ fontWeight: 600, fontSize: "1.1rem" }}>Formulating Strategy based on actual losses...</p>
          </div>
        )}

        {result && !loading && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="markdown-body" style={{ color: "var(--text-primary)", lineHeight: 1.6 }}>
              <ReactMarkdown
                components={{
                  h2: ({node, ...props}) => <h2 style={{ background: "linear-gradient(90deg, rgba(16, 185, 129, 0.1), transparent)", padding: "12px 16px", borderRadius: "8px", borderLeft: "4px solid var(--accent-emerald)", marginTop: "32px", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "8px" }} {...props} />,
                  h3: ({node, ...props}) => <h3 style={{ color: "var(--text-primary)", marginTop: "24px", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }} {...props} />,
                  p: ({node, ...props}) => <p style={{ color: "var(--text-secondary)", margin: "12px 0", fontSize: "1rem" }} {...props} />,
                  ul: ({node, ...props}) => <ul style={{ background: "var(--bg-card)", padding: "16px 16px 16px 36px", borderRadius: "8px", border: "1px solid var(--border-color)", margin: "16px 0" }} {...props} />,
                  strong: ({node, ...props}) => <strong style={{ color: "var(--text-primary)", fontWeight: 700 }} {...props} />
                }}
              >
                {result}
              </ReactMarkdown>
            </div>
            
            {citations && citations.length > 0 && (
              <div style={{ marginTop: "32px", paddingTop: "24px", borderTop: "1px solid var(--border-color)" }}>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontWeight: 700, marginBottom: "12px", letterSpacing: "0.5px" }}>SOURCES & KNOWLEDGE BASE</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {citations.map((c, idx) => (
                    <span key={idx} style={{ 
                      display: "inline-flex", alignItems: "center", gap: "6px", 
                      padding: "8px 12px", background: "var(--bg-shell)", 
                      border: "1px solid var(--border-color)", borderRadius: "8px", 
                      fontSize: "0.85rem", color: "var(--text-secondary)",
                      boxShadow: "0 2px 4px rgba(0,0,0,0.02)"
                    }}>
                      📄 {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Query Input Area */}
      <div style={{ display: "flex", gap: "12px", background: "var(--bg-secondary)", padding: "16px", borderRadius: "12px", border: "1px solid var(--border-color)" }}>
        <input 
          type="text" 
          placeholder="Ask a specific question (e.g., 'Why is CNC_Milling failing?') or leave blank for a general plan..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') generateRecommendations(); }}
          style={{ flex: 1, padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)", background: "var(--bg-primary)", color: "var(--text-primary)", fontSize: "1rem" }}
        />
        <button
          onClick={generateRecommendations}
          disabled={loading || !analysisData?.summary}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
            padding: "0 32px", borderRadius: "8px", border: "none",
            background: loading || !analysisData?.summary ? "var(--border-color)" : "linear-gradient(135deg, var(--accent-emerald), var(--accent-blue))",
            color: "white", fontWeight: 600, fontSize: "1rem", cursor: loading || !analysisData?.summary ? "not-allowed" : "pointer",
            boxShadow: loading || !analysisData?.summary ? "none" : "0 4px 12px rgba(16, 185, 129, 0.3)",
            whiteSpace: "nowrap"
          }}
        >
          {loading ? <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Activity size={18} /></motion.div> : <Bot size={18} />}
          {loading ? "Analyzing..." : (query.trim() ? "Ask Copilot" : "Generate Action Plan")}
        </button>
      </div>
    </div>
  );
}

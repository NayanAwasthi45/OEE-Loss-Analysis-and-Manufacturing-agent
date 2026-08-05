import React, { useState } from "react";
import { motion } from "framer-motion";
import { Play, Activity, Settings, CheckCircle, Search, AlertCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ScenarioDashboard({ analysisProps }) {
  const { data } = analysisProps;
  
  const [activeScenario, setActiveScenario] = useState("availability");
  
  // Independent improvement states
  const [availPct, setAvailPct] = useState(10);
  const [perfPct, setPerfPct] = useState(5);
  const [qualPct, setQualPct] = useState(4);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const analysisData = data;

  const runSimulation = async () => {
    if (!analysisData || !analysisData.summary) {
      setError("No base data found. Please run an OEE Analytics query first.");
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);

    let mode = "";
    let text = "";

    if (activeScenario === "compare_all") {
      mode = `simulate:compare_all:${availPct}:${perfPct}:${qualPct}`;
      text = `Simulate Availability (+${availPct}%), Performance (+${perfPct}%), and Quality (+${qualPct}%) simultaneously.`;
    } else {
      const pct = activeScenario === "availability" ? availPct : activeScenario === "performance" ? perfPct : qualPct;
      mode = `simulate:${activeScenario}:${pct}`;
      text = `Run ${activeScenario} scenario simulation with +${pct}% improvement.`;
    }

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
          session_id: "dashboard-sim",
          message: text,
          mode: mode,
          analytics_context: analyticsContext
        }),
      });

      if (!res.ok) throw new Error("Simulation failed");
      const data = await res.json();
      setResult(data.reply);
    } catch (err) {
      setError("Failed to run simulation. Please ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "32px", maxWidth: "1200px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: "1.8rem", fontWeight: 700, margin: "0 0 8px 0", color: "var(--text-primary)" }}>Scenario Simulations</h1>
          <p style={{ color: "var(--text-muted)", margin: 0 }}>Model operational improvements and project their financial impact.</p>
        </div>
      </div>

      {!analysisData?.summary && (
        <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid var(--accent-amber)", padding: "16px", borderRadius: "8px", display: "flex", gap: "12px", color: "var(--accent-amber)" }}>
          <AlertCircle />
          <span>You need to load data in the OEE Analytics dashboard first before running a simulation.</span>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px" }}>
        {/* Controls Sidebar */}
        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "20px", display: "flex", flexDirection: "column", gap: "20px", height: "fit-content" }}>
          
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "12px" }}>Select Scenario</label>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {[
                { id: "availability", label: "Availability (+Uptime)", icon: Activity },
                { id: "performance", label: "Performance (+Speed)", icon: Settings },
                { id: "quality", label: "Quality (+Yield)", icon: CheckCircle },
                { id: "compare_all", label: "Compare All", icon: Search }
              ].map(opt => (
                <button
                  key={opt.id}
                  onClick={() => setActiveScenario(opt.id)}
                  style={{
                    display: "flex", alignItems: "center", gap: "12px",
                    padding: "12px", borderRadius: "8px",
                    background: activeScenario === opt.id ? (opt.id === "compare_all" ? "linear-gradient(135deg, var(--accent-rose), var(--accent-amber))" : "var(--bg-primary)") : "transparent",
                    border: `1px solid ${activeScenario === opt.id ? (opt.id === "compare_all" ? "transparent" : "var(--accent-brand)") : "var(--border-color)"}`,
                    color: activeScenario === opt.id ? (opt.id === "compare_all" ? "white" : "var(--accent-brand)") : "var(--text-secondary)",
                    cursor: "pointer", transition: "all 0.2s",
                    fontWeight: activeScenario === opt.id ? 700 : 600
                  }}
                >
                  <opt.icon size={18} />
                  <span>{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div style={{ background: "var(--bg-primary)", padding: "16px", borderRadius: "12px", border: "1px solid var(--border-color)", display: "flex", flexDirection: "column", gap: "16px" }}>
            {activeScenario === "compare_all" ? (
              <>
                <SliderControl label="Availability" pct={availPct} setPct={setAvailPct} color="var(--accent-emerald)" />
                <SliderControl label="Performance" pct={perfPct} setPct={setPerfPct} color="var(--accent-amber)" />
                <SliderControl label="Quality" pct={qualPct} setPct={setQualPct} color="var(--accent-brand)" />
              </>
            ) : (
              <SliderControl 
                label={activeScenario.charAt(0).toUpperCase() + activeScenario.slice(1)} 
                pct={activeScenario === "availability" ? availPct : activeScenario === "performance" ? perfPct : qualPct} 
                setPct={activeScenario === "availability" ? setAvailPct : activeScenario === "performance" ? setPerfPct : setQualPct} 
                color="var(--accent-brand)" 
              />
            )}
          </div>

          <button
            onClick={runSimulation}
            disabled={loading || !analysisData?.summary}
            style={{
              display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
              padding: "12px", borderRadius: "8px", border: "none",
              background: loading || !analysisData?.summary ? "var(--border-color)" : "var(--accent-brand)",
              color: "white", fontWeight: 600, cursor: loading || !analysisData?.summary ? "not-allowed" : "pointer"
            }}
          >
            {loading ? <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Search size={18} /></motion.div> : <Play size={18} />}
            {loading ? "Simulating..." : "Run Simulation"}
          </button>
        </div>

        {/* Results Area */}
        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "32px", minHeight: "500px" }}>
          {error && <div style={{ color: "var(--accent-rose)", marginBottom: "16px" }}>{error}</div>}
          
          {!result && !loading && !error && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)", gap: "12px" }}>
              <Activity size={48} opacity={0.5} />
              <p>Configure and run a simulation to project business impact.</p>
            </div>
          )}

          {loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--accent-brand)", gap: "16px" }}>
              <motion.div animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 1.5 }}>
                <Search size={48} />
              </motion.div>
              <p style={{ fontWeight: 600 }}>Crunching OEE Scenario Math...</p>
            </div>
          )}

          {result && !loading && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="markdown-body" style={{ color: "var(--text-primary)", lineHeight: 1.6 }}>
              <ReactMarkdown
                components={{
                  h2: ({node, ...props}) => <h2 style={{ background: "linear-gradient(90deg, rgba(37,99,235,0.1), transparent)", padding: "12px 16px", borderRadius: "8px", borderLeft: "4px solid var(--accent-brand)", marginTop: "24px", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "8px" }} {...props} />,
                  h3: ({node, ...props}) => <h3 style={{ color: "var(--text-primary)", marginTop: "20px", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }} {...props} />,
                  p: ({node, ...props}) => <p style={{ color: "var(--text-secondary)", margin: "8px 0" }} {...props} />,
                  ul: ({node, ...props}) => <ul style={{ background: "var(--bg-card)", padding: "16px 16px 16px 32px", borderRadius: "8px", border: "1px solid var(--border-color)", margin: "12px 0" }} {...props} />,
                  strong: ({node, ...props}) => <strong style={{ color: "var(--text-primary)", fontWeight: 700 }} {...props} />
                }}
              >
                {result}
              </ReactMarkdown>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

function SliderControl({ label, pct, setPct, color }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
        <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)" }}>{label} Target</label>
        <div style={{ display: "flex", alignItems: "center", background: "var(--bg-secondary)", padding: "4px 8px", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginRight: "2px" }}>+</span>
          <input 
            type="number" min="1" max="50" 
            value={pct} onChange={(e) => setPct(e.target.value)}
            style={{ width: "36px", border: "none", background: "transparent", color: "var(--text-primary)", fontWeight: 700, fontSize: "0.9rem", textAlign: "right", outline: "none" }}
          />
          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginLeft: "2px" }}>%</span>
        </div>
      </div>
      <input 
        type="range" min="1" max="20" step="1"
        value={pct} onChange={(e) => setPct(e.target.value)}
        style={{ width: "100%", accentColor: color }}
      />
    </div>
  );
}

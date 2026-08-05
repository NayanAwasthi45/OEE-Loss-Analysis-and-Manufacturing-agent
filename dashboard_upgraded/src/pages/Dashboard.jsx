import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search, Gauge, ArrowUpDown, ShieldCheck, TrendingUp,
  DollarSign, Lightbulb, BarChart3, FileText,
} from "lucide-react";

import DashboardShell from "../components/layout/DashboardShell";
import KpiCard from "../components/cards/KpiCard";
import AiInsightPanel from "../components/cards/AiInsightPanel";
import BusinessImpactCard from "../components/cards/BusinessImpactCard";
import PlaceholderCard from "../components/cards/PlaceholderCard";
import OeeRadialGauge from "../components/charts/OeeRadialGauge";
import PillarProgressBars from "../components/charts/PillarProgressBars";
import OeeTrendChart from "../components/charts/OeeTrendChart";
import SixBigLossDonut from "../components/charts/SixBigLossDonut";
import DominantLossBar from "../components/charts/DominantLossBar";
import AiValidationPie from "../components/charts/AiValidationPie";
import ProductionTable from "../components/tables/ProductionTable";
import BusinessImpactTable from "../components/tables/BusinessImpactTable";
import FloatingChatbot from "../components/chat/FloatingChatbot";
import { useAnalysis } from "../hooks/useAnalysis";
import { fetchMachines, fetchPlants, fetchLines, fetchShifts } from "../services/api";

export default function Dashboard({ analysisProps }) {
  const [query, setQuery] = useState("");
  const [plant, setPlant] = useState("");
  const [line, setLine] = useState("");
  const [machine, setMachine] = useState("");
  const [shift, setShift] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [plantsOptions, setPlantsOptions] = useState([]);
  const [linesOptions, setLinesOptions] = useState([]);
  const [machinesOptions, setMachinesOptions] = useState([]);
  const [shiftsOptions, setShiftsOptions] = useState([]);

  const { data, loading, error, analyze } = analysisProps;
  
  const [loadingStep, setLoadingStep] = useState(0);

  useEffect(() => {
    let interval;
    if (loading) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 800);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const loadingMessages = [
    "Connecting to Manufacturing Database...",
    "Fetching Production Records...",
    "Calculating OEE Metrics...",
    "Analyzing Downtime...",
    "Generating AI Insights..."
  ];

  useEffect(() => {
    fetchPlants().then(setPlantsOptions).catch(() => {});
    fetchShifts().then(setShiftsOptions).catch(() => {});
  }, []);

  useEffect(() => {
    fetchLines(plant || null).then(setLinesOptions).catch(() => {});
    setLine(""); // reset line on plant change
  }, [plant]);

  useEffect(() => {
    fetchMachines(line || null, plant || null).then(setMachinesOptions).catch(() => {});
    setMachine(""); // reset machine on line change
  }, [line, plant]);

  const handleSubmit = (e) => {
    e.preventDefault();
    analyze({
      query,
      plant: plant || null,
      line: line || null,
      machine: machine || null,
      shift: shift || null,
      from_date: fromDate || null,
      to_date: toDate || null,
    });
  };

  const summary = data?.summary;
  const records = data?.records;
  const lossDist = data?.loss_distribution || {};
  const aiStats = data?.ai_stats || null;
  const aiDist = data?.ai_distribution || {};

  // Financial Aggregations
  const totalBusinessLoss = records?.reduce((sum, r) => sum + (r["Estimated Business Loss"] || 0), 0) || 0;
  const totalAvailabilityLoss = records?.reduce((sum, r) => sum + (r["Downtime Cost"] || 0), 0) || 0;
  const totalPerformanceLoss = records?.reduce((sum, r) => sum + (r["Production Loss Cost"] || 0), 0) || 0;
  const totalQualityLoss = records?.reduce((sum, r) => sum + (r["Scrap Cost"] || 0), 0) || 0;

  return (
    <DashboardShell>
      {/* ── Hero Query Section ──────────────────────── */}
      {/* ── Hero Search & Filter Section ──────────────────────── */}
      <div style={{ gridColumn: "1 / -1", marginBottom: "8px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.02em", marginBottom: "6px" }}>
              Manufacturing Performance Overview
            </h1>
            <p style={{ fontSize: "0.95rem", color: "var(--text-muted)", fontWeight: 500 }}>
              Query any machine or shift to pull live OEE metrics, loss drivers, and AI-validated insights.
            </p>
          </div>
          
          {data && !loading && (
            <div style={{ display: "flex", gap: "10px" }}>
              <button onClick={() => window.print()} style={{ display: "flex", alignItems: "center", gap: "6px", padding: "8px 16px", borderRadius: "8px", border: "1px solid var(--border-color)", background: "var(--bg-card)", color: "var(--text-secondary)", fontWeight: 600, fontSize: "0.85rem", cursor: "pointer", boxShadow: "var(--shadow-card)" }}>
                <FileText size={14} /> Export PDF
              </button>
            </div>
          )}
        </div>

        <motion.div
          className="card"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}
        >
          {/* Top Row: Search + Analyze Button */}
          <form onSubmit={handleSubmit} style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <div style={{ flex: 1, position: "relative" }}>
              <Search size={20} style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "var(--accent-rose)" }} />
              <input
                className="query-input"
                style={{ 
                  paddingLeft: "48px", 
                  paddingTop: "14px", 
                  paddingBottom: "14px", 
                  fontSize: "1.05rem",
                  background: "var(--bg-primary)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "12px",
                  width: "100%",
                  outline: "none",
                  transition: "border-color 0.2s, box-shadow 0.2s"
                }}
                placeholder="Ask anything about manufacturing... e.g. Show CNC_Milling_3 Night Shift"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                list="machine-list"
              />
              <datalist id="machine-list">
                {machinesOptions.map((m) => (
                  <option key={m} value={`Show ${m}`} />
                ))}
              </datalist>
            </div>
            <button
              type="submit"
              className="btn-analyze"
              disabled={loading || (!query.trim() && !plant && !line && !machine && !shift && !fromDate && !toDate)}
              style={{
                padding: "14px 32px",
                fontSize: "1.05rem",
                fontWeight: 600,
                borderRadius: "12px",
                background: "linear-gradient(135deg, var(--accent-rose), var(--accent-brand))",
                color: "white",
                border: "none",
                cursor: "pointer",
                boxShadow: "var(--shadow-glow)",
                transition: "transform 0.2s, box-shadow 0.2s"
              }}
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </form>

          {/* Bottom Row: Dropdown Filters */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "center" }}>
            <select className="query-input" style={{ flex: "1 1 140px", padding: "10px 14px", fontSize: "0.85rem", borderRadius: "8px" }} value={plant} onChange={(e) => setPlant(e.target.value)}>
              <option value="">Plant ▼</option>
              {plantsOptions.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select className="query-input" style={{ flex: "1 1 140px", padding: "10px 14px", fontSize: "0.85rem", borderRadius: "8px" }} value={line} onChange={(e) => setLine(e.target.value)}>
              <option value="">Line ▼</option>
              {linesOptions.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
            <select className="query-input" style={{ flex: "1 1 140px", padding: "10px 14px", fontSize: "0.85rem", borderRadius: "8px" }} value={machine} onChange={(e) => setMachine(e.target.value)}>
              <option value="">Machine ▼</option>
              {machinesOptions.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <select className="query-input" style={{ flex: "1 1 140px", padding: "10px 14px", fontSize: "0.85rem", borderRadius: "8px" }} value={shift} onChange={(e) => setShift(e.target.value)}>
              <option value="">Shift ▼</option>
              {shiftsOptions.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            
            <div style={{ display: "flex", flex: "2 1 280px", gap: "8px", alignItems: "center" }}>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 500, flexShrink: 0 }}>Date Range:</span>
              <input type="date" className="query-input" style={{ padding: "10px 14px", fontSize: "0.85rem", borderRadius: "8px", flex: 1 }} value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
              <span style={{ color: "var(--text-muted)" }}>-</span>
              <input type="date" className="query-input" style={{ padding: "10px 14px", fontSize: "0.85rem", borderRadius: "8px", flex: 1 }} value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </div>
          </div>
        </motion.div>

        {/* Quick Action Chips */}
        <div style={{ display: "flex", gap: "10px", marginTop: "16px", flexWrap: "wrap" }}>
          {["Today's OEE", "Machine Health", "Downtime Analysis", "Production Summary", "Compare Shifts", "Top Losses"].map((action) => (
            <button
              key={action}
              onClick={() => setQuery(`Show me ${action.toLowerCase()}`)}
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
                padding: "6px 14px",
                borderRadius: "20px",
                fontSize: "0.8rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                cursor: "pointer",
                transition: "all 0.2s ease",
                boxShadow: "0 1px 2px rgba(0,0,0,0.05)"
              }}
              onMouseOver={(e) => e.currentTarget.style.borderColor = "var(--accent-rose)"}
              onMouseOut={(e) => e.currentTarget.style.borderColor = "var(--border-color)"}
            >
              {action}
            </button>
          ))}
        </div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              marginTop: "12px",
              padding: "12px 16px",
              background: "rgba(244, 63, 94, 0.1)",
              border: "1px solid rgba(244, 63, 94, 0.3)",
              borderRadius: "var(--radius)",
              color: "#f43f5e",
              fontSize: "0.85rem",
            }}
          >
            {error}
          </motion.div>
        )}
      </div>

      {/* ── Loading Sequence ───────────────────────── */}
      {loading && !data && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card"
          style={{ gridColumn: "1 / -1", padding: "40px", display: "flex", flexDirection: "column", gap: "24px", alignItems: "center" }}
        >
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {loadingMessages[loadingStep]}
          </div>
          
          <div style={{ width: "100%", maxWidth: "400px", height: "6px", background: "var(--bg-primary)", borderRadius: "3px", overflow: "hidden" }}>
            <motion.div
              initial={{ width: "0%" }}
              animate={{ width: `${(loadingStep + 1) * 20}%` }}
              transition={{ duration: 0.5 }}
              style={{ height: "100%", background: "linear-gradient(90deg, var(--accent-rose), var(--accent-brand))", borderRadius: "3px" }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px", width: "100%", maxWidth: "400px" }}>
            {loadingMessages.map((msg, idx) => (
              <div key={idx} style={{ display: "flex", alignItems: "center", gap: "12px", opacity: loadingStep >= idx ? 1 : 0.4 }}>
                <div style={{ 
                  width: "24px", height: "24px", borderRadius: "50%", 
                  background: loadingStep > idx ? "var(--accent-emerald)" : loadingStep === idx ? "var(--accent-rose)" : "var(--bg-primary)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "white", fontSize: "12px", border: loadingStep >= idx ? "none" : "1px solid var(--border-color)"
                }}>
                  {loadingStep > idx ? "✓" : (idx + 1)}
                </div>
                <span style={{ fontSize: "0.9rem", color: loadingStep >= idx ? "var(--text-primary)" : "var(--text-muted)", fontWeight: loadingStep === idx ? 600 : 400 }}>
                  {msg}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── KPI Summary Cards ──────────────────────── */}
      {summary && (
        <>
          <div
            style={{
              gridColumn: "1 / -1",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "16px",
            }}
          >
            <KpiCard title="Overall OEE" value={summary.avg_oee} icon={Gauge} subtitle={`${summary.records_count} records`} delay={0} />
            <KpiCard title="Availability" value={summary.avg_availability} icon={ArrowUpDown} delay={0.05} showProgress={true} />
            <KpiCard title="Performance" value={summary.avg_performance} icon={TrendingUp} delay={0.1} showProgress={true} />
            <KpiCard title="Quality" value={summary.avg_quality} icon={ShieldCheck} delay={0.15} showProgress={true} />
            {aiStats && (
              <motion.div
                className="card"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.2 }}
                style={{ padding: "20px", borderLeft: "3px solid var(--accent-violet)" }}
              >
                <div style={{ fontSize: "0.72rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-secondary)", marginBottom: "8px" }}>
                  AI Validation
                </div>
                <div style={{ display: "flex", gap: "12px", alignItems: "baseline" }}>
                  <span style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-emerald)" }}>
                    {aiDist?.["Verified"] || 0}
                  </span>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>verified</span>
                  <span style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-amber)" }}>
                    {(aiDist?.["Partially Verified"] || 0) + (aiDist?.["Mismatch"] || 0)}
                  </span>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>flagged</span>
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  Groq: {aiStats.response_time}s
                </div>
              </motion.div>
            )}
          </div>

          {/* ── Charts Row 1: Gauges + Trend ──────────── */}
          <div style={{ gridColumn: "1 / -1" }} className="section-label">
            <span className="bar" />
            <span className="title">Performance Overview</span>
            <span className="sub">OEE composition and trend across records</span>
          </div>
          <div
            style={{
              gridColumn: "1 / -1",
              display: "grid",
              gridTemplateColumns: "280px 1fr",
              gap: "20px",
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <OeeRadialGauge value={summary.avg_oee} />
              <PillarProgressBars
                availability={summary.avg_availability}
                performance={summary.avg_performance}
                quality={summary.avg_quality}
              />
            </div>
            <OeeTrendChart records={records} />
          </div>

          {/* ── Charts Row 2: Donut + Bar + Pie ────────── */}
          <div style={{ gridColumn: "1 / -1" }} className="section-label">
            <span className="bar" />
            <span className="title">Loss &amp; Root-Cause Analysis</span>
            <span className="sub">Where the six big losses are concentrated, and AI confidence in the data</span>
          </div>
          <div
            style={{
              gridColumn: "1 / -1",
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "20px",
            }}
          >
            <SixBigLossDonut lossDistribution={lossDist} />
            <DominantLossBar lossDistribution={lossDist} />
            <AiValidationPie aiDistribution={aiDist} />
          </div>

          {/* ── AI Intelligence Panel ──────────────────── */}
          <div style={{ gridColumn: "1 / -1" }}>
            <AiInsightPanel records={records} />
          </div>

          {/* ── Production Detail Table ─────────────────── */}
          <div style={{ gridColumn: "1 / -1" }} className="section-label">
            <span className="bar" />
            <span className="title">Production Records</span>
            <span className="sub">Row-level machine, shift, and business-impact detail</span>
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <ProductionTable records={records} />
          </div>

          {/* ── Financial Impact Summary ─────────────────── */}
          <div style={{ gridColumn: "1 / -1" }} className="section-label">
            <span className="bar" style={{ background: "var(--accent-rose)" }} />
            <span className="title">Aggregated Financial Loss</span>
            <span className="sub">Total business cost breakdown across Availability, Performance, and Quality</span>
          </div>
          <div
            style={{
              gridColumn: "1 / -1",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "16px",
              marginBottom: "24px"
            }}
          >
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="card" style={{ padding: "20px", borderTop: "4px solid var(--accent-rose)", display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ fontSize: "0.80rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>Total Business Loss</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)" }}>
                ₹{totalBusinessLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.05 }} className="card" style={{ padding: "20px", borderTop: "4px solid var(--accent-amber)", display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ fontSize: "0.80rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>Availability Loss</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)" }}>
                ₹{totalAvailabilityLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.1 }} className="card" style={{ padding: "20px", borderTop: "4px solid var(--accent-blue)", display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ fontSize: "0.80rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>Performance Loss</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)" }}>
                ₹{totalPerformanceLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.15 }} className="card" style={{ padding: "20px", borderTop: "4px solid var(--accent-emerald)", display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ fontSize: "0.80rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>Quality Loss</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)" }}>
                ₹{totalQualityLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </motion.div>
          </div>

          {/* ── Business Impact Detail Table ────────────── */}
          <BusinessImpactTable records={records} />
        </>
      )}

      {/* ── Empty State ────────────────────────────── */}
      {!data && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="card"
          style={{
            gridColumn: "1 / -1",
            textAlign: "center",
            padding: "80px 20px",
            border: "1px dashed var(--border-accent)",
            background: "var(--bg-card)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center"
          }}
        >
          <div
            style={{
              width: "80px",
              height: "80px",
              borderRadius: "20px",
              background: "linear-gradient(135deg, rgba(159, 28, 46, 0.1), rgba(37, 99, 235, 0.1))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "24px",
              boxShadow: "0 8px 16px rgba(0,0,0,0.04)"
            }}
          >
            <BarChart3 size={36} style={{ color: "var(--accent-rose)" }} />
          </div>
          <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: "12px", letterSpacing: "-0.02em" }}>
            Ready for Analysis
          </div>
          <div style={{ fontSize: "0.95rem", color: "var(--text-muted)", maxWidth: "480px", marginBottom: "32px", lineHeight: 1.5 }}>
            No data loaded yet. Enter a query or select a preset to analyze OEE metrics, identify loss drivers, and get actionable AI-powered insights.
          </div>
          
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "center" }}>
            <button
              onClick={() => { setQuery("Show me yesterday's OEE for all machines"); handleSubmit(new Event('submit')); }}
              className="btn-analyze"
              style={{
                background: "linear-gradient(135deg, var(--accent-rose), var(--accent-brand))",
                padding: "12px 24px",
                borderRadius: "12px",
                fontSize: "0.95rem",
                fontWeight: 600,
                color: "white",
                border: "none",
                cursor: "pointer",
                boxShadow: "var(--shadow-glow)"
              }}
            >
              Run Sample Analysis
            </button>
          </div>
        </motion.div>
      )}

      {/* ── RAG Floating Chatbot ─────────────────── */}
      <FloatingChatbot analysisData={data} />
    </DashboardShell>
  );
}

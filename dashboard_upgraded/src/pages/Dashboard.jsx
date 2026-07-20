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
import { useAnalysis } from "../hooks/useAnalysis";
import { fetchMachines } from "../services/api";

export default function Dashboard() {
  const [query, setQuery] = useState("");
  const [machines, setMachines] = useState([]);
  const { data, loading, error, analyze } = useAnalysis();

  useEffect(() => {
    fetchMachines()
      .then(setMachines)
      .catch(() => {});
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    analyze(query);
  };

  const summary = data?.summary;
  const records = data?.records;
  const aiDist = data?.ai_distribution;
  const lossDist = data?.loss_distribution;
  const aiStats = data?.ai_stats;

  return (
    <DashboardShell>
      {/* ── Hero Query Section ──────────────────────── */}
      <div style={{ gridColumn: "1 / -1" }}>
        <div style={{ marginBottom: "18px" }}>
          <h1
            style={{
              fontSize: "1.5rem",
              fontWeight: 800,
              color: "var(--text-primary)",
              letterSpacing: "-0.02em",
              marginBottom: "4px",
            }}
          >
            Manufacturing Performance Overview
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Query any machine or shift to pull live OEE metrics, loss drivers, and AI-validated insights.
          </p>
        </div>
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          style={{ display: "flex", gap: "12px", alignItems: "stretch" }}
        >
          <div style={{ flex: 1, position: "relative" }}>
            <Search
              size={16}
              style={{
                position: "absolute",
                left: "14px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            />
            <input
              className="query-input"
              style={{ paddingLeft: "40px" }}
              placeholder="Enter manufacturing query — e.g. Show CNC_Milling_3 Night Shift"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              list="machine-list"
            />
            <datalist id="machine-list">
              {machines.map((m) => (
                <option key={m} value={`Show ${m}`} />
              ))}
            </datalist>
          </div>
          <button
            type="submit"
            className="btn-analyze"
            disabled={loading || !query.trim()}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </motion.form>

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

      {/* ── Loading Skeleton ───────────────────────── */}
      {loading && !data && (
        <>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: "100px", borderRadius: "var(--radius)" }} />
          ))}
        </>
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
            <KpiCard title="Availability" value={summary.avg_availability} icon={ArrowUpDown} delay={0.05} />
            <KpiCard title="Performance" value={summary.avg_performance} icon={TrendingUp} delay={0.1} />
            <KpiCard title="Quality" value={summary.avg_quality} icon={ShieldCheck} delay={0.15} />
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

          {/* ── Business Impact Detail Table ────────────── */}
          <BusinessImpactTable records={records} />

          {/* ── Future Phase Placeholders ───────────────── */}
          <div style={{ gridColumn: "1 / -1" }} className="section-label">
            <span className="bar" />
            <span className="title">Roadmap</span>
            <span className="sub">What's shipping next in the intelligence layer</span>
          </div>
          <div
            style={{
              gridColumn: "1 / -1",
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "16px",
            }}
          >
            <BusinessImpactCard summary={summary} records={records} />
            <PlaceholderCard title="Recommendations" phase="Coming in Phase C" icon={Lightbulb} />
            <PlaceholderCard title="Scenario Simulation" phase="Coming in Phase C" icon={BarChart3} />
            <PlaceholderCard title="Manager Summary" phase="Coming in Phase C" icon={FileText} />
          </div>
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
            padding: "72px 20px",
            border: "1px dashed var(--border-accent)",
            background: "var(--bg-card)",
          }}
        >
          <div
            style={{
              width: "72px",
              height: "72px",
              borderRadius: "18px",
              background: "linear-gradient(135deg, rgba(217,45,60,0.1), rgba(37,99,235,0.08))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 20px",
            }}
          >
            <Gauge size={30} style={{ color: "var(--accent-rose)" }} />
          </div>
          <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
            Ready for Analysis
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: "420px", margin: "0 auto" }}>
            Enter a manufacturing query above to analyze OEE metrics, identify loss drivers, and get AI-powered insights.
          </div>
        </motion.div>
      )}
    </DashboardShell>
  );
}

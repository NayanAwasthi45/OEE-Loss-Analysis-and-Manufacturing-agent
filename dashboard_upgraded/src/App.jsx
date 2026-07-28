import { useState } from "react";
import Navbar from "./components/layout/Navbar";
import Dashboard from "./pages/Dashboard";
import ScenarioDashboard from "./pages/ScenarioDashboard";
import RecommendationDashboard from "./pages/RecommendationDashboard";
import { useAnalysis } from "./hooks/useAnalysis";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const analysisProps = useAnalysis();

  return (
    <div>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div style={{ display: activeTab === "dashboard" ? "block" : "none" }}>
        <Dashboard analysisProps={analysisProps} />
      </div>
      <div style={{ display: activeTab === "scenarios" ? "block" : "none" }}>
        <ScenarioDashboard analysisProps={analysisProps} />
      </div>
      <div style={{ display: activeTab === "recommendations" ? "block" : "none" }}>
        <RecommendationDashboard analysisProps={analysisProps} />
      </div>
    </div>
  );
}

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
      {activeTab === "dashboard" ? (
        <Dashboard analysisProps={analysisProps} />
      ) : activeTab === "scenarios" ? (
        <ScenarioDashboard analysisProps={analysisProps} />
      ) : (
        <RecommendationDashboard analysisProps={analysisProps} />
      )}
    </div>
  );
}

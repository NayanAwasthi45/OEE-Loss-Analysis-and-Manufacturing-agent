import { useState, useEffect } from "react";
import Navbar from "./components/layout/Navbar";
import Dashboard from "./pages/Dashboard";
import ScenarioDashboard from "./pages/ScenarioDashboard";
import RecommendationDashboard from "./pages/RecommendationDashboard";
import Login from "./pages/Login";
import { useAnalysis } from "./hooks/useAnalysis";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const analysisProps = useAnalysis();

  const addNotification = (message) => {
    setNotifications(prev => [{ id: Date.now(), message, time: new Date() }, ...prev]);
  };

  useEffect(() => {
    const token = localStorage.getItem("oee_token");
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = (token) => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("oee_token");
    window.location.href = "/";
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} notifications={notifications} />
      <div style={{ display: activeTab === "dashboard" ? "block" : "none" }}>
        <Dashboard analysisProps={analysisProps} onAddNotification={addNotification} />
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

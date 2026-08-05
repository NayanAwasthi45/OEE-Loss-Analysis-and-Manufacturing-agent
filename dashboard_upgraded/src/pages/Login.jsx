import React, { useState } from "react";
import { motion } from "framer-motion";
import { Lock, User, Key, LogIn, AlertCircle } from "lucide-react";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData
      });

      if (!res.ok) {
        let errorMsg = "Invalid username or password";
        try {
          const errData = await res.json();
          if (errData.detail) errorMsg = errData.detail;
        } catch(e) {}
        throw new Error(errorMsg);
      }

      const data = await res.json();
      localStorage.setItem("oee_token", data.access_token);
      
      // Force a full page reload to ensure a perfectly clean state and avoid any React unmount race conditions or blank screens.
      window.location.href = "/";
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-shell)", padding: "20px" }}>
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: "var(--bg-card)",
          padding: "40px",
          borderRadius: "16px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.4)",
          width: "100%",
          maxWidth: "400px",
          border: "1px solid var(--border-color)"
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{ display: "inline-flex", background: "linear-gradient(135deg, var(--accent-rose), var(--accent-brand))", padding: "16px", borderRadius: "12px", marginBottom: "16px", boxShadow: "0 4px 12px rgba(159, 28, 46, 0.3)" }}>
            <Lock size={32} color="white" />
          </div>
          <h1 style={{ margin: "0 0 8px 0", fontSize: "1.8rem", color: "var(--text-primary)" }}>OEE Agent</h1>
          <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "0.9rem" }}>Enter your credentials to access the dashboard</p>
        </div>

        {error && (
          <div style={{ background: "rgba(244, 63, 94, 0.1)", border: "1px solid rgba(244, 63, 94, 0.3)", padding: "12px", borderRadius: "8px", display: "flex", alignItems: "center", gap: "8px", color: "var(--accent-rose)", marginBottom: "20px", fontSize: "0.85rem" }}>
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label style={{ display: "block", marginBottom: "8px", fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 600 }}>Username</label>
            <div style={{ position: "relative" }}>
              <User size={18} color="var(--text-muted)" style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)" }} />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="plant_user, production_user..."
                style={{ width: "100%", padding: "12px 12px 12px 40px", borderRadius: "8px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", outline: "none", fontSize: "0.95rem" }}
              />
            </div>
            <div style={{ marginTop: "6px", fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Valid users: plant_user, production_user, cli_user, op_ex_user
            </div>
          </div>

          <div>
            <label style={{ display: "block", marginBottom: "8px", fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 600 }}>Password</label>
            <div style={{ position: "relative" }}>
              <Key size={18} color="var(--text-muted)" style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)" }} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{ width: "100%", padding: "12px 12px 12px 40px", borderRadius: "8px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", outline: "none", fontSize: "0.95rem" }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: "12px",
              padding: "14px",
              borderRadius: "8px",
              border: "none",
              background: "linear-gradient(135deg, var(--accent-brand), var(--accent-rose))",
              color: "white",
              fontWeight: 600,
              fontSize: "1rem",
              cursor: loading ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              boxShadow: "0 4px 12px rgba(159, 28, 46, 0.3)"
            }}
          >
            {loading ? <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Activity size={18} /></motion.div> : <LogIn size={18} />}
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}

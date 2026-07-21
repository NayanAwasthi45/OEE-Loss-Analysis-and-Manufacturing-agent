import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, X, Send, Cpu, TrendingUp, BarChart3, HelpCircle, BookOpen, Activity, ArrowLeft, Zap, Target } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { v4 as uuidv4 } from "uuid";

export default function FloatingChatbot({ analysisData }) {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  
  const [messagesByMode, setMessagesByMode] = useState({
    general_chat: [],
    manufacturing_question: [],
    recommendation: [],
    simulation: []
  });
  
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Views: "home", "chat", "simulation_menu"
  const [view, setView] = useState("home");
  const [chatMode, setChatMode] = useState("general_chat");
  
  // Local state for Simulation Menu
  const [availPct, setAvailPct] = useState(10);
  const [perfPct, setPerfPct] = useState(5);
  const [qualPct, setQualPct] = useState(4);
  
  const messages = messagesByMode[chatMode] || [];
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, view]);

  const toggleChat = () => setIsOpen(!isOpen);

  const sendMessage = async (text, forceMode = null) => {
    const activeMode = forceMode || chatMode;
    let resolvedMode = chatMode;
    if (forceMode) {
      if (forceMode.startsWith("simulate:")) {
        resolvedMode = "simulation";
        setChatMode("simulation");
      } else {
        resolvedMode = forceMode;
        setChatMode(forceMode);
      }
    }
    
    if (!text.trim() && !forceMode) return;
    
    setView("chat");

    const isSimulation = activeMode && activeMode.startsWith("simulate:");
    const displayMessage = isSimulation ? `Run ${activeMode.split(":")[1]} scenario simulation.` : text;

    if (displayMessage) {
        setMessagesByMode(prev => ({
            ...prev,
            [resolvedMode]: [...(prev[resolvedMode] || []), { role: "user", content: displayMessage }]
        }));
    }
    
    setInput("");
    setLoading(true);

    try {
      let analyticsContext = null;
      // ONLY send analytics context if it's recommendation or simulation
      if ((activeMode === "recommendation" || activeMode.startsWith("simulate:")) && analysisData?.summary) {
        analyticsContext = {
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
      }

      const payloadMessage = text.trim() ? text : activeMode;

      const res = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: payloadMessage,
          mode: activeMode,
          analytics_context: analyticsContext
        }),
      });

      if (!res.ok) throw new Error("Failed to get response");
      const data = await res.json();
      
      setMessagesByMode(prev => ({
          ...prev,
          [resolvedMode]: [...(prev[resolvedMode] || []), { 
              role: "assistant", 
              content: data.reply,
              citations: data.citations
          }]
      }));
      
    } catch (error) {
      setMessagesByMode(prev => ({
          ...prev,
          [resolvedMode]: [...(prev[resolvedMode] || []), { 
              role: "assistant", 
              content: "Sorry, I encountered an error connecting to the Copilot. Please try again." 
          }]
      }));
    } finally {
      setLoading(false);
    }
  };


  const renderHome = () => {
    const hasData = !!analysisData?.summary;
    
    return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }} 
      animate={{ opacity: 1, x: 0 }} 
      exit={{ opacity: 0, x: 20 }}
      style={{ padding: "20px", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", width: "100%" }}
    >
      <div style={{ textAlign: "center", marginBottom: "24px" }}>
        <div style={{ fontSize: "2.5rem", marginBottom: "8px" }}>🤖</div>
        <h3 style={{ color: "var(--text-primary)", margin: "0 0 8px 0", fontSize: "1.2rem" }}>Manufacturing AI Copilot</h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", margin: 0 }}>
          I can analyze your dashboard, simulate scenarios, and answer questions using plant knowledge.
        </p>
      </div>

      <div style={{ display: "grid", gap: "12px" }}>
        <ActionCard 
          icon={<HelpCircle size={20} color="var(--text-muted)" />}
          title="General Assistant"
          desc="General questions and non-domain chat."
          onClick={() => { setChatMode("general_chat"); setView("chat"); }}
        />
        <ActionCard 
          icon={<BookOpen size={20} color="var(--accent-blue)" />}
          title="Manufacturing Knowledge Assistant"
          desc="Ask factual questions about SOPs, Manuals, and Guidelines."
          onClick={() => { setChatMode("manufacturing_question"); setView("chat"); }}
        />
        
        {/* Only enable Recommendation and Scenario Simulation if dashboard data is available */}
        <div style={{ opacity: hasData ? 1 : 0.5, pointerEvents: hasData ? "auto" : "none" }}>
          <ActionCard 
            icon={<TrendingUp size={20} color="var(--accent-emerald)" />}
            title="Recommendations"
            desc={hasData ? "Analyze current dashboard for actionable insights." : "Requires active dashboard analysis."}
            onClick={() => sendMessage("Generate recommendation based on current dashboard.", "recommendation")}
          />
        </div>
        <div style={{ opacity: hasData ? 1 : 0.5, pointerEvents: hasData ? "auto" : "none" }}>
          <ActionCard 
            icon={<BarChart3 size={20} color="var(--accent-amber)" />}
            title="Scenario Simulation"
            desc={hasData ? "Simulate KPI improvements and business impact." : "Requires active dashboard analysis."}
            onClick={() => setView("simulation_menu")}
          />
        </div>
      </div>
    </motion.div>
  )};

  const renderSimulationMenu = () => {
    return (
      <motion.div 
        initial={{ opacity: 0, x: 20 }} 
        animate={{ opacity: 1, x: 0 }} 
        exit={{ opacity: 0, x: -20 }}
        style={{ padding: "20px", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", width: "100%" }}
      >
        <button 
          onClick={() => setView("home")}
          style={{ background: "none", border: "none", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", marginBottom: "20px", padding: 0 }}
        >
          <ArrowLeft size={16} /> Back
        </button>
        
        <h3 style={{ color: "var(--text-primary)", margin: "0 0 8px 0", fontSize: "1.1rem" }}>📈 OEE Scenario Simulation</h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "20px" }}>
          Select an improvement strategy. The Copilot will project the impact on OEE, Business Loss and Savings using the latest dashboard analytics.
        </p>

        <div style={{ display: "grid", gap: "16px" }}>
          {/* Availability Card */}
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "16px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <div style={{ background: "rgba(16, 185, 129, 0.1)", padding: "6px", borderRadius: "8px" }}><Activity size={18} color="#10B981" /></div>
              <h4 style={{ margin: 0, color: "var(--text-primary)", fontSize: "0.95rem" }}>🟢 Availability Improvement</h4>
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "12px" }}>Focus: Reduce downtime, reduce breakdowns, optimize preventive maintenance</div>
            <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
              {[5, 10, 15].map(val => (
                <label key={val} style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "4px", color: "var(--text-primary)", cursor: "pointer" }}>
                  <input type="radio" name="avail" value={val} checked={availPct === val} onChange={() => setAvailPct(val)} />
                  +{val}%
                </label>
              ))}
            </div>
            <button 
              onClick={() => sendMessage("", `simulate:availability:${availPct}`)}
              style={{ width: "100%", padding: "8px", background: "var(--bg-shell)", border: "1px solid var(--border-color)", borderRadius: "8px", color: "var(--text-primary)", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem" }}>
              [ Run Simulation ]
            </button>
          </div>

          {/* Performance Card */}
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "16px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <div style={{ background: "rgba(245, 158, 11, 0.1)", padding: "6px", borderRadius: "8px" }}><Zap size={18} color="#F59E0B" /></div>
              <h4 style={{ margin: 0, color: "var(--text-primary)", fontSize: "0.95rem" }}>🟡 Performance Improvement</h4>
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "12px" }}>Focus: Reduce minor stops, optimize cycle time, increase operating speed</div>
            <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
              {[3, 5, 8].map(val => (
                <label key={val} style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "4px", color: "var(--text-primary)", cursor: "pointer" }}>
                  <input type="radio" name="perf" value={val} checked={perfPct === val} onChange={() => setPerfPct(val)} />
                  +{val}%
                </label>
              ))}
            </div>
            <button 
              onClick={() => sendMessage("", `simulate:performance:${perfPct}`)}
              style={{ width: "100%", padding: "8px", background: "var(--bg-shell)", border: "1px solid var(--border-color)", borderRadius: "8px", color: "var(--text-primary)", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem" }}>
              [ Run Simulation ]
            </button>
          </div>

          {/* Quality Card */}
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "16px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <div style={{ background: "rgba(59, 130, 246, 0.1)", padding: "6px", borderRadius: "8px" }}><Target size={18} color="#3B82F6" /></div>
              <h4 style={{ margin: 0, color: "var(--text-primary)", fontSize: "0.95rem" }}>🔵 Quality Improvement</h4>
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "12px" }}>Focus: Reduce scrap, reduce rework, improve first-pass yield</div>
            <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
              {[2, 4, 6].map(val => (
                <label key={val} style={{ fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "4px", color: "var(--text-primary)", cursor: "pointer" }}>
                  <input type="radio" name="qual" value={val} checked={qualPct === val} onChange={() => setQualPct(val)} />
                  +{val}%
                </label>
              ))}
            </div>
            <button 
              onClick={() => sendMessage("", `simulate:quality:${qualPct}`)}
              style={{ width: "100%", padding: "8px", background: "var(--bg-shell)", border: "1px solid var(--border-color)", borderRadius: "8px", color: "var(--text-primary)", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem" }}>
              [ Run Simulation ]
            </button>
          </div>
          
          {/* Compare All Scenarios */}
          <div style={{ background: "linear-gradient(to right, rgba(244,63,94,0.05), rgba(37,99,235,0.05))", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "16px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <div style={{ background: "rgba(139, 92, 246, 0.1)", padding: "6px", borderRadius: "8px" }}><BarChart3 size={18} color="#8B5CF6" /></div>
              <h4 style={{ margin: 0, color: "var(--text-primary)", fontSize: "0.95rem" }}>📊 Compare All Scenarios</h4>
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "16px" }}>Simulate Availability (+{availPct}%), Performance (+{perfPct}%), and Quality (+{qualPct}%) simultaneously to find the best impact.</div>
            <button 
              onClick={() => sendMessage("", `simulate:compare_all:${availPct}:${perfPct}:${qualPct}`)}
              style={{ width: "100%", padding: "8px", background: "linear-gradient(135deg, var(--accent-rose), var(--accent-amber))", border: "none", borderRadius: "8px", color: "white", cursor: "pointer", fontWeight: 700, fontSize: "0.85rem", boxShadow: "0 4px 10px rgba(244, 63, 94, 0.3)" }}>
              [ Run Comparison ]
            </button>
          </div>

        </div>
      </motion.div>
    );
  };

  return (
    <>
      <motion.button
        onClick={toggleChat}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        style={{
          position: "fixed", bottom: "30px", right: "30px", width: "60px", height: "60px", borderRadius: "30px",
          background: "linear-gradient(135deg, var(--accent-rose), var(--accent-amber))",
          color: "white", border: "none", boxShadow: "0 10px 25px rgba(244, 63, 94, 0.4)",
          display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", zIndex: 9999
        }}
      >
        {isOpen ? <X size={28} /> : <MessageSquare size={28} />}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            style={{
              position: "fixed", bottom: "100px", right: "30px", width: "420px", height: "650px",
              backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "16px",
              boxShadow: "0 15px 35px rgba(0,0,0,0.2)", display: "flex", flexDirection: "column", overflow: "hidden", zIndex: 9998
            }}
          >
            {/* Header */}
            <div style={{
              padding: "16px 20px", background: "linear-gradient(to right, rgba(244,63,94,0.1), rgba(37,99,235,0.05))",
              borderBottom: "1px solid var(--border-color)", display: "flex", alignItems: "center", gap: "12px", justifyContent: "space-between"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div style={{ background: "var(--accent-rose)", padding: "8px", borderRadius: "10px", color: "white" }}>
                  <Cpu size={20} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: "1rem", color: "var(--text-primary)", fontWeight: 700 }}>Enterprise Copilot</h3>
                  <span style={{ fontSize: "0.75rem", color: "var(--accent-emerald)", fontWeight: 600 }}>
                    ● {view === "home" ? "Select Module" : (
                      chatMode === "general_chat" ? "General Assistant" :
                      chatMode === "manufacturing_question" ? "Manufacturing Knowledge" :
                      chatMode === "recommendation" ? "Recommendations" : "Scenario Simulation"
                    )}
                  </span>
                </div>
              </div>
              {view !== "home" && (
                <button onClick={() => setView("home")} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.85rem" }}>
                  Home
                </button>
              )}
            </div>

            {/* Quick Tabs when in Chat View */}
            {view === "chat" && (
              <div style={{ display: "flex", borderBottom: "1px solid var(--border-color)", background: "var(--bg-shell)" }}>
                {[
                  { id: "general_chat", label: "General", icon: <HelpCircle size={14} /> },
                  { id: "manufacturing_question", label: "Knowledge", icon: <BookOpen size={14} /> },
                  { id: "recommendation", label: "Recommend", icon: <TrendingUp size={14} />, requiresData: true },
                  { id: "simulation", label: "Simulate", icon: <BarChart3 size={14} />, requiresData: true }
                ].map(tab => {
                  const hasData = !!analysisData?.summary;
                  const isDisabled = tab.requiresData && !hasData;
                  return (
                    <button
                      key={tab.id}
                      disabled={isDisabled}
                      onClick={() => {
                        if (tab.id === "simulation") setView("simulation_menu");
                        else setChatMode(tab.id);
                      }}
                      style={{
                        flex: 1, padding: "8px 0", border: "none", background: "none",
                        color: chatMode === tab.id ? "var(--accent-rose)" : "var(--text-muted)",
                        borderBottom: chatMode === tab.id ? "2px solid var(--accent-rose)" : "2px solid transparent",
                        display: "flex", flexDirection: "column", alignItems: "center", gap: "4px",
                        fontSize: "0.65rem", fontWeight: 600, cursor: isDisabled ? "not-allowed" : "pointer",
                        opacity: isDisabled ? 0.3 : 1
                      }}
                      title={isDisabled ? "Requires active dashboard analysis" : tab.label}
                    >
                      {tab.icon}
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Content Area */}
            <div style={{ flex: 1, overflowY: "hidden", display: "flex", flexDirection: "column", background: "var(--bg-shell)" }}>
              <AnimatePresence mode="wait">
                {view === "home" && <motion.div key="home" style={{ flex: 1, display: "flex", flexDirection: "column", width: "100%", overflow: "hidden" }}>{renderHome()}</motion.div>}
                {view === "simulation_menu" && <motion.div key="sim" style={{ flex: 1, display: "flex", flexDirection: "column", width: "100%", overflow: "hidden" }}>{renderSimulationMenu()}</motion.div>}
                {view === "chat" && (
                  <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ flex: 1, padding: "20px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
                    {messages.length === 0 && <div style={{ textAlign: "center", color: "var(--text-muted)", marginTop: "20px" }}>Start typing below to chat.</div>}
                    
                    {messages.map((msg, i) => (
                      <div key={i} style={{
                        alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                        maxWidth: "85%",
                        background: msg.role === "user" ? "rgba(244, 63, 94, 0.1)" : "var(--bg-card)",
                        border: msg.role === "user" ? "1px solid rgba(244, 63, 94, 0.2)" : "1px solid var(--border-color)",
                        padding: "16px", borderRadius: "12px",
                        borderBottomRightRadius: msg.role === "user" ? "2px" : "12px",
                        borderBottomLeftRadius: msg.role === "assistant" ? "2px" : "12px",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.05)"
                      }}>
                        <div className="markdown-body" style={{ fontSize: "0.9rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
                          {msg.role === "assistant" ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.content}
                        </div>
                        {msg.citations && msg.citations.length > 0 && (
                          <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid var(--border-color)" }}>
                            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, marginBottom: "6px", letterSpacing: "0.5px" }}>SOURCES</div>
                            {msg.citations.map((c, idx) => (
                              <span key={idx} style={{ display: "inline-flex", alignItems: "center", gap: "4px", padding: "4px 8px", background: "var(--bg-shell)", border: "1px solid var(--border-color)", borderRadius: "6px", fontSize: "0.7rem", marginRight: "6px", color: "var(--text-secondary)" }}>
                                📄 {c}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                    {loading && (
                      <div style={{ alignSelf: "flex-start", padding: "16px", background: "var(--bg-card)", borderRadius: "12px", border: "1px solid var(--border-color)" }}>
                        <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5 }} style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          Analyzing...
                        </motion.div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Input Area (Only visible in chat mode or home mode) */}
            {(view === "chat" || view === "home") && (
              <form 
                onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
                style={{ padding: "16px", borderTop: "1px solid var(--border-color)", background: "var(--bg-card)", display: "flex", gap: "10px" }}
              >
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question..."
                  style={{
                    flex: 1, padding: "12px 16px", borderRadius: "24px", border: "1px solid var(--border-color)",
                    background: "var(--bg-shell)", color: "var(--text-primary)", outline: "none", fontSize: "0.95rem"
                  }}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  style={{
                    background: input.trim() && !loading ? "var(--accent-rose)" : "var(--border-accent)",
                    color: "white", border: "none", borderRadius: "50%", width: "44px", height: "44px",
                    display: "flex", alignItems: "center", justifyContent: "center", cursor: input.trim() && !loading ? "pointer" : "not-allowed",
                    transition: "background 0.2s"
                  }}
                >
                  <Send size={18} style={{ marginLeft: "2px" }} />
                </button>
              </form>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Helper Component for the rich UI cards
function ActionCard({ icon, title, desc, onClick }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      style={{
        padding: "16px",
        background: "var(--bg-card)",
        border: "1px solid var(--border-color)",
        borderRadius: "12px",
        display: "flex",
        alignItems: "flex-start",
        gap: "16px",
        cursor: "pointer",
        boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
      }}
    >
      <div style={{
        background: "var(--bg-shell)",
        padding: "10px",
        borderRadius: "10px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}>
        {icon}
      </div>
      <div>
        <h4 style={{ margin: "0 0 4px 0", color: "var(--text-primary)", fontSize: "0.95rem" }}>{title}</h4>
        <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "0.8rem", lineHeight: 1.4 }}>{desc}</p>
      </div>
    </motion.div>
  );
}

export default function DashboardShell({ children }) {
  return (
    <div
      style={{
        minHeight: "calc(100vh - 56px)",
        background: "var(--bg-primary)",
      }}
    >
      <div className="dashboard-grid">{children}</div>
    </div>
  );
}

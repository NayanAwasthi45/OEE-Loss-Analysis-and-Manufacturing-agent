const API_BASE = "/api";

export async function fetchMachines() {
  const res = await fetch(`${API_BASE}/machines`);
  if (!res.ok) throw new Error("Failed to fetch machines");
  const data = await res.json();
  return data.machines;
}

export async function analyzeQuery(query) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed (${res.status})`);
  }
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("API unhealthy");
  return res.json();
}

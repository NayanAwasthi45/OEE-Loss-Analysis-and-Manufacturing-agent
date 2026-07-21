const API_BASE = "/api";

export async function fetchPlants() {
  const res = await fetch(`${API_BASE}/filters/plants`);
  if (!res.ok) throw new Error("Failed to fetch plants");
  const data = await res.json();
  return data.plants;
}

export async function fetchLines(plant = null) {
  const url = plant ? `${API_BASE}/filters/lines?plant=${encodeURIComponent(plant)}` : `${API_BASE}/filters/lines`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch lines");
  const data = await res.json();
  return data.lines;
}

export async function fetchShifts() {
  const res = await fetch(`${API_BASE}/filters/shifts`);
  if (!res.ok) throw new Error("Failed to fetch shifts");
  const data = await res.json();
  return data.shifts;
}

export async function fetchMachines(line = null, plant = null) {
  let url = `${API_BASE}/machines`;
  const params = new URLSearchParams();
  if (line) params.append("line", line);
  if (plant) params.append("plant", plant);
  
  if (params.toString()) {
    url += `?${params.toString()}`;
  }
  
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch machines");
  const data = await res.json();
  return data.machines;
}

export async function analyzeQuery(payload) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
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

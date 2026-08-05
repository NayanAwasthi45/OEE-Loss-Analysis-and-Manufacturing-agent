const API_BASE = "/api";

const getAuthHeader = () => {
  const token = localStorage.getItem("oee_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
};

export const fetchPlants = async () => {
  const res = await fetch(`${API_BASE}/filters/plants`, { headers: getAuthHeader() });
  if (!res.ok) throw new Error("Failed to fetch plants");
  const data = await res.json();
  return data.plants || [];
};

export const fetchLines = async (plant = null) => {
  const url = plant ? `${API_BASE}/filters/lines?plant=${encodeURIComponent(plant)}` : `${API_BASE}/filters/lines`;
  const res = await fetch(url, { headers: getAuthHeader() });
  if (!res.ok) throw new Error("Failed to fetch lines");
  const data = await res.json();
  return data.lines;
};

export const fetchShifts = async () => {
  const res = await fetch(`${API_BASE}/filters/shifts`, { headers: getAuthHeader() });
  if (!res.ok) throw new Error("Failed to fetch shifts");
  const data = await res.json();
  return data.shifts;
};

export const fetchMachines = async (line = null, plant = null) => {
  let url = `${API_BASE}/machines`;
  const params = new URLSearchParams();
  if (line) params.append("line", line);
  if (plant) params.append("plant", plant);
  
  if (params.toString()) {
    url += `?${params.toString()}`;
  }
  
  const res = await fetch(url, { headers: getAuthHeader() });
  if (!res.ok) throw new Error("Failed to fetch machines");
  const data = await res.json();
  return data.machines || [];
};

export async function analyzeQuery(payload) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      ...getAuthHeader()
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed (${res.status})`);
  }
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`, { headers: getAuthHeader() });
  if (!res.ok) throw new Error("API unhealthy");
  return res.json();
}

export async function createTicket(payload) {
  const res = await fetch(`${API_BASE}/tickets`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      ...getAuthHeader()
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create ticket");
  return res.json();
}

export async function fetchTickets() {
  const res = await fetch(`${API_BASE}/tickets`, { headers: getAuthHeader() });
  if (!res.ok) throw new Error("Failed to fetch tickets");
  const data = await res.json();
  return data.tickets || [];
}

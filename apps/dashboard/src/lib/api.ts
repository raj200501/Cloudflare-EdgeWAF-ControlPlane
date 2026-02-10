export type EventItem = {
  id: string;
  ts: number;
  decision: string;
  reason: string;
  ip: string;
  country: string;
  path: string;
  status_code: number;
  latency_ms: number;
  threat_type?: string;
};

const API = 'http://localhost:8000';

export async function fetchEvents(limit = 250): Promise<EventItem[]> {
  const res = await fetch(`${API}/api/events?limit=${limit}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.items ?? [];
}

export async function fetchWafPolicies() {
  const res = await fetch(`${API}/api/policies/waf`);
  return res.json();
}

export async function createWafRule(payload: Record<string, unknown>) {
  const res = await fetch(`${API}/api/policies/waf`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  return res.json();
}

export async function compileDeployment() {
  const res = await fetch(`${API}/api/deployments/compile`, { method: 'POST' });
  return res.json();
}

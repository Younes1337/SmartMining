// Use relative URL in production, absolute in development
const isProduction = process.env.NODE_ENV === 'production';
const API_BASE = isProduction ? '/api' : 'http://localhost:8000';

export async function fetchData() {
  const res = await fetch(`${API_BASE}/data`);
  if (!res.ok) throw new Error(`GET /data failed: ${res.status}`);
  return res.json();
}

export async function predict(payload) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = '';
    try { detail = await res.text(); } catch {}
    throw new Error(`POST /predict failed: ${res.status} ${detail}`);
  }
  return res.json();
}

export async function ingestFile(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/ingest`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    let detail = '';
    try { detail = await res.text(); } catch {}
    throw new Error(`POST /ingest failed: ${res.status} ${detail}`);
  }
  return res.json();
}
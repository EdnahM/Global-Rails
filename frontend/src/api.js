// Shared helper for calling Global Rails backend tools. Every surface that
// executes a tool — the AI Agent chat and the dedicated Market Data / Swap /
// Transfer / x402 pages — goes through this one function, so there's a
// single place that knows how to reach the backend (relative "/api/..." so
// it works via the Vite dev proxy locally and the Vercel rewrite in prod).
export async function callTool(name, payload) {
  const response = await fetch(`/api/tool/${name}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }

  return response.json();
}

// GET /api/tools — used by the Developer page to show the live tool catalog
// rather than a hardcoded list that can drift from what's actually deployed.
export async function listTools() {
  const response = await fetch("/api/tools");
  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }
  return response.json();
}

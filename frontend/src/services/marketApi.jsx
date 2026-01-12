// Replace this with your real backend route when ready.
// Expected return:
// { nifty: { price: number, pct: number }, sensex: { price: number, pct: number }, ts: number }

export async function getIndicesSnapshot() {
  // --- OPTION A: call your backend ---
  // const r = await fetch("/api/indices"); // e.g., your FastAPI endpoint
  // if (!r.ok) throw new Error("Failed");
  // return await r.json();

  // --- OPTION B: temporary mock (random walk) ---
  const baseNifty = 22500, baseSensex = 74500;
  const rnd = (b) => (b + (Math.random() - 0.5) * 60);
  const now = Date.now();
  const n = rnd(baseNifty);
  const s = rnd(baseSensex);
  // simulate +/- 0.00–0.50%
  const pctN = ((Math.random() - 0.5) * 1.0);
  const pctS = ((Math.random() - 0.5) * 1.0);

  return {
    nifty:  { price: Math.round(n), pct: +pctN.toFixed(2) },
    sensex: { price: Math.round(s), pct: +pctS.toFixed(2) },
    ts: now
  };
}

export async function askMarket(question){
  // TODO: call your LLM backend
  await wait(400);
  return { answer: `Market bot says: "${question}" → (demo answer)` };
}

export async function askPortfolio(question){
  await wait(400);
  return { answer: `Portfolio bot on your holdings: "${question}" → (demo answer)` };
}

export async function generateReport(){
  await wait(600);
  return {
    summary: "Your portfolio is moderately diversified with a tilt to large-cap growth.",
    metrics: [
      { label: "Total Value", value: "₹ 12,34,567" },
      { label: "1M Return", value: "+2.8%" },
      { label: "Risk (Vol.)", value: "Low" },
    ]
  };
}

function wait(ms){ return new Promise(r => setTimeout(r, ms)); }

import React from "react";
import { useMarket } from "../state/MarketProvider";

const Arrow = ({ up }) => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
    style={{ marginRight: 4, transform: up ? "rotate(0deg)" : "rotate(180deg)" }}>
    <path d="M12 4l7 8h-4v8H9v-8H5l7-8z" fill="currentColor" />
  </svg>
);

function Row({ label, value = 0, pct = 0 }) {
  const up = pct >= 0;
  const pctText = `${up ? "+" : ""}${pct.toFixed(2)}%`;
  return (
    <div className="ticker-row" title={`${label}: ${value.toLocaleString()} (${pctText})`}>
      <span className="ticker-label">{label}</span>
      <span className="ticker-value">{value.toLocaleString()}</span>
      <span className={`ticker-pct ${up ? "up" : "down"}`}><Arrow up={up} />{pctText}</span>
    </div>
  );
}

export default function IndexTicker() {
  const { data, error } = useMarket();

  if (!data && !error) {
    return (
      <div className="ticker-card" aria-busy="true">
        <div className="ticker-skeleton" />
        <div className="ticker-skeleton" />
        <div className="ticker-skeleton" />
      </div>
    );
  }

  return (
    <div className="ticker-card">
      <Row label="Nifty 50" value={data?.nifty?.price} pct={data?.nifty?.pct} />
      <Row label="Sensex" value={data?.sensex?.price} pct={data?.sensex?.pct} />
      <Row label="FinNifty" value={data?.fin?.price} pct={data?.fin?.pct} />
    </div>
  );
}

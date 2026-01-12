import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import { useAuth } from "../auth";
import { Navigate } from "react-router-dom";
import { getStockBuddy } from "../services/api";
import AI_Voice from "../components/AI_Voice";
import "../components/AI_Voice.css";

export default function StockBuddy() {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [showAll, setShowAll] = useState(false);

  // Streaming states
  const [visibleParamsCount, setVisibleParamsCount] = useState(0);
  const [typedRationale, setTypedRationale] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const SUGGESTIONS = [
    { name: "Reliance", symbol: "RELIANCE" },
    { name: "TCS", symbol: "TCS" },
    { name: "HDFC Bank", symbol: "HDFCBANK" },
    { name: "Infosys", symbol: "INFY" },
    { name: "NTPC Limited", symbol: "NTPC" },
    { name: "Adani Enterprises", symbol: "ADANIENT" }
  ];

  if (!user) return <Navigate to="/login" replace />;

  const performSearch = async (val) => {
    if (!val.trim()) return;
    setLoading(true);
    setError(null);
    setResponse(null);
    setShowAll(false);
    setVisibleParamsCount(0);
    setTypedRationale([]);

    try {
      const data = await getStockBuddy(val);
      setResponse(data);
      setLoading(false); // Stop main loading to show the structure

      // 1. Reveal parameters row-by-row (first 10)
      const count = data.stock_data_ui?.length || 0;
      const revealLimit = Math.min(count, 10);

      for (let i = 1; i <= revealLimit; i++) {
        await new Promise(r => setTimeout(r, 60));
        setVisibleParamsCount(i);
      }

      // 2. Type Rationale rationale
      if (data.recommendation?.["Investment Rationale"]) {
        setIsTyping(true);
        const rationales = data.recommendation["Investment Rationale"];
        for (let i = 0; i < rationales.length; i++) {
          const fullText = rationales[i];
          let currentText = "";
          // Add empty string to start typing this line
          setTypedRationale(prev => [...prev, ""]);

          for (let j = 0; j < fullText.length; j++) {
            currentText += fullText[j];
            const idx = i;
            setTypedRationale(prev => {
              const next = [...prev];
              next[idx] = currentText;
              return next;
            });
            await new Promise(r => setTimeout(r, 10));
          }
        }
        setIsTyping(false);
      }

    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    performSearch(query);
  };

  const handleSuggestion = (item) => {
    setQuery(item.name);
    performSearch(item.name);
  };

  const handleTranscript = (transcript) => {
    setQuery(transcript || "");
  };

  // Extract variables for easier rendering
  const stockDataUi = response?.stock_data_ui || [];
  const displayParams = showAll
    ? stockDataUi
    : stockDataUi.slice(0, visibleParamsCount);

  const hasMoreParams = stockDataUi.length > 10;
  const symbol = response?.symbol || "";
  const recommendation = response?.recommendation || null;

  return (
    <div className={`app-shell ${collapsed ? "collapsed" : ""}`}>
      <style>{`
        /* Fix the main container to fill available height and hide overflow */
        .main {
          height: calc(100vh - var(--topnav-h));
          overflow: hidden;
          background: #0d1117;
          display: flex;
          flex-direction: column;
        }

        /* The scrollable area for stock analysis content */
        .stock-buddy-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 8px 24px 40px;
          scroll-behavior: smooth;
        }

        .stock-buddy-container {
          max-width: 1000px;
          margin: 0 auto;
          width: 100%;
        }

        .stock-buddy-header {
          margin-bottom: 12px;
        }

        .stock-buddy-title {
          font-size: 1.5rem;
          font-weight: 700;
          background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 2px;
          letter-spacing: -0.5px;
        }

        .search-form {
          margin-bottom: 24px;
        }

        .search-input-wrapper {
          display: flex;
          gap: 10px;
          max-width: 800px;
          width: 100%;
          margin: 0 auto;
        }

        .search-input {
          flex: 1;
          padding: 8px 14px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 8px;
          color: #fff;
          font-size: 0.8rem;
          outline: none;
          transition: all 0.2s ease;
        }

        .search-input:focus {
          background: rgba(255, 255, 255, 0.05);
          border-color: #3b82f6;
          box-shadow: 0 0 15px rgba(59, 130, 246, 0.1);
        }

        .search-input::placeholder {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.2);
        }

        .suggestions-row {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 8px;
          animation: fadeIn 0.8s ease;
        }

        .suggestion-tag {
          padding: 4px 10px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 100px;
          color: rgba(255, 255, 255, 0.3);
          font-size: 0.7rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .suggestion-tag:hover {
          background: rgba(59, 130, 246, 0.05);
          border-color: rgba(59, 130, 246, 0.15);
          color: #3b82f6;
        }

        .search-button {
          padding: 0 18px;
          background: transparent;
          border: 1px solid #3b82f6;
          border-radius: 8px;
          color: #3b82f6;
          font-weight: 600;
          font-size: 0.8rem;
          height: 36px;
          display: flex;
          align-items: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .search-button:hover:not(:disabled) {
          background: rgba(59, 130, 246, 0.08);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }

        .search-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        /* Stock Data Cards */
        .data-section-title {
          font-size: 0.75rem;
          font-weight: 700;
          color: #475569;
          margin-bottom: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        /* Table format for stock details */
        .param-table-wrapper {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          overflow: hidden;
          margin-bottom: 32px;
        }

        .param-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.85rem;
        }

        .param-table tr {
          border-bottom: 1px solid rgba(255, 255, 255, 0.02);
          transition: background 0.2s ease;
        }

        .param-table tr:last-child {
          border-bottom: none;
        }

        .param-table tr:hover {
          background: rgba(255, 255, 255, 0.01);
        }

        .param-table td {
          padding: 10px 16px;
          color: rgba(255, 255, 255, 0.8);
          vertical-align: middle;
        }

        .param-table .key-td {
          color: rgba(255, 255, 255, 0.9);
          font-weight: 500;
          width: 25%;
        }

        .param-table .value-td {
          font-weight: 600;
          color: #fff;
          width: 20%;
          text-align: left;
        }

        .param-table .meaning-td {
          width: 55%;
        }

        .meaning-content {
          font-size: 0.78rem;
          color: rgba(255, 255, 255, 0.8);
          line-height: 1.6;
        }


        /* Highlights Row */
        .highlights-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          margin-bottom: 24px;
        }

        .highlight-card {
          padding: 24px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.04);
          border-radius: 16px;
          text-align: center;
        }

        /* Sentiment Bar condensed */
        .sentiment-bar-mini {
          height: 4px;
          background: rgba(255,255,255,0.05);
          border-radius: 100px;
          margin-bottom: 32px;
          display: flex;
          overflow: hidden;
        }

        /* Recommendation Panel */
        .recommendation-panel {
          margin-top: 24px;
          background: rgba(255, 255, 255, 0.01);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 20px;
          padding: 24px;
          animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .stat-card {
          padding: 14px 16px;
          border-radius: 14px;
          text-align: center;
          border: 1px solid rgba(255, 255, 255, 0.04);
          background: rgba(255, 255, 255, 0.02);
        }

        .stat-card.buy { border-top: 3px solid #10b981; }
        .stat-card.hold { border-top: 3px solid #f59e0b; }
        .stat-card.sell { border-top: 3px solid #ef4444; }

        .stat-label { 
          font-size: 0.65rem; 
          font-weight: 700; 
          margin-bottom: 6px; 
          display: block;
          letter-spacing: 0.08em;
        }
        
        .buy .stat-label { color: #10b981; }
        .hold .stat-label { color: #f59e0b; }
        .sell .stat-label { color: #ef4444; }

        .stat-value { font-size: 1.5rem; font-weight: 800; color: #fff; }

        .sentiment-segment { height: 100%; transition: width 1s ease-out; }
        .segment-buy { background: #10b981; }
        .segment-hold { background: #f59e0b; }
        .segment-sell { background: #ef4444; }

        .rationale-list {
          list-style: none;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .rationale-item {
          background: rgba(255, 255, 255, 0.02);
          padding: 12px 20px;
          border-radius: 12px;
          border: 1px solid rgba(255, 255, 255, 0.03);
          color: rgba(255, 255, 255, 0.65);
          line-height: 1.6;
          font-size: 0.82rem;
        }

        .view-more-container {
          text-align: center;
          margin-top: 16px;
        }

        .view-more-btn {
          background: transparent;
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.5);
          padding: 12px 28px;
          border-radius: 100px;
          cursor: pointer;
          font-size: 0.8rem;
          font-weight: 600;
          transition: all 0.2s ease;
        }

        .view-more-btn:hover {
          background: rgba(255, 255, 255, 0.04);
          border-color: #3b82f6;
          color: #fff;
        }

        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid rgba(59, 130, 246, 0.1);
            border-left-color: #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        .loading-ring {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 80px 0;
            width: 100%;
        }

        /* AI Voice Theme Override */
        .search-input-wrapper {
          --ai-voice-color: #3b82f6;
          --ai-voice-hover-bg: rgba(59, 130, 246, 0.1);
          --ai-voice-active-color: #3b82f6;
          --ai-voice-active-bg: rgba(59, 130, 246, 0.15);
          --ai-voice-wave-color: #3b82f6;
          --tooltip-bg: #3b82f6;
        }
      `}</style>

      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((x) => !x)} />

      <section className="main">
        <div className="stock-buddy-scroll">
          <div className="stock-buddy-container">
            <div className={`stock-buddy-header ${!response && !loading ? 'centered' : ''}`} style={{
              textAlign: !response && !loading ? "center" : "left",
              marginTop: !response && !loading ? "4vh" : "0",
              transition: "all 0.5s ease"
            }}>
              <h1 className="stock-buddy-title">Stock Score</h1>
              <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "0.95rem" }}>
                Enter any stock. Get complete analysis instantly.
              </p>
            </div>

            <form onSubmit={handleSearch} className="search-form">
              <div className="search-input-wrapper">
                <input
                  className="search-input"
                  placeholder="Enter stock name or symbol (e.g., TCS, RELIANCE, INFY)..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={loading}
                />
                <div style={{ alignSelf: 'center', display: 'flex', alignItems: 'center' }}>
                  <AI_Voice
                    variant="button"
                    disabled={loading}
                    onTranscript={handleTranscript}
                  />
                </div>
                <button className="search-button" type="submit" disabled={loading}>
                  {loading ? "Analyzing..." : "Analyze"}
                </button>
              </div>

              {!response && !loading && (
                <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div className="data-section-title" style={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.7rem', marginBottom: '8px' }}>
                    Trending Analysis
                  </div>
                  <div className="suggestions-row" style={{ marginTop: '8px', justifyContent: 'center' }}>
                    {SUGGESTIONS.map(item => (
                      <span key={item.symbol} className="suggestion-tag" onClick={() => handleSuggestion(item)}>
                        {item.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </form>

            {loading && (
              <div className="loading-ring">
                <div className="spinner"></div>
              </div>
            )}

            {error && (
              <div style={{
                padding: "16px 20px",
                background: "rgba(255,107,107,0.08)",
                color: "#ff6b6b",
                borderRadius: "12px",
                border: "1px solid rgba(255,107,107,0.15)",
                fontSize: "0.9rem",
                marginBottom: "24px",
                display: "flex",
                alignItems: "center",
                gap: "10px"
              }}>
                {error}
              </div>
            )}

            {response && !loading && (
              <>
                {recommendation && (
                  <div className="highlights-row">
                    <div className="stat-card buy">
                      <span className="stat-label">BUY</span>
                      <div className="stat-value">{recommendation.Buy}</div>
                    </div>
                    <div className="stat-card hold" style={{ animationDelay: '0.1s' }}>
                      <span className="stat-label">HOLD</span>
                      <div className="stat-value">{recommendation.Hold}</div>
                    </div>
                    <div className="stat-card sell" style={{ animationDelay: '0.2s' }}>
                      <span className="stat-label">SELL</span>
                      <div className="stat-value">{recommendation.Sell}</div>
                    </div>
                  </div>
                )}

                <div className="data-section-title">
                  Stock Details
                </div>

                <div className="param-table-wrapper">
                  <table className="param-table">
                    <thead>
                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.01)' }}>
                        <th style={{ textAlign: 'left', padding: '12px 16px', color: 'rgba(255,255,255,0.3)', fontSize: '0.7rem' }}>PARAMETER</th>
                        <th style={{ textAlign: 'left', padding: '12px 16px', color: 'rgba(255,255,255,0.3)', fontSize: '0.7rem' }}>VALUE</th>
                        <th style={{ textAlign: 'left', padding: '12px 16px', color: 'rgba(255,255,255,0.3)', fontSize: '0.7rem' }}>MEANING</th>
                      </tr>
                    </thead>
                    <tbody>
                      {displayParams.map((item, idx) => {
                        const isLegacy = Array.isArray(item);
                        const key = isLegacy ? item[0] : item.parameter;
                        const value = isLegacy ? item[1] : item.value;
                        const meaning = isLegacy ? "" : item.meaning;

                        return (
                          <tr key={key || idx}>
                            <td className="key-td">{key}</td>
                            <td className="value-td">{String(value)}</td>
                            <td className="meaning-td">
                              {meaning && (
                                <div className="meaning-content">{meaning}</div>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {hasMoreParams && visibleParamsCount >= 10 && (
                  <div className="view-more-container" style={{ marginBottom: '24px' }}>
                    <button className="view-more-btn" onClick={() => setShowAll(!showAll)}>
                      {showAll ? "Hide Details" : "View All Parameters"}
                    </button>
                  </div>
                )}

                {recommendation && (
                  <div className="recommendation-panel" style={{ marginTop: '0px' }}>
                    {/* Sentiment Visual Bar */}
                    <div className="sentiment-bar-mini">
                      {(() => {
                        const total = (recommendation.Buy || 0) + (recommendation.Hold || 0) + (recommendation.Sell || 0);
                        if (total === 0) return null;
                        return (
                          <>
                            <div className="sentiment-segment segment-buy" style={{ width: `${(recommendation.Buy / total) * 100}%` }} />
                            <div className="sentiment-segment segment-hold" style={{ width: `${(recommendation.Hold / total) * 100}%` }} />
                            <div className="sentiment-segment segment-sell" style={{ width: `${(recommendation.Sell / total) * 100}%` }} />
                          </>
                        );
                      })()}
                    </div>

                    <div className="data-section-title" style={{ marginTop: '24px' }}>
                      Investment Rationale
                    </div>
                    <ul className="rationale-list">
                      {typedRationale.map((text, i) => (
                        <li key={i} className="rationale-item" style={{ animationDelay: `0s`, fontSize: '0.85rem' }}>{text}</li>
                      ))}
                      {isTyping && <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.2)', padding: '10px 24px' }}>Finishing analysis...</div>}
                    </ul>
                  </div>
                )}
              </>
            )}

            {!response && !loading && (
              <div style={{
                textAlign: "left",
                padding: "24px 32px",
                maxWidth: "600px",
                margin: "20px auto",
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
                borderRadius: "20px",
                animation: "fadeIn 1s ease"
              }}>
                <h3 style={{ color: "#fff", marginBottom: "16px", fontSize: "1rem", fontWeight: "600" }}>What you'll get:</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <span style={{ color: "#3b82f6", fontWeight: "bold", fontSize: "0.9rem" }}>✓</span>
                    <div>
                      <div style={{ color: "rgba(255,255,255,0.9)", fontWeight: "600", fontSize: "0.85rem" }}>Technical Analysis</div>
                      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: "0.75rem" }}>RSI, MACD, moving averages, momentum</div>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <span style={{ color: "#3b82f6", fontWeight: "bold", fontSize: "0.9rem" }}>✓</span>
                    <div>
                      <div style={{ color: "rgba(255,255,255,0.9)", fontWeight: "600", fontSize: "0.85rem" }}>Fundamental Metrics</div>
                      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: "0.75rem" }}>P/E ratio, earnings, revenue, margins</div>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <span style={{ color: "#3b82f6", fontWeight: "bold", fontSize: "0.9rem" }}>✓</span>
                    <div>
                      <div style={{ color: "rgba(255,255,255,0.9)", fontWeight: "600", fontSize: "0.85rem" }}>AI Recommendation</div>
                      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: "0.75rem" }}>Buy/Sell/Hold insights with confidence scores</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

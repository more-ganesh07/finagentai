import React, { useState, useEffect, useRef } from "react";
import Sidebar from "../components/Sidebar";
import { useAuth } from "../auth";
import { Navigate } from "react-router-dom";
import {
  generatePortfolioReport,
  portfolioChatbotStream,
  getPortfolioReportHTML,
  sendPortfolioReportEmail,
  getPortfolioStatus,
  getPortfolioConnectUrl,
  getPortfolioReportDemo,
  disconnectPortfolio
} from "../services/api";
import ShinyText from "../components/ShinyText";
import FloatingBackground from "../components/FloatingBackground";
import AITextLoading from "../components/AITextLoading";

export default function Reports() {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reportStatus, setReportStatus] = useState(null);
  const [error, setError] = useState(null);

  const [initializing, setInitializing] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [authError, setAuthError] = useState(null);
  const hasCheckedStatus = useRef(false);

  const [previewHtml, setPreviewHtml] = useState(null);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [toast, setToast] = useState(null);

  // Load demo report on mount
  useEffect(() => {
    const loadDemo = async () => {
      try {
        const demoHtml = await getPortfolioReportDemo();
        if (demoHtml) {
          setPreviewHtml(demoHtml);
          setIsDemo(true);
        }
      } catch (e) {
        console.error("Failed to load demo report:", e);
      }
    };
    loadDemo();
  }, []);

  // Check connection status on mount
  useEffect(() => {
    if (!user || hasCheckedStatus.current) return;
    hasCheckedStatus.current = true;

    const checkStatus = async () => {
      setInitializing(true);
      try {
        const { connected } = await getPortfolioStatus();
        setIsConnected(connected);
      } catch (e) {
        console.error("Status check failed:", e);
      } finally {
        setInitializing(false);
      }
    };
    checkStatus();
  }, [user]);

  if (!user) return <Navigate to="/login" replace />;

  const handleLogin = async () => {
    try {
      setInitializing(true);
      setAuthError(null);

      // First, check if already connected
      const { connected } = await getPortfolioStatus();
      if (connected) {
        setIsConnected(true);
        setInitializing(false);
        return;
      }

      // If not connected, get fresh login URL
      const { login_url } = await getPortfolioConnectUrl();
      if (login_url) {
        window.open(login_url, '_blank');
        setInitializing(false);
        setAuthError("Login window opened. Click 'Verify Connection' once done.");
      } else {
        throw new Error("No login URL returned from server");
      }
    } catch (e) {
      setAuthError(e.message);
      setInitializing(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setInitializing(true);
      await disconnectPortfolio();
      setIsConnected(false);
      setAuthError(null);
    } catch (e) {
      console.error("Disconnect failed:", e);
    } finally {
      setInitializing(false);
    }
  };

  const handleGenerate = async () => {
    if (!isConnected) {
      setError("Please login to Zerodha first to generate your report.");
      return;
    }
    setLoading(true);
    setError(null);
    setPreviewHtml(null);
    setReportStatus(null);

    try {
      const html = await getPortfolioReportHTML();
      if (html) {
        setPreviewHtml(html);
        setIsDemo(false);
        setReportStatus({ status: "success", message: "Report generated successfully." });
      } else {
        throw new Error("Empty report received from server.");
      }
    } catch (err) {
      console.error("Report generation error:", err);
      setError(err.message || "Failed to generate report");
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async () => {
    // Show toast instantly
    setToast("Email sent successfully!");
    setTimeout(() => setToast(null), 3000);

    setSendingEmail(true);
    try {
      // Fire and forget (let it run in background)
      sendPortfolioReportEmail().catch(err => {
        console.error("Delayed email error:", err);
      });
    } catch (err) {
      console.error("Email send trigger error:", err);
    } finally {
      setSendingEmail(false);
    }
  };

  const getStyledHtml = (html) => {
    if (!html) return "";
    const scrollbarStyle = `
      <style>
        ::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        ::-webkit-scrollbar-track {
          background: #f8f9fa;
        }
        ::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
          border: 2px solid #f8f9fa;
          background-clip: content-box;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
        /* Firefox */
        * {
          scrollbar-width: thin;
          scrollbar-color: #cbd5e1 #f8f9fa;
        }
      </style>
    `;

    if (html.includes("</head>")) {
      return html.replace("</head>", `${scrollbarStyle}</head>`);
    }
    return scrollbarStyle + html;
  };

  return (
    <div className={`app-shell ${collapsed ? "collapsed" : ""}`}>
      <style>{`
        .reports-panel {
          display: flex;
          flex-direction: column;
          height: 100vh;
          overflow: hidden;
          background: linear-gradient(180deg, rgba(13, 17, 23, 0.8), rgba(13, 17, 23, 0.9));
          position: relative;
        }
        .reports-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 16px;
          overflow-y: auto;
          position: relative;
          z-index: 1;
        }
        .preview-container {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border-radius: 16px;
          margin-top: 16px;
          flex: 1;
          min-height: 500px;
          box-shadow: 0 20px 50px rgba(0,0,0,0.5);
          border: 1px solid rgba(255,255,255,0.1);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          animation: slideUp 0.6s ease-out;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .preview-header {
          background: rgba(255, 255, 255, 0.03);
          padding: 12px 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .preview-header span {
          color: #fff;
          font-weight: 500;
          font-size: 0.9rem;
          opacity: 0.8;
        }
        .preview-iframe {
          width: 100%;
          flex: 1;
          border: none;
          background: #fff;
        }
        .action-button {
          background: var(--brand);
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 8px;
          font-weight: 600;
          font-size: 0.85rem;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .action-button:hover:not(:disabled) {
          filter: brightness(1.1);
          transform: translateY(-1px);
        }
        .action-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .action-button.secondary {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }
        .action-button.danger {
          background: rgba(239, 68, 68, 0.2);
          color: #f87171;
          border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .action-button.danger:hover {
          background: rgba(239, 68, 68, 0.3);
        }
        .header-actions {
          display: flex;
          gap: 10px;
          align-items: center;
        }
        .conn-status {
          font-size: 0.75rem;
          padding: 4px 10px;
          border-radius: 20px;
          background: rgba(255,255,255,0.05);
          color: rgba(255,255,255,0.5);
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .conn-status.online {
          color: #34d399;
          background: rgba(52, 211, 153, 0.1);
        }
        .status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: currentColor;
        }
        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(59, 130, 246, 0.1);
          border-left-color: #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .toast {
          position: fixed;
          bottom: 40px;
          left: 50%;
          transform: translateX(-50%);
          background: #10b981;
          color: white;
          padding: 12px 24px;
          border-radius: 100px;
          font-weight: 600;
          font-size: 0.9rem;
          box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
          z-index: 10000;
          animation: toastIn 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
        }
        @keyframes toastIn {
          from { opacity: 0; transform: translate(-50%, 20px); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }
      `}</style>

      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((x) => !x)} />

      <section className="main reports-panel">
        <FloatingBackground />

        <div className="header" style={{ padding: "10px 16px", zIndex: 2 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>Portfolio Report</div>
            <div className="mini" style={{ opacity: 0.7, fontSize: "0.75rem" }}>
              {isConnected
                ? "Generate and preview your personalized analysis."
                : "View sample layout or login to analyze your holdings."}
            </div>
          </div>

          <div className="header-actions">
            {!initializing && (
              <>
                <div className={`conn-status ${isConnected ? 'online' : ''}`}>
                  <div className="status-dot"></div>
                  {isConnected ? 'Zerodha Connected' : 'Disconnected'}
                </div>

                {!isConnected ? (
                  <button className="action-button" onClick={handleLogin} disabled={loading}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                    {authError && authError.includes("Verify") ? "Verify Connection" : "Login to Zerodha"}
                  </button>
                ) : (
                  <>
                    <button
                      className="action-button"
                      onClick={handleGenerate}
                      disabled={loading}
                    >
                      {loading ? "Generating..." : "Generate Report"}
                    </button>
                    <button className="action-button danger" onClick={handleDisconnect} title="Logout from Zerodha">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                        <polyline points="16 17 21 12 16 7" />
                        <line x1="21" y1="12" x2="9" y2="12" />
                      </svg>
                      Logout
                    </button>
                  </>
                )}
              </>
            )}
            {initializing && <div style={{ fontSize: '0.8rem', opacity: 0.5 }}>Checking...</div>}
          </div>
        </div>

        <div className="reports-content">
          {error && (
            <div style={{
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              borderRadius: "12px",
              padding: "16px",
              marginBottom: "16px",
              color: "#f87171",
              fontSize: "0.9rem"
            }}>
              {error}
            </div>
          )}

          {authError && (
            <div style={{
              background: "rgba(59, 130, 246, 0.1)",
              border: "1px solid rgba(59, 130, 246, 0.2)",
              borderRadius: "12px",
              padding: "16px",
              marginBottom: "16px",
              color: "#60a5fa",
              fontSize: "0.9rem"
            }}>
              {authError}
            </div>
          )}

          {reportStatus && !previewHtml && !loading && (
            <div style={{
              background: "rgba(16, 185, 129, 0.1)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
              borderRadius: "12px",
              padding: "16px",
              marginBottom: "16px",
              color: "#34d399",
              fontSize: "0.9rem"
            }}>
              {reportStatus.message}
            </div>
          )}

          {previewHtml && !loading && (
            <div className="preview-container">
              <div className="preview-header">
                <span>{isDemo ? "Sample Report Layout (Demo)" : "Your Portfolio Analysis Report"}</span>
                {!isDemo && (
                  <button
                    className="action-button secondary"
                    onClick={handleSendEmail}
                    disabled={sendingEmail}
                    style={{ padding: "6px 14px", fontSize: "0.85rem" }}
                  >
                    {sendingEmail ? "Sending..." : "Send to Email"}
                  </button>
                )}
              </div>
              <iframe
                srcDoc={getStyledHtml(previewHtml)}
                className="preview-iframe"
                title="Portfolio Report Preview"
              />
            </div>
          )}

          {loading && (
            <div style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <div className="spinner"></div>
              <div style={{ color: "rgba(255,255,255,0.6)", fontSize: "0.9rem", textAlign: "center", maxWidth: "400px" }}>
                Analyzing your holdings and generating insights...
              </div>
            </div>
          )}
        </div>
        {toast && <div className="toast">{toast}</div>}
      </section>
    </div>
  );
}

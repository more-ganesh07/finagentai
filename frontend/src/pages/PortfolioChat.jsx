import React, { useEffect, useRef, useState, useMemo } from "react";
import Sidebar from "../components/Sidebar";
import ChatInput from "../components/ChatInput";
import ChatMessage from "../components/ChatMessage";
import { useAuth } from "../auth";
import { Navigate } from "react-router-dom";
import AITextLoading from "../components/AITextLoading";
import ShinyText from "../components/ShinyText";
import "../components/ShinyText.css";
import { portfolioChatbotStream, getPortfolioStatus, getPortfolioConnectUrl, disconnectPortfolio } from "../services/api";
import FloatingBackground from "../components/FloatingBackground";


export default function PortfolioChat() {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [msgs, setMsgs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [showAuthPrompt, setShowAuthPrompt] = useState(false);
  const [authError, setAuthError] = useState(null);
  const scrollRef = useRef(null);
  const hasCheckedStatus = useRef(false);


  const userHasSentMessage = msgs.some((m) => m.role === "user");

  // scroll helper: wait a tick so layout/transition finishes, then scroll
  const scrollToBottom = () => {
    // small delay to allow header collapse/DOM updates to finish
    setTimeout(() => {
      requestAnimationFrame(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      });
    }, 50);
  };

  const [isThinking, setIsThinking] = useState(false);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    // whenever messages, loading, or header state changes -> scroll
    scrollToBottom();
  }, [msgs, loading, isThinking, userHasSentMessage]);

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
        // Show a helpful hint
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

  if (!user) return <Navigate to="/login" replace />;

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
      setIsThinking(false);
    }
  };

  const handleSend = async (q) => {
    if (!isConnected) {
      setShowAuthPrompt(true);
      return;
    }
    // add user message immediately for snappy UI
    setMsgs((m) => [...m, { role: "user", text: q, timestamp: new Date() }]);
    setLoading(true);
    setIsThinking(true);

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let botResponse = "";

    // Local flag to track if we've received the first chunk in this request
    let firstChunkReceived = false;

    try {
      // Use streaming endpoint for chat
      await portfolioChatbotStream(
        q,
        (chunk) => {
          // onChunk - accumulate response
          if (!firstChunkReceived) {
            firstChunkReceived = true;
            setIsThinking(false);
          }

          botResponse += chunk;
          // Update the last bot message in real-time
          setMsgs((m) => {
            const newMsgs = [...m];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.role === "bot" && lastMsg.streaming) {
              lastMsg.text = botResponse;
            } else {
              newMsgs.push({
                role: "bot",
                text: botResponse,
                timestamp: new Date(),
                streaming: true,
              });
            }
            return newMsgs;
          });
        },
        () => {
          // onComplete
          setLoading(false);
          setIsThinking(false);
          abortControllerRef.current = null;

          // Mark streaming as complete
          setMsgs((m) => {
            const newMsgs = [...m];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.streaming) {
              delete lastMsg.streaming;
            }
            return newMsgs;
          });
        },
        (error) => {
          // onError
          if (error.name === 'AbortError' || error.message === 'Aborted') {
            console.log("Generation stopped by user");
            return;
          }

          console.error("Portfolio chatbot error:", error);
          setLoading(false);
          setIsThinking(false);
          abortControllerRef.current = null;

          const friendly = `Sorry, something went wrong while contacting the portfolio assistant. ${error.message ? `(${error.message})` : ""}`;
          setMsgs((m) => [...m, { role: "bot", text: friendly, timestamp: new Date() }]);
        },
        controller.signal
      );
    } catch (e) {
      // Catch sync errors
      if (e.name === 'AbortError') return;
      console.error("Portfolio chatbot error:", e);
      setLoading(false);
      setIsThinking(false);
      const friendly = `Sorry, something went wrong while contacting the portfolio assistant. ${e.message ? `(${e.message})` : ""}`;
      setMsgs((m) => [...m, { role: "bot", text: friendly, timestamp: new Date() }]);
    }
  };

  const handleEdit = async (index, newText) => {
    // Keep messages up to the edited one, and update the edited message
    const newMsgs = msgs.slice(0, index + 1);
    newMsgs[index] = { ...newMsgs[index], text: newText, timestamp: new Date() };
    setMsgs(newMsgs);

    setLoading(true);
    setIsThinking(true);

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let botResponse = "";

    // Local flag to track if we've received the first chunk in this request
    let firstChunkReceived = false;

    try {
      await portfolioChatbotStream(
        newText,
        (chunk) => {
          if (!firstChunkReceived) {
            firstChunkReceived = true;
            setIsThinking(false);
          }

          botResponse += chunk;
          setMsgs((m) => {
            const newMsgs = [...m];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.role === "bot" && lastMsg.streaming) {
              lastMsg.text = botResponse;
            } else {
              newMsgs.push({
                role: "bot",
                text: botResponse,
                timestamp: new Date(),
                streaming: true,
              });
            }
            return newMsgs;
          });
        },
        () => {
          setLoading(false);
          setIsThinking(false);
          abortControllerRef.current = null;

          setMsgs((m) => {
            const newMsgs = [...m];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.streaming) {
              delete lastMsg.streaming;
            }
            return newMsgs;
          });
        },
        (error) => {
          if (error.name === 'AbortError') return;
          console.error("Portfolio chatbot error:", error);
          setLoading(false);
          setIsThinking(false);
          const friendly = `Sorry, something went wrong. ${error.message ? `(${error.message})` : ""}`;
          setMsgs((m) => [...m, { role: "bot", text: friendly, timestamp: new Date() }]);
        },
        controller.signal
      );
    } catch (e) {
      if (e.name === 'AbortError') return;
      console.error("Portfolio chatbot error:", e);
      setLoading(false);
      setIsThinking(false);
      const friendly = `Sorry, something went wrong. ${e.message ? `(${e.message})` : ""}`;
      setMsgs((m) => [...m, { role: "bot", text: friendly, timestamp: new Date() }]);
    }
  };

  return (
    <div className={`app-shell ${collapsed ? "collapsed" : ""}`}>
      <style>{`
        .portfolio-panel {
          display: flex;
          flex-direction: column;
          height: 90vh;
          overflow: hidden;
          background: linear-gradient(180deg, rgba(255,255,255,0.005), rgba(255,255,255,0.01));
        }

        .content {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          position: relative;
          z-index: 1;
        }

        .chat-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 16px 24px;
          scroll-behavior: smooth;
          box-sizing: border-box;
        }

        .footer {
          position: sticky;
          bottom: 0;
          padding: 12px 24px;
          z-index: 5;
        }

        .welcome-state {
          display: flex;
          flex-direction: column;
          justify-content: center !important;
          align-items: center;
          height: 100%;
        }
        .welcome-screen {
          text-align: center;
          max-width: 650px;
          margin-bottom: 32px;
          margin-top: -10vh;
          animation: fadeIn 0.8s ease-out;
          padding: 0 20px;
        }
        .welcome-icon {
          font-size: 2.2rem;
          margin-bottom: 12px;
        }
        .welcome-screen h1 {
          font-size: 1.6rem;
          font-weight: 700;
          color: #fff;
          margin-bottom: 0;
        }
        .welcome-state .footer {
          width: 100%;
          max-width: 760px;
          border: none;
          background: transparent;
          padding: 0 24px;
        }
        .welcome-state .input-container {
           box-shadow: 0 10px 40px rgba(0,0,0,0.3);
           border-radius: 12px;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .chat-disclaimer {
          font-size: 0.65rem;
          color: rgba(255, 255, 255, 0.3);
          text-align: center;
          margin-top: 8px;
          letter-spacing: 0.01em;
        }

         .initializing-overlay {
          position: absolute;
          inset: 0;
          background: rgba(13, 17, 23, 0.75);
          backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          flex-direction: column;
          gap: 16px;
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
      `}</style>

      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((x) => !x)} />

      <section className="main portfolio-panel" style={{ position: 'relative' }}>
        <FloatingBackground />
        <div className="header" style={{ padding: "10px 16px", zIndex: 1001 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>Portfolio Chat</div>
            <div className="mini" style={{ opacity: 0.7, fontSize: "0.75rem" }}>
              {isConnected
                ? "Ask anything about your holdings and performance."
                : "Login to Zerodha to analyze your portfolio."}
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
                  <button className="action-button danger" onClick={handleDisconnect} title="Logout from Zerodha">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16 17 21 12 16 7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Logout
                  </button>
                )}
              </>
            )}
            {initializing && <div style={{ fontSize: '0.8rem', opacity: 0.5 }}>Checking...</div>}
          </div>
        </div>

        {initializing && (
          <div className="initializing-overlay">
            <ShinyText
              text="Checking connection..."
              disabled={false}
              speed={3}
            />
          </div>
        )}

        {!initializing && showAuthPrompt && !isConnected && (
          <div className="initializing-overlay" onClick={() => setShowAuthPrompt(false)}>
            <div onClick={e => e.stopPropagation()} style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '40px',
              borderRadius: '24px',
              background: 'rgba(13, 17, 23, 0.4)',
              boxShadow: '0 20px 50px rgba(0,0,0,0.3)',
              border: '1px solid rgba(255,255,255,0.05)',
              maxWidth: '90%',
              width: '450px'
            }}>
              <div style={{ fontSize: "3.5rem", marginBottom: "1.5rem" }}>🔐</div>
              <h2 style={{ color: "#fff", fontSize: "1.5rem", fontWeight: "700", marginBottom: "12px", textAlign: 'center' }}>Zerodha Login Required</h2>
              <div style={{ color: "rgba(255,255,255,0.6)", fontSize: "0.95rem", textAlign: "center", lineHeight: "1.6", marginBottom: "32px" }}>
                To analyze your portfolio, we need a secure connection to your Zerodha account.
              </div>
              <button
                className="action-button"
                onClick={handleLogin}
                style={{
                  padding: "14px 40px",
                  borderRadius: "12px",
                  fontWeight: 700,
                  fontSize: "1.05rem",
                  background: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                {authError && authError.includes("Verify") ? "Verify Connection" : "Login to Zerodha"}
              </button>
              {authError && <div style={{ color: "#f87171", fontSize: "0.85rem", marginTop: "16px", textAlign: 'center' }}>{authError}</div>}
            </div>
          </div>
        )}

        <div className={`content ${!userHasSentMessage ? "welcome-state" : ""}`}>
          {!userHasSentMessage && (
            <div className="welcome-screen">
              <h1 style={{ fontSize: '1.8rem', fontWeight: '800', marginBottom: '16px' }}>Welcome to Portfolio Pulse!</h1>
              <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "1rem", lineHeight: "1.6" }}>
                Connect your holdings to get clear, personalized insights on performance and risk.
              </p>
            </div>
          )}

          <div className="chat-scroll" ref={scrollRef} style={{ display: !userHasSentMessage ? 'none' : 'block' }}>
            {msgs.map((m, i) => (
              <ChatMessage
                key={i}
                role={m.role === "user" ? "user" : "bot"}
                text={m.text}
                timestamp={m.timestamp}
                userInitial={(user?.name?.[0] || user?.email?.[0] || "U").toUpperCase()}
                onEdit={(newText) => handleEdit(i, newText)}
              />
            ))}

            {isThinking && (
              <div style={{ padding: "10px 20px" }}>
                <AITextLoading />
              </div>
            )}
          </div>

          <div className="footer">
            <div className="input-container">
              <ChatInput
                onSend={handleSend}
                onStop={loading ? handleStop : undefined}
                placeholder="e.g., Which holdings are affecting my returns the most today?"
                loading={loading || initializing}
              />
              {userHasSentMessage && (
                <div className="chat-disclaimer">
                  AI-powered insights for research purposes. Not financial advice.
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

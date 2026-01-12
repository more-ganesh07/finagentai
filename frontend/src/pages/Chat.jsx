import React, { useEffect, useRef, useState, useMemo } from "react";
import Sidebar from "../components/Sidebar";
import ChatInput from "../components/ChatInput";
import ChatMessage from "../components/ChatMessage";
import { useAuth } from "../auth";
import { Navigate } from "react-router-dom";
import AITextLoading from "../components/AITextLoading";
import ShinyText from "../components/ShinyText"; // Added import
import { marketChatbotStream } from "../services/api"; // Updated import
import FloatingBackground from "../components/FloatingBackground";


export default function Chat() {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [msgs, setMsgs] = useState([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const [isThinking, setIsThinking] = useState(false);
  const abortControllerRef = useRef(null);


  const userHasSentMessage = msgs.some((m) => m.role === "user");

  // Smart scroll: only scroll to bottom if user is already near bottom or a user message was sent
  useEffect(() => {
    if (!scrollRef.current) return;

    const container = scrollRef.current;
    const threshold = 150; // pixels from bottom to trigger auto-scroll
    const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold;

    // Always scroll if last message is from user
    const lastMsgIsUser = msgs.length > 0 && msgs[msgs.length - 1].role === "user";

    if (isAtBottom || lastMsgIsUser) {
      container.scrollTop = container.scrollHeight;
    }
  }, [msgs, loading, isThinking]);

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
    const userMsg = { role: "user", text: q, timestamp: new Date() };
    setMsgs((m) => [...m, userMsg]);
    setLoading(true);
    setIsThinking(true);

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let botResponse = "";
    // Local flag to track if we've received the first chunk
    let firstChunkReceived = false;

    try {
      await marketChatbotStream(
        q,
        (chunk) => {
          // onChunk
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
          // onComplete
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
          // onError
          if (error.name === 'AbortError' || error.message === 'Aborted') {
            console.log("Generation stopped by user");
            return;
          }
          console.error("Market chatbot error:", error);
          setLoading(false);
          setIsThinking(false);
          abortControllerRef.current = null;

          const friendly = `Sorry, something went wrong while contacting the market assistant. ${error.message || ''}`;
          setMsgs((m) => [...m, { role: "bot", text: friendly, timestamp: new Date() }]);
        },
        controller.signal
      );
    } catch (e) {
      if (e.name === 'AbortError') return;
      console.error("Market chatbot error:", e);
      setLoading(false);
      setIsThinking(false);
      const friendly = `Sorry, something went wrong while contacting the market assistant. ${e.message || ''}`;
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
    let firstChunkReceived = false;

    try {
      await marketChatbotStream(
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
          console.error("Market chatbot error:", error);
          setLoading(false);
          setIsThinking(false);
          const friendly = `Sorry, something went wrong while contacting the market assistant. ${error.message || ''}`;
          setMsgs((m) => [...m, { role: "bot", text: friendly, timestamp: new Date() }]);
        },
        controller.signal
      );
    } catch (e) {
      if (e.name === 'AbortError') return;
      console.error("Market chatbot error:", e);
      setLoading(false);
      setIsThinking(false);
      const friendly = `Sorry, something went wrong while contacting the market assistant. ${e.message || ''}`;
      setMsgs((m) => [...m, { role: "bot", text: friendly, timestamp: new Date() }]);
    }
  };

  return (
    <div className={`app-shell ${collapsed ? "collapsed" : ""}`}>
      <style>{`
        /* Chat panel: orange accent, subtle by default, stronger on hover/focus */
        .chat-panel {
          display: flex;
          flex-direction: column;
          height: 90vh;
          overflow: hidden;
          border-radius: 12px;
          border: 1.5px solid rgba(255,122,24,0.10); /* subtle default orange */
          box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.01),
            inset 0 8px 24px rgba(255,122,24,0.02),
            0 8px 28px rgba(0,0,0,0.45);
          transition: border-color .16s ease, box-shadow .18s ease, transform .12s ease;
          background: linear-gradient(180deg, rgba(255,255,255,0.005), rgba(255,255,255,0.01));
        }

        /* stronger accent when user interacts with the chat panel */
        .chat-panel:hover,
        .chat-panel:focus-within {
          border-color: rgba(255,122,24,0.36);
          box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.01),
            inset 0 18px 48px rgba(255,122,24,0.06),
            0 14px 42px rgba(0,0,0,0.50);
        }

        /* ensure the header sit flush with panel edges */
        .chat-panel .header {
          border-radius: 12px 12px 0 0;
          background: transparent;
        }

        /* inner layout rules */
        .chat-panel .content {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          position: relative;
          z-index: 1;
        }
        .chat-panel .chat-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 16px 24px;
          scroll-behavior: smooth;
          background: transparent; /* let panel surface show */
        }

        /* keep ShinyText area visually separated */
        .chat-panel .shiny-wrap { padding: 10px 20px; }

        /* footer visual polish */
        .chat-panel .footer {
          position: sticky;
          bottom: 0;
          padding: 12px 24px;
          z-index: 5;
        }

        /* keyboard accessibility: visible ring when focusing input inside panel */
        .chat-panel:focus-within {
          outline: none;
          box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.01),
            0 0 0 4px rgba(255,122,24,0.06);
        }

        /* small screens - reduce height slightly */
        @media (max-width: 900px) {
          .chat-panel { height: calc(100vh - 48px); }
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
      `}</style>

      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((x) => !x)} />

      {/* added chat-panel class so styles are scoped to chat area only */}
      <section className="main chat-panel" style={{ position: 'relative' }}>
        <FloatingBackground />
        <div className={`content ${!userHasSentMessage ? "welcome-state" : ""}`}>
          {!userHasSentMessage && (
            <div className="welcome-screen">
              <h1 style={{ fontSize: '1.8rem', fontWeight: '800', marginBottom: '16px' }}>Welcome to Market Watch!</h1>
              <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "1rem", lineHeight: "1.6" }}>
                Ask anything about Indian markets, sectors, or stocks. Get AI-powered insights backed by real-time data and news.
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
              <div className="shiny-wrap">
                <AITextLoading />
              </div>
            )}
          </div>

          {/* ✅ Sticky footer */}
          <div className="footer">
            <div className="input-container">
              <ChatInput
                onSend={handleSend}
                onStop={loading ? handleStop : undefined}
                placeholder="e.g., Why is the Silver ETF rising day by day?"
                loading={loading}
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
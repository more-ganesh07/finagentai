import React, { useState, useRef, useEffect } from "react";
import AI_Voice from "./AI_Voice";
import "./AI_Voice.css";
import { Send, Square } from "lucide-react";

export default function ChatInput({
  onSend,
  placeholder = "Type your question…",
  loading = false,
  onStop,
  autoSendVoice = false,
}) {
  const [text, setText] = useState("");
  const finalVoiceRef = useRef("");
  const textareaRef = useRef(null);

  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      const newHeight = Math.min(textarea.scrollHeight, 120);
      textarea.style.height = `${newHeight}px`;

      // Only show scrollbar if content exceeds max height
      textarea.style.overflowY = textarea.scrollHeight > 120 ? "auto" : "hidden";
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [text]);

  const submit = (e) => {
    e && e.preventDefault();

    // If loading and having onStop, this is a Stop action
    if (loading && onStop) {
      onStop();
      return;
    }

    const t = text.trim();
    if (!t || loading) return;
    onSend(t);
    setText("");
    // Reset height after send
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.overflowY = "hidden";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(e);
    }
  };

  const handleTranscript = (transcript) => {
    setText(transcript || "");
    finalVoiceRef.current = transcript || "";
  };

  const handleListeningChange = () => { };

  // Can we stop?
  const canStop = loading && !!onStop;

  return (
    <>
      <form className="chat-input" onSubmit={submit}>
        <textarea
          ref={textareaRef}
          className="input"
          value={text}
          placeholder={placeholder}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading && !onStop} // Disable input only if we can't stop (legacy loading)
          aria-label="Chat message"
          rows={1}
        />

        {/* Mic button */}
        <div style={{ marginLeft: 8 }}>
          <AI_Voice
            variant="button"
            disabled={loading}
            onTranscript={handleTranscript}
            onListeningChange={handleListeningChange}
          />
        </div>

        <button
          className="send-btn"
          type="submit"
          disabled={loading && !onStop} // Enable button if we can stop
          aria-label={canStop ? "Stop generating" : "Send message"}
          style={canStop ? { background: "rgba(255, 69, 58, 0.9)" } : {}}
        >
          {canStop ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Square size={16} fill="currentColor" />
            </div>
          ) : loading ? (
            <div
              style={{
                width: "16px",
                height: "16px",
                border: "2px solid rgba(255,255,255,0.3)",
                borderTopColor: "#fff",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }}
            />
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Send size={16} color="var(--accent-orange)" />

            </div>
          )}
        </button>
      </form>

      <style>{`
        @keyframes spin { from { transform: rotate(0);} to { transform: rotate(360deg);} }

        .chat-input {
          display: grid;
          grid-template-columns: 1fr auto auto;
          gap: 8px;
          align-items: flex-end; /* Align to bottom so it grows upwards */
          padding: 8px;
          border-radius: 10px;
          background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.015));
          border: 1px solid rgba(255,122,24,0.10);
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.01), inset 0 6px 18px rgba(255,122,24,0.02);
          min-height: 56px;
          height: auto;
          box-sizing: border-box;
        }

        .chat-input .input {
          padding: 10px 12px;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.04);
          background: rgba(255,255,255,0.02);
          min-height: 40px;
          max-height: 120px; /* Approx 5 lines */
          box-sizing: border-box;
          resize: none;
          overflow-y: hidden; /* Hidden by default, toggled in JS */
          font-family: inherit;
          font-size: 0.9rem;
          line-height: 1.5;
          color: inherit;
          white-space: pre-wrap; /* Preserve whitespace/indentation */
        }

        .chat-input .input::placeholder {
          font-size: 0.85em;
          opacity: 0.6;
        }

        .chat-input .input:focus {
          outline: none;
          border-color: var(--accent-orange);
          box-shadow: 0 6px 18px rgba(255,122,24,0.06);
        }

        /* Custom scrollbar for the textarea */
        .chat-input .input::-webkit-scrollbar {
          width: 6px;
        }
        .chat-input .input::-webkit-scrollbar-track {
          background: transparent;
        }
        .chat-input .input::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }
        .chat-input .input::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        .send-btn {
          padding: 8px 14px;
          border-radius: 8px;
          background: linear-gradient(180deg, var(--brand-2), var(--brand));
          color: var(--ink);
          border: 0;
          height: 40px;
          font-weight: 600;
          margin-bottom: 0; /* Align with bottom of input */
        }

        .send-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        @media (max-width: 540px) {
          .chat-input { padding: 6px; gap: 6px; grid-template-columns: 1fr auto; }
          .send-btn { min-width: 64px; }
        }
      `}</style>
    </>
  );
}
import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import styled from "styled-components";
import { Copy, ThumbsUp, ThumbsDown, Pencil, Check, X } from "lucide-react";

const MarkdownWrapper = styled.div`
  /* === ULTRA-COMPACT MARKDOWN STYLING FOR CHAT (tighter) === */
  font-size: 0.92rem;
  line-height: 1.16;
  color: #e5e7eb;
  white-space: normal;

  /* reset block margins with small consistent gap */
  p, h1, h2, h3, ul, ol, pre, table, blockquote {
    margin: 0 0 0.5rem 0;
    padding: 0;
  }

  /* paragraphs */
  p {
    line-height: 1.16;
  }

  /* headings */
  h1, h2, h3 {
    margin: 0 0 0.5rem 0;
    font-weight: 600;
    line-height: 1.08;
  }
  h1 { color: #facc15; font-size: 1rem; }
  h2 { color: #93c5fd; font-size: 0.95rem; }
  h3 { color: #a5b4fc; font-size: 0.9rem; }

  /* lists — zero top/bottom margin, tiny item spacing */
  ul, ol {
    padding-left: 0.9rem;   /* compact indent */
  }
  li {
    margin: 0.2rem 0;      /* small gap between items */
    line-height: 1.16;
  }

  /* pre / code blocks — remove margin */
  pre {
    margin: 0;
    background: #1a1f2e;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 6px;           /* slightly smaller */
    color: #c9d1d9;
    font-family: monospace;
    overflow-x: auto;
  }

  /* blockquote */
  blockquote {
    margin: 0;
    padding-left: 6px;
    font-style: italic;
    color: #9baecf;
    border-left: 2px solid rgba(255,255,255,0.12);
  }

  /* table */
  table {
    margin: 0;
    border-collapse: collapse;
    width: 100%;
    font-size: 0.9rem;
  }
  th, td {
    padding: 4px 6px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }

  /* inline-code */
  code {
    background: rgba(255,255,255,0.06);
    color: #f0c674;
    border-radius: 3px;
    padding: 0 3px;
    font-family: monospace;
    font-size: 0.9em;
  }

  /* Strong and links */
  strong { color: #facc15; font-weight:600; }
  a { color: #60a5fa; text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* === Important: collapse ANY last-child anywhere inside markdown === */
  /* This prevents nested elements from adding bottom-margin */
  & *:last-child {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
  }

  /* Also ensure the wrapper itself doesn't introduce top/bottom spacing */
  margin: 0;
  padding: 0;

  /* ensure direct first/last child not adding extra gaps */
  & > :first-child { margin-top: 0 !important; }
  & > :last-child  { margin-bottom: 0 !important; }
`;

const IconBtn = ({ onClick, children, title, active }) => {
  const [hover, setHover] = useState(false);
  return (
    <button
      onClick={onClick}
      title={title}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: "transparent",
        border: "none",
        color: active ? "#fff" : (hover ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.4)"),
        cursor: "pointer",
        padding: "2px",
        display: "flex",
        alignItems: "center",
        transition: "color 0.2s",
      }}
    >
      {children}
    </button>
  );
};

export default function ChatMessage({ role, text, userInitial = "U", timestamp, onEdit }) {
  const isUser = role === "user";
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(text);
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const formatTime = (date) => {
    if (!date) return "";
    try {
      return new Intl.DateTimeFormat("en-US", {
        hour: "numeric",
        minute: "numeric",
        hour12: true,
      }).format(new Date(date));
    } catch (e) {
      return "";
    }
  };

  const timeString = formatTime(timestamp);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveEdit = () => {
    if (editText.trim() !== text) {
      onEdit(editText);
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditText(text);
    setIsEditing(false);
  };

  const handleFeedback = (type) => {
    setFeedback((prev) => (prev === type ? null : type));
  };

  return (
    <div className={`chat-row ${role}`}>
      {isUser ? (
        <>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", maxWidth: "100%" }}>
            {isEditing ? (
              <div className={`bubble ${role}`} style={{ width: "100%", minWidth: "300px" }}>
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  style={{
                    width: "100%",
                    background: "transparent",
                    border: "none",
                    color: "inherit",
                    resize: "none",
                    outline: "none",
                    fontFamily: "inherit",
                    fontSize: "inherit",
                    lineHeight: "inherit"
                  }}
                  rows={Math.max(2, editText.split('\n').length)}
                />
                <div style={{ display: "flex", gap: "8px", marginTop: "8px", justifyContent: "flex-end" }}>
                  <button
                    onClick={handleSaveEdit}
                    style={{
                      background: "#11c26f",
                      border: "none",
                      borderRadius: "4px",
                      padding: "6px 12px",
                      color: "white",
                      cursor: "pointer",
                      fontSize: "0.85rem",
                      fontWeight: "500"
                    }}
                  >
                    Send
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    onMouseEnter={(e) => e.currentTarget.style.background = "#ef4444"}
                    onMouseLeave={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
                    style={{
                      background: "rgba(255,255,255,0.1)",
                      border: "none",
                      borderRadius: "4px",
                      padding: "6px 12px",
                      color: "white",
                      cursor: "pointer",
                      fontSize: "0.85rem",
                      fontWeight: "500",
                      transition: "background 0.2s"
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className={`bubble ${role}`}>
                {text}
              </div>
            )}

            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px", marginRight: "4px" }}>
              <div style={{ fontSize: "0.7rem", color: "rgba(255, 255, 255, 0.4)", lineHeight: 1 }}>
                {timeString}
              </div>
              {!isEditing && (
                <>
                  <IconBtn onClick={handleCopy} title="Copy">
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                  </IconBtn>
                  <IconBtn onClick={() => setIsEditing(true)} title="Edit">
                    <Pencil size={12} />
                  </IconBtn>
                </>
              )}
            </div>
          </div>
          <div className={`avatar ${role}`} aria-label="You">
            <span>{userInitial}</span>
          </div>
        </>
      ) : (
        <>
          <div className={`avatar ${role}`} aria-label="AI">
            <span>AI</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", maxWidth: "100%" }}>
            <div className={`bubble ${role}`}>
              <MarkdownWrapper className="md-bubble">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ inline, className, children, ...props }) {
                      return inline ? (
                        <code {...props}>{children}</code>
                      ) : (
                        <pre>
                          <code {...props}>{children}</code>
                        </pre>
                      );
                    },
                    a({ children, ...props }) {
                      return (
                        <a target="_blank" rel="noreferrer noopener" {...props}>
                          {children}
                        </a>
                      );
                    },
                    table({ children }) {
                      return (
                        <div style={{ overflowX: "auto", margin: "0.5em 0" }}>
                          <table>{children}</table>
                        </div>
                      );
                    },
                  }}
                >
                  {text}
                </ReactMarkdown>
              </MarkdownWrapper>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px", marginLeft: "4px" }}>
              <div style={{ fontSize: "0.7rem", color: "rgba(255, 255, 255, 0.4)", lineHeight: 1 }}>
                {timeString}
              </div>
              <IconBtn onClick={handleCopy} title="Copy">
                {copied ? <Check size={12} /> : <Copy size={12} />}
              </IconBtn>
              <IconBtn
                onClick={() => handleFeedback('up')}
                title="Good response"
                active={feedback === 'up'}
              >
                <ThumbsUp size={12} fill={feedback === 'up' ? "currentColor" : "none"} />
              </IconBtn>
              <IconBtn
                onClick={() => handleFeedback('down')}
                title="Bad response"
                active={feedback === 'down'}
              >
                <ThumbsDown size={12} fill={feedback === 'down' ? "currentColor" : "none"} />
              </IconBtn>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../auth";
import { FcGoogle } from "react-icons/fc";
import { FaGithub } from "react-icons/fa";
import { FaMicrosoft } from "react-icons/fa";


export default function Login() {
  const { user, login } = useAuth();
  const nav = useNavigate();

  const [activeTab, setActiveTab] = useState("try");
  const [email, setEmail] = useState("");
  const [userName, setUserName] = useState("");
  const [pwd, setPwd] = useState("");

  if (user) return <Navigate to="/chat" replace />;

  const submit = (e) => {
    e.preventDefault();
    if (activeTab === "try") {
      login(null, userName || "Guest");
    } else {
      login(email || "user@example.com", userName);
    }
    nav("/chat");
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px",
      }}
    >
      <div
        style={{
          width: "min(460px, 92vw)",
          background: "var(--card)",
          border: "2px solid var(--accent-orange)", // ORANGE BORDER
          borderRadius: "18px",
          padding: "24px",
          boxShadow: "0 16px 44px rgba(0,0,0,.4)",
        }}
      >
        {/* ---------------- TABS ---------------- */}
        <div
          style={{
            display: "flex",
            marginBottom: 20,
            borderBottom: "1px solid rgba(255,255,255,.1)",
          }}
        >
          <div
            onClick={() => setActiveTab("try")}
            style={{
              flex: 1,
              textAlign: "center",
              padding: "12px",
              cursor: "pointer",
              fontWeight: 600,
              color: activeTab === "try" ? "var(--accent-orange)" : "#ddd",
              borderBottom:
                activeTab === "try"
                  ? "2px solid var(--accent-orange)"
                  : "2px solid transparent",
            }}
          >
            Try with your name
          </div>

          <div
            onClick={() => setActiveTab("login")}
            style={{
              flex: 1,
              textAlign: "center",
              padding: "12px",
              cursor: "pointer",
              fontWeight: 600,
              color: activeTab === "login" ? "var(--accent-orange)" : "#ddd",
              borderBottom:
                activeTab === "login"
                  ? "2px solid var(--accent-orange)"
                  : "2px solid transparent",
            }}
          >
            Login
          </div>

          {/* 
          <div
            onClick={() => setActiveTab("signup")}
            style={{
              flex: 1,
              textAlign: "center",
              padding: "12px",
              cursor: "pointer",
              fontWeight: 600,
              color: activeTab === "signup" ? "var(--accent-orange)" : "#ddd",
              borderBottom:
                activeTab === "signup"
                  ? "2px solid var(--accent-orange)"
                  : "2px solid transparent",
            }}
          >
            Signup
          </div>
          */}
        </div>

        {/* ---------------- FORM ---------------- */}
        <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
          {activeTab !== "try" && (
            <input
              className="input"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          )}

          {(activeTab === "signup" || activeTab === "try") && (
            <input
              className="input"
              placeholder="Your Name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
            />
          )}

          {activeTab !== "try" && (
            <input
              className="input"
              type="password"
              placeholder={activeTab === "login" ? "Password" : "Create Password"}
              value={pwd}
              onChange={(e) => setPwd(e.target.value)}
            />
          )}

          {activeTab === "signup" && (
            <input
              className="input"
              type="password"
              placeholder="Confirm Password"
            />
          )}

          <button className="button" type="submit">
            {activeTab === "login" ? "Continue" : activeTab === "signup" ? "Create Account" : "Try Now"}
          </button>
        </form>

        {/* ----------------- SSO OPTIONS ----------------- */}
        <div
          style={{
            marginTop: 22,
            textAlign: "center",
            color: "#bbb",
            fontSize: ".9rem",
          }}
        >
          or continue with
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 20,
            marginTop: 16,
          }}
        >
          {/* Google */}
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "50%",
              background: "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.15)",
              display: "grid",
              placeItems: "center",
              cursor: "pointer",
              transition: "0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.15)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
          >
            <FcGoogle size={22} />
          </div>

          {/* GitHub */}
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "50%",
              background: "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.15)",
              display: "grid",
              placeItems: "center",
              cursor: "pointer",
              transition: "0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.15)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
          >
            <FaGithub size={20} color="#fff" />
          </div>

          {/* Microsoft */}
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "50%",
              background: "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.15)",
              display: "grid",
              placeItems: "center",
              cursor: "pointer",
              transition: "0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.15)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
          >
            <FaMicrosoft size={22} color="#fff" />
          </div>

        </div>
      </div>
    </div >
  );
}

import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function TopNav() {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const nav = useNavigate();

  const handleLogout = () => {
    logout?.();
    nav("/");
  };

  const isLanding = pathname === "/";
  return (
    <header className="topnav">
      {/* Left brand logo */}
      <div className="topnav__left">
        <Link to="/" className="topnav__brand">
          <span className="brand-dim">FinAgent</span>
          <span className="brand-glow">AI</span>
        </Link>
      </div>

      {/* Right section */}
      <div className="topnav__right">
        {/* Navigation links only on landing page */}

        <nav className="topnav__links">
          <Link className={pathname === "/" ? "active" : ""} to="/">
            Home
          </Link>
          {!user && (
            <>
              <Link className={pathname === "/about" ? "active" : ""} to="/about">About</Link>
            </>
          )}
        </nav>

        {/* Buttons */}
        {!user && isLanding && (
          <button className="btn-login" onClick={() => nav("/login")}>
            Login
          </button>
        )}

        {user && !isLanding && (
          <button className="btn-logout" onClick={handleLogout}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="red"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        )}
      </div>
    </header>
  );
}

import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import IndexTicker from "./IndexTicker";
import { getPortfolioStatus, disconnectPortfolio } from "../services/api";
import { useState, useEffect } from "react";

/* 🌈 Colorful Icons */
const IconChat = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <defs>
      <linearGradient id="chatGradient" x1="0" y1="0" x2="24" y2="24">
        <stop offset="0%" stopColor="#00B4DB" />
        <stop offset="100%" stopColor="#0083B0" />
      </linearGradient>
    </defs>
    <path
      d="M4 6.5A3.5 3.5 0 0 1 7.5 3h9A3.5 3.5 0 0 1 20 6.5v5A3.5 3.5 0 0 1 16.5 15H12l-3.8 3.2c-.6.5-1.2.1-1.2-.6V15A3.5 3.5 0 0 1 4 11.5v-5Z"
      stroke="url(#chatGradient)"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const IconPortfolio = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <defs>
      <linearGradient id="portfolioGradient" x1="0" y1="0" x2="24" y2="24">
        <stop offset="0%" stopColor="#F7971E" />
        <stop offset="100%" stopColor="#FFD200" />
      </linearGradient>
    </defs>
    <path
      d="M4 18V6m5 12V10m5 8V8m5 10V4"
      stroke="url(#portfolioGradient)"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

const IconReport = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <defs>
      <linearGradient id="reportGradient" x1="0" y1="0" x2="24" y2="24">
        <stop offset="0%" stopColor="#8E2DE2" />
        <stop offset="100%" stopColor="#4A00E0" />
      </linearGradient>
    </defs>
    <path
      d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
      stroke="url(#reportGradient)"
      strokeWidth="1.8"
    />
    <path
      d="M14 3v4a1 1 0 0 0 1 1h4"
      stroke="url(#reportGradient)"
      strokeWidth="1.8"
    />
    <path
      d="M8.5 14H15M8.5 17H13"
      stroke="url(#reportGradient)"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

const IconStockBuddy = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <defs>
      <linearGradient id="stockBuddyGradient" x1="0" y1="0" x2="24" y2="24">
        <stop offset="0%" stopColor="#3b82f6" />
        <stop offset="100%" stopColor="#6366f1" />
      </linearGradient>
    </defs>
    <path
      d="M3 3v18h18"
      stroke="url(#stockBuddyGradient)"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M7 16l4-6 3 3 5-8"
      stroke="url(#stockBuddyGradient)"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle
      cx="19"
      cy="5"
      r="2"
      fill="url(#stockBuddyGradient)"
    />
  </svg>
);

const IconPower = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <defs>
      <linearGradient id="powerGradient" x1="0" y1="0" x2="24" y2="24">
        <stop offset="0%" stopColor="#eb3349" />
        <stop offset="100%" stopColor="#f45c43" />
      </linearGradient>
    </defs>
    <path
      d="M18.36 6.64a9 9 0 1 1-12.73 0M12 2v10"
      stroke="url(#powerGradient)"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default function Sidebar({ collapsed, onToggle }) {
  const { user } = useAuth();
  const displayName = user?.name || user?.email?.split("@")[0] || "User";
  const initial = (displayName?.[0] || "U").toUpperCase();

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* top row: logo chip + collapse toggle */}
      <div className="brand-row small">
        <button className="toggle tiny" onClick={onToggle} aria-label="Toggle sidebar">
          {collapsed ? "»" : "«"}
        </button>
      </div>

      {/* nav */}
      <nav className="nav compact">
        <NavLink to="/chat" className="nav-item" title="Explore stocks, sectors, and broader market trends">
          <IconChat />
          <span>Market Watch</span>
        </NavLink>

        <NavLink to="/stock-buddy" className="nav-item" title="Get instant stock analysis and insights">
          <IconStockBuddy />
          <span>Stock Score</span>
        </NavLink>

        <div className="nav-section-title">PORTFOLIO ACCESS</div>

        <NavLink to="/portfolio" className="nav-item" title="Review your portfolio for tailored insights">
          <IconPortfolio />
          <span>Portfolio Pulse</span>
        </NavLink>

        <NavLink to="/reports" className="nav-item" title="Generate professional PDF reports">
          <IconReport />
          <span>Portfolio Report</span>
        </NavLink>
      </nav>

      <IndexTicker />

      {/* user inline chip at bottom */}
      <div className="sidebar-user small">
        <div className="sidebar-avatar tiny" aria-label={displayName}>
          {initial}
        </div>
        <div className="sidebar-identity">
          <div className="sidebar-name">{displayName}</div>
        </div>
      </div>
    </aside>
  );
}

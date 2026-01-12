import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Chat from "./pages/Chat";
import PortfolioChat from "./pages/PortfolioChat";
import Reports from "./pages/Reports";
import StockBuddy from "./pages/StockBuddy";
import About from "./pages/About";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import CookieSettings from "./pages/CookieSettings";
import { AuthProvider } from "./auth";
import TopNav from "./components/TopNav";
import ScrollToTop from "./components/ScrollToTop";
import "./styles.css";
import { MarketProvider } from "./state/MarketProvider";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ScrollToTop />
        <MarketProvider refreshMs={1000}>
          <TopNav />
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/portfolio" element={<PortfolioChat />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/stock-buddy" element={<StockBuddy />} />
            <Route path="/about" element={<About />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/cookie-settings" element={<CookieSettings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </MarketProvider>
      </BrowserRouter>
    </AuthProvider>
  );
}

import React from "react";
import { useNavigate } from "react-router-dom";
import RotatingText from "../components/RotatingText";
import "../components/RotatingText.css";
import Lottie from "lottie-react";
import financeAnim from "../assets/demo4.json";
import PlainFooter from "../components/PlainFooter";
import image from "../assets/fintech.png";
import GridBackground from "../components/GridBackground";
import FeatureBlocks from "../components/FeatureBlocks";

export default function Landing() {
  const nav = useNavigate();

  return (
    <div
      style={{
        minHeight: "calc(100vh - var(--topnav-h))",
        display: "grid",
        placeItems: "center",
        padding: "0 0 0 0",
        background:
          "radial-gradient(1000px 600px at 20% 10%, #1b2440 0%, transparent 60%), var(--bg)",
        overflowY: "auto",
        overflowX: "hidden"
      }}
    >
      <GridBackground
        gridSize="8:8"
        colors={{ background: "var(--bg)", borderColor: "rgba(254, 192, 148, 1)", borderSize: "1px", borderStyle: "solid" }}
        beams={{ count: 12, speed: 5, size: "6px", colors: ["#22d3ee", "#a78bfa", "#fb7185", "#60a5fa", "#34d399", "#fb923c"] }}
        style={{ minHeight: "calc(100vh - var(--topnav-h))", overflowY: "hidden", overflowX: "hidden", padding: "120px 24px 24px" }}
      >
        <div className="landing-grid">
          <div className="landing-card">
            <h1 className="hero-title">
              <span className="hero-dim">AI Investment Agent : </span>{" "}
              <RotatingText
                texts={["Ask about Trends.", "Grill your Holdings!", "Ship Polished Reports."]}
                mainClassName="hero-pill"
                staggerFrom="last"
                initial={{ y: "100%", opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: "-120%", opacity: 0 }}
                staggerDuration={0.02}
                splitLevelClassName="hero-pill-split"
                transition={{ type: "spring", damping: 30, stiffness: 200 }}
                rotationInterval={5000}
              />
            </h1>

            <p className="hero-sub">
              Track your portfolio, research markets, and get AI-driven recommendations.
            </p>

            {/* centered actions area */}
            <div className="hero-actions">
              <button
                className="button"
                onClick={() => nav("/login")}
              >
                Get Started
              </button>
            </div>
          </div>

          <div className="lottie-free">
            <Lottie
              animationData={financeAnim}
              loop
              autoplay
              rendererSettings={{ preserveAspectRatio: "xMidYMid meet" }}
              style={{ width: "100%", height: "100%" }}
            />
          </div>
        </div>
      </GridBackground>

      {/* Example: new sections you can append below the landing-grid */}
      <div className="below-landing">
        {/* add components here — they'll appear below and page will scroll */}
        <FeatureBlocks />

        {/* full-window hero image section */}
        {/* <div className="landing-full-image">
          <img
            src={image}
            alt="FinAgentAI Banner"
            className="landing-full-image-img"
          />
        </div> */}
        <div className="image-hero">
          <img
            src={image}
            alt="FinAgentAI Banner"
            className="image-hero-img"
          />

          <div className="image-hero-text">
            <h1>Meet Your 24/7 AI Portfolio Agent</h1>
            <p>
              One intelligent agent for your entire investment journey. From portfolio insights to market research to AI-driven stock analysis—your finance agent delivers everything you need to invest with confidence.
            </p>
            <button className="hero-learn-btn" onClick={() => nav("/login")}>
              Learn More
            </button>
          </div>
        </div>
        <PlainFooter />
      </div>
    </div>
  );
}

import React from "react";
import { Send, Mail, MapPin, Phone } from "lucide-react";
import { FaFacebookF, FaLinkedinIn, FaYoutube, FaXTwitter } from "react-icons/fa6";
import { Link } from "react-router-dom";

/**
 * PlainFooter — improved, accessible footer with icons
 * - Uses lucide-react icons for UI
 * - Uses react-icons/fa6 for social brands
 * - Accessible forms (labels, aria)
 */
export default function PlainFooter() {
  const [email, setEmail] = React.useState("");

  function handleSubscribe(e) {
    e.preventDefault();
    // TODO: hook up to newsletter API
    alert(`Subscribed with: ${email || "no-email"}`);
    setEmail("");
  }

  return (
    <footer className="plain-footer" role="contentinfo" aria-label="Site footer">
      <div className="plain-footer__container">
        <div className="plain-col plain-brand">
          <p>FinAgentAI</p>
          <p className="plain-lead">
            Market insights, portfolio chat & one-click reports - delivered simply.
          </p>

          <form className="plain-subscribe" onSubmit={handleSubscribe}>
            <label htmlFor="newsletter-email" className="sr-only">
              Email address
            </label>
            <div className="plain-subscribe__row">
              <input
                id="newsletter-email"
                className="plain-input"
                type="email"
                placeholder="you@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-label="Email for newsletter"
                required
              />
              <button
                type="submit"
                className="plain-btn plain-btn--icon plain-btn--orange"
                aria-label="Subscribe to newsletter"
              >
                <Send className="icon" />
              </button>
            </div>

          </form>
          <p className="plain-note">We only send product updates and important news.</p>
        </div>

        <div className="plain-col plain-links" aria-label="Quick links">
          <h4>Quick Links</h4>
          <nav className="plain-nav" aria-label="Footer quick links">
            <Link to="/">Home</Link>
            <Link to="/about">About</Link>
          </nav>
        </div>

        <div className="plain-col plain-contact" aria-label="Contact details">
          <h4>Contact</h4>
          <address className="plain-address">
            <div className="contact-row"><MapPin className="icon" /> Pune</div>
            <div className="contact-row"><Phone className="icon" /> +91 9287940258</div>
            <div className="contact-row"><Mail className="icon" />finagentai.team@gmail.com</div>
          </address>
        </div>

        <div className="plain-col plain-social">
          <h4>Follow Us On</h4>
          <div className="plain-socials" style={{ display: "flex", gap: "12px" }}>
            <a href="#" className="social-icon" aria-label="X (Twitter)">
              <FaXTwitter size={20} />
            </a>
            <a href="#" className="social-icon" aria-label="LinkedIn">
              <FaLinkedinIn size={20} />
            </a>
            <a href="#" className="social-icon" aria-label="Facebook">
              <FaFacebookF size={20} />
            </a>
            <a href="#" className="social-icon" aria-label="YouTube">
              <FaYoutube size={20} />
            </a>
          </div>
        </div>
      </div>

      <div className="plain-footer__bottom">
        <p className="muted">© {new Date().getFullYear()} FinAgentAI. All rights reserved.</p>
        <nav className="bottom-links" aria-label="Legal links">
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/cookie-settings">Cookie Settings</Link>
        </nav>
      </div>

      <style>{`
        .social-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background-color: #1e2024ff;
          color: #000;
          text-decoration: none;
          border: 0.5px solid transparent;
          transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .social-icon:hover {
          transform: scale(1.1);
          border-color: var(--accent-orange, #ff7a18);
        }
      `}</style>
    </footer>
  );
}

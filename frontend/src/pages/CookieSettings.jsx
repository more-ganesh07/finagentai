import React, { useState } from "react";
import { motion } from "motion/react";
import { Cookie, Settings, ToggleLeft, ToggleRight, Info, Save } from "lucide-react";
import PlainFooter from "../components/PlainFooter";
import "../styles/Legal.css";

export default function CookieSettings() {
    const [settings, setSettings] = useState({
        essential: true, // Always required
        analytics: true,
        marketing: false,
        preferences: true
    });

    const [saved, setSaved] = useState(false);

    const cookieTypes = [
        {
            id: "essential",
            title: "Essential Cookies",
            description: "These cookies are necessary for the website to function and cannot be disabled. They enable core functionality such as security, network management, and accessibility.",
            required: true,
            examples: "Session management, authentication, security tokens"
        },
        {
            id: "analytics",
            title: "Analytics Cookies",
            description: "These cookies help us understand how visitors interact with our website by collecting and reporting information anonymously. This helps us improve our services.",
            required: false,
            examples: "Google Analytics, user behavior tracking, performance monitoring"
        },
        {
            id: "marketing",
            title: "Marketing Cookies",
            description: "These cookies track your online activity to help advertisers deliver more relevant advertising or to limit how many times you see an ad.",
            required: false,
            examples: "Ad targeting, conversion tracking, retargeting pixels"
        },
        {
            id: "preferences",
            title: "Preference Cookies",
            description: "These cookies allow the website to remember choices you make (such as your language or region) and provide enhanced, more personal features.",
            required: false,
            examples: "Language preferences, theme settings, customization options"
        }
    ];

    const handleToggle = (id) => {
        if (id === "essential") return; // Can't toggle essential cookies
        setSettings(prev => ({
            ...prev,
            [id]: !prev[id]
        }));
        setSaved(false);
    };

    const handleSave = () => {
        // Here you would typically save to localStorage or send to backend
        localStorage.setItem("cookieSettings", JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };

    const handleAcceptAll = () => {
        setSettings({
            essential: true,
            analytics: true,
            marketing: true,
            preferences: true
        });
        setSaved(false);
    };

    const handleRejectAll = () => {
        setSettings({
            essential: true,
            analytics: false,
            marketing: false,
            preferences: false
        });
        setSaved(false);
    };

    return (
        <div className="legal-page">
            {/* Hero Section */}
            <section className="legal-hero">
                <div className="legal-hero-content">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5 }}
                        className="legal-icon-hero"
                    >
                        <Cookie size={48} color="#ff7a18" />
                    </motion.div>
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.1 }}
                        className="legal-hero-title"
                    >
                        Cookie Settings
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="legal-hero-subtitle"
                    >
                        Manage your cookie preferences and control your privacy
                    </motion.p>
                </div>
            </section>

            {/* Info Banner */}
            <section className="cookie-info">
                <div className="cookie-info-content">
                    <Info size={24} color="#ff7a18" />
                    <div>
                        <h3 className="cookie-info-title">What are cookies?</h3>
                        <p className="cookie-info-text">
                            Cookies are small text files that are placed on your device when you visit our website.
                            They help us provide you with a better experience by remembering your preferences and
                            understanding how you use our services.
                        </p>
                    </div>
                </div>
            </section>

            {/* Cookie Controls */}
            <section className="cookie-controls">
                <div className="legal-container">
                    <div className="cookie-actions">
                        <button className="cookie-btn cookie-btn-accept" onClick={handleAcceptAll}>
                            Accept All Cookies
                        </button>
                        <button className="cookie-btn cookie-btn-reject" onClick={handleRejectAll}>
                            Reject Non-Essential
                        </button>
                    </div>

                    {/* Cookie Types */}
                    <div className="cookie-types">
                        {cookieTypes.map((cookie, index) => (
                            <motion.div
                                key={cookie.id}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.4, delay: index * 0.1 }}
                                className="cookie-card"
                            >
                                <div className="cookie-card-header">
                                    <div className="cookie-card-title-group">
                                        <Settings size={20} color="#ff7a18" />
                                        <h3 className="cookie-card-title">{cookie.title}</h3>
                                        {cookie.required && <span className="cookie-required">Required</span>}
                                    </div>
                                    <button
                                        className={`cookie-toggle ${settings[cookie.id] ? "active" : ""}`}
                                        onClick={() => handleToggle(cookie.id)}
                                        disabled={cookie.required}
                                        aria-label={`Toggle ${cookie.title}`}
                                    >
                                        {settings[cookie.id] ? (
                                            <ToggleRight size={32} color="#ff7a18" />
                                        ) : (
                                            <ToggleLeft size={32} color="#8f9fb6" />
                                        )}
                                    </button>
                                </div>
                                <p className="cookie-card-description">{cookie.description}</p>
                                <div className="cookie-card-examples">
                                    <strong>Examples:</strong> {cookie.examples}
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* Save Button */}
                    <div className="cookie-save">
                        <button className="cookie-btn cookie-btn-save" onClick={handleSave}>
                            <Save size={20} />
                            Save Preferences
                        </button>
                        {saved && (
                            <motion.span
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="cookie-saved-message"
                            >
                                ✓ Settings saved successfully
                            </motion.span>
                        )}
                    </div>
                </div>
            </section>

            {/* Additional Info */}
            <section className="legal-contact">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="legal-contact-content"
                >
                    <Cookie size={32} color="#ff7a18" />
                    <h2 className="legal-contact-title">Need More Information?</h2>
                    <p className="legal-contact-text">
                        For more details about how we use cookies, please read our{" "}
                        <a href="/privacy">Privacy Policy</a>. If you have questions, contact us at{" "}
                        <a href="mailto:finagentai.team@gmail.com">finagentai.team@gmail.com</a>
                    </p>
                </motion.div>
            </section>

            <PlainFooter />
        </div>
    );
}

import React from "react";
import { motion } from "motion/react";
import { Shield, Lock, Eye, Database, UserCheck, AlertCircle } from "lucide-react";
import PlainFooter from "../components/PlainFooter";
import "../styles/Legal.css";

export default function Privacy() {
    const sections = [
        {
            icon: Database,
            title: "Information We Collect",
            content: [
                {
                    subtitle: "Personal Information",
                    text: "We collect information you provide directly to us, including your name, email address, and portfolio data when you create an account or use our services."
                },
                {
                    subtitle: "Usage Data",
                    text: "We automatically collect information about your interactions with our platform, including IP address, browser type, pages visited, and time spent on our services."
                },
                {
                    subtitle: "Financial Data",
                    text: "Portfolio holdings, transaction history, and investment preferences are collected to provide personalized insights and recommendations."
                }
            ]
        },
        {
            icon: Lock,
            title: "How We Use Your Information",
            content: [
                {
                    subtitle: "Service Delivery",
                    text: "We use your information to provide, maintain, and improve our AI-powered portfolio management services, including generating insights and reports."
                },
                {
                    subtitle: "Personalization",
                    text: "Your data helps us customize your experience, provide relevant recommendations, and deliver tailored financial insights."
                },
                {
                    subtitle: "Communication",
                    text: "We may send you service updates, security alerts, and promotional messages (which you can opt out of at any time)."
                }
            ]
        },
        {
            icon: Shield,
            title: "Data Security",
            content: [
                {
                    subtitle: "Encryption",
                    text: "All data is encrypted in transit using TLS 1.3 and at rest using AES-256 encryption standards."
                },
                {
                    subtitle: "Access Controls",
                    text: "We implement strict access controls and authentication mechanisms to ensure only authorized personnel can access your data."
                },
                {
                    subtitle: "Regular Audits",
                    text: "Our security practices are regularly audited by third-party security firms to maintain the highest standards."
                }
            ]
        },
        {
            icon: Eye,
            title: "Data Sharing",
            content: [
                {
                    subtitle: "Third-Party Services",
                    text: "We may share data with trusted service providers who assist in operating our platform, subject to strict confidentiality agreements."
                },
                {
                    subtitle: "Legal Requirements",
                    text: "We may disclose information when required by law, court order, or to protect our rights and the safety of our users."
                },
                {
                    subtitle: "No Selling",
                    text: "We never sell your personal information to third parties for marketing purposes."
                }
            ]
        },
        {
            icon: UserCheck,
            title: "Your Rights",
            content: [
                {
                    subtitle: "Access & Export",
                    text: "You have the right to access and export all your personal data at any time through your account settings."
                },
                {
                    subtitle: "Correction & Deletion",
                    text: "You can update or delete your information directly in your account or by contacting our support team."
                },
                {
                    subtitle: "Opt-Out",
                    text: "You can opt out of marketing communications and certain data collection practices at any time."
                }
            ]
        }
    ];

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
                        <Shield size={48} color="#ff7a18" />
                    </motion.div>
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.1 }}
                        className="legal-hero-title"
                    >
                        Privacy Policy
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="legal-hero-subtitle"
                    >
                        Your privacy is our priority. Learn how we collect, use, and protect your data.
                    </motion.p>
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.6, delay: 0.3 }}
                        className="legal-updated"
                    >
                        Last Updated: November 25, 2025
                    </motion.p>
                </div>
            </section>

            {/* Content Sections */}
            <section className="legal-content">
                <div className="legal-container">
                    {sections.map((section, index) => {
                        const Icon = section.icon;
                        return (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: index * 0.1 }}
                                className="legal-section"
                            >
                                <div className="legal-section-header">
                                    <div className="legal-section-icon">
                                        <Icon size={24} />
                                    </div>
                                    <h2 className="legal-section-title">{section.title}</h2>
                                </div>
                                <div className="legal-section-content">
                                    {section.content.map((item, idx) => (
                                        <div key={idx} className="legal-subsection">
                                            <h3 className="legal-subtitle">{item.subtitle}</h3>
                                            <p className="legal-text">{item.text}</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </section>

            {/* Contact Section */}
            <section className="legal-contact">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="legal-contact-content"
                >
                    <AlertCircle size={32} color="#ff7a18" />
                    <h2 className="legal-contact-title">Questions About Privacy?</h2>
                    <p className="legal-contact-text">
                        If you have any questions or concerns about our privacy practices, please contact us at{" "}
                        <a href="mailto:finagentai.team@gmail.com">finagentai.team@gmail.com</a>
                    </p>
                </motion.div>
            </section>

            <PlainFooter />
        </div>
    );
}

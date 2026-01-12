import React from "react";
import { motion } from "motion/react";
import { FileText, Scale, Ban, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import PlainFooter from "../components/PlainFooter";
import "../styles/Legal.css";

export default function Terms() {
    const sections = [
        {
            icon: CheckCircle,
            title: "Acceptance of Terms",
            content: [
                {
                    subtitle: "Agreement",
                    text: "By accessing or using FinAgentAI, you agree to be bound by these Terms of Service and all applicable laws and regulations. If you do not agree with any of these terms, you are prohibited from using our services."
                },
                {
                    subtitle: "Modifications",
                    text: "We reserve the right to modify these terms at any time. We will notify users of any material changes via email or through the platform. Continued use after changes constitutes acceptance."
                }
            ]
        },
        {
            icon: FileText,
            title: "Use of Service",
            content: [
                {
                    subtitle: "Eligibility",
                    text: "You must be at least 18 years old and capable of forming a binding contract to use our services. By using FinAgentAI, you represent that you meet these requirements."
                },
                {
                    subtitle: "Account Responsibility",
                    text: "You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. Notify us immediately of any unauthorized access."
                },
                {
                    subtitle: "Permitted Use",
                    text: "You may use FinAgentAI for lawful purposes only. You agree not to use the service to violate any laws, infringe on intellectual property rights, or engage in fraudulent activities."
                }
            ]
        },
        {
            icon: Ban,
            title: "Prohibited Activities",
            content: [
                {
                    subtitle: "Unauthorized Access",
                    text: "You may not attempt to gain unauthorized access to any part of the service, other user accounts, or computer systems connected to the service."
                },
                {
                    subtitle: "Interference",
                    text: "You may not interfere with or disrupt the service or servers/networks connected to the service, or disobey any requirements, procedures, policies, or regulations."
                },
                {
                    subtitle: "Misuse of Data",
                    text: "You may not use data mining, robots, or similar data gathering and extraction tools on the service without our express written consent."
                }
            ]
        },
        {
            icon: Scale,
            title: "Intellectual Property",
            content: [
                {
                    subtitle: "Ownership",
                    text: "All content, features, and functionality of FinAgentAI, including but not limited to text, graphics, logos, and software, are owned by FinAgentAI and protected by copyright, trademark, and other intellectual property laws."
                },
                {
                    subtitle: "Limited License",
                    text: "We grant you a limited, non-exclusive, non-transferable license to access and use the service for personal, non-commercial purposes in accordance with these terms."
                },
                {
                    subtitle: "User Content",
                    text: "You retain ownership of any content you submit to the service. By submitting content, you grant us a worldwide, royalty-free license to use, store, and display such content as necessary to provide the service."
                }
            ]
        },
        {
            icon: AlertTriangle,
            title: "Disclaimers & Limitations",
            content: [
                {
                    subtitle: "No Financial Advice",
                    text: "FinAgentAI provides information and tools for portfolio management but does not provide financial, investment, or legal advice. All decisions based on our insights are your sole responsibility."
                },
                {
                    subtitle: "Service Availability",
                    text: "We strive to maintain service availability but do not guarantee uninterrupted or error-free operation. We may suspend or terminate the service for maintenance or other reasons without liability."
                },
                {
                    subtitle: "Limitation of Liability",
                    text: "To the maximum extent permitted by law, FinAgentAI shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the service."
                }
            ]
        },
        {
            icon: XCircle,
            title: "Termination",
            content: [
                {
                    subtitle: "By You",
                    text: "You may terminate your account at any time by contacting our support team or through your account settings. Upon termination, your right to use the service will immediately cease."
                },
                {
                    subtitle: "By Us",
                    text: "We reserve the right to suspend or terminate your account if you violate these terms, engage in fraudulent activity, or for any other reason at our sole discretion."
                },
                {
                    subtitle: "Effect of Termination",
                    text: "Upon termination, all licenses and rights granted to you will immediately cease. We may delete your data in accordance with our data retention policies."
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
                        <Scale size={48} color="#ff7a18" />
                    </motion.div>
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.1 }}
                        className="legal-hero-title"
                    >
                        Terms of Service
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="legal-hero-subtitle"
                    >
                        Please read these terms carefully before using FinAgentAI
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
                    <FileText size={32} color="#ff7a18" />
                    <h2 className="legal-contact-title">Questions About Terms?</h2>
                    <p className="legal-contact-text">
                        If you have any questions about these Terms of Service, please contact us at{" "}
                        <a href="mailto:finagentai.team@gmail.com">finagentai.team@gmail.com</a>
                    </p>
                </motion.div>
            </section>

            <PlainFooter />
        </div>
    );
}

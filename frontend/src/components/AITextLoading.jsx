import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";

export default function AITextLoading({
    texts = [
        "Thinking...",
        "Processing...",
        "Analyzing...",
        "Computing...",
        "Generating...",
        "Almost...",
    ],
    interval = 1300,
}) {
    const [currentTextIndex, setCurrentTextIndex] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTextIndex((prevIndex) => {
                // If we've reached the last one, don't increment anymore
                if (prevIndex === texts.length - 1) {
                    return prevIndex;
                }
                return prevIndex + 1;
            });
        }, interval);

        return () => clearInterval(timer);
    }, [interval, texts.length]);

    return (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-start", padding: "0 1rem" }}>
            <motion.div
                style={{ position: "relative", width: "auto" }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4 }}
            >
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentTextIndex}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{
                            opacity: 1,
                            y: 0,
                            backgroundPosition: ["200% center", "-200% center"],
                        }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{
                            opacity: { duration: 0.3 },
                            y: { duration: 0.3 },
                            backgroundPosition: {
                                duration: 2.5,
                                ease: "linear",
                                repeat: currentTextIndex === texts.length - 1 ? 0 : Infinity,
                            },
                        }}
                        style={{
                            display: "flex",
                            justifyContent: "flex-start",
                            fontSize: "0.95rem",
                            fontWeight: "500",
                            background: "linear-gradient(to right, #ffffff, #737373, #ffffff)",
                            backgroundSize: "200% 100%",
                            WebkitBackgroundClip: "text",
                            backgroundClip: "text",
                            color: "transparent",
                            whiteSpace: "nowrap",
                            minWidth: "max-content",
                        }}
                    >
                        {texts[currentTextIndex]}
                    </motion.div>
                </AnimatePresence>
            </motion.div>
        </div>
    );
}

import React from "react";
import { motion } from "framer-motion";
import { Zap, Clock, TrendingUp, LineChart, PieChart, Activity } from "lucide-react";

const FloatingBackground = ({ type = "market" }) => {
    // Define icons and colors based on chat type
    const icons = [
        { Icon: Zap, color: "#ff7a18", size: 32, top: "15%", left: "10%", delay: 0 },
        { Icon: Clock, color: "#22d3ee", size: 28, top: "25%", right: "15%", delay: 1 },
        { Icon: TrendingUp, color: "#a78bfa", size: 36, bottom: "20%", left: "20%", delay: 2 },
        { Icon: LineChart, color: "#fbbf24", size: 30, top: "60%", right: "10%", delay: 1.5 },
        { Icon: PieChart, color: "#38ef7d", size: 34, top: "40%", left: "5%", delay: 0.5 },
        { Icon: Activity, color: "#00B4DB", size: 26, bottom: "10%", right: "25%", delay: 2.5 },
    ];

    return (
        <div className="floating-bg-icons">
            <style>{`
        .floating-bg-icons {
          position: absolute;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          overflow: hidden;
          opacity: 0.15; /* Subtle background presence */
        }
        .floating-icon-wrap {
          position: absolute;
        }
      `}</style>
            {icons.map((item, idx) => (
                <motion.div
                    key={idx}
                    className="floating-icon-wrap"
                    style={{
                        top: item.top,
                        left: item.left,
                        right: item.right,
                        bottom: item.bottom,
                    }}
                    animate={{
                        y: [0, -15, 0],
                        rotate: [0, 5, -5, 0],
                        opacity: [0.3, 0.6, 0.3],
                    }}
                    transition={{
                        duration: 4 + Math.random() * 2,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: item.delay,
                    }}
                >
                    <item.Icon size={item.size} color={item.color} />
                </motion.div>
            ))}
        </div>
    );
};

export default FloatingBackground;

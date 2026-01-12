import React from "react";
import "./GridBackground.css";
/**
 * GridBackground
 * - Props:
 *    - gridSize: "cols:rows" string (e.g. "8:8")
 *    - colors: { background, borderColor, borderSize, borderStyle }
 *    - beams: { count, colors, size, shadow, speed }
 * - children rendered on top of the visual background
 */

export default function GridBackground({
  children,
  gridSize = "8:8",
  colors = {},
  beams = {},
  className = "",
  ...rest
}) {
  const {
    background = "var(--bg)", // default page background variable you already have
    borderColor = "rgba(255,255,255,0.04)",
    borderSize = "1px",
    borderStyle = "solid",
  } = colors;

  const {
    count = 10,
    colors: beamColors = [
      "#22d3ee", // cyan
      "#a78bfa", // purple
      "#fb7185", // rose-ish
      "#60a5fa", // blue
      "#34d399", // green
      "#fb923c", // orange
      "#f472b6", // pink
      "#f97316", // amber
    ],
    size = "8px", // beam thickness (approx)
    shadow = "0 6px 20px rgba(0,0,0,0.4)",
    speed = 5,
  } = beams;

  // parse cols and rows
  const [cols, rows] = ("" + gridSize).split(":").map((n) => Math.max(1, Number(n) || 8));

  // create beams config once
  const animatedBeams = React.useMemo(() => {
    return Array.from({ length: Math.min(count, 24) }).map((_, i) => {
      const direction = Math.random() > 0.5 ? "horizontal" : "vertical";
      const startPosition = Math.random() > 0.5 ? "start" : "end";
      const gridLine =
        direction === "horizontal"
          ? Math.floor(Math.random() * Math.max(1, rows - 1)) + 1
          : Math.floor(Math.random() * Math.max(1, cols - 1)) + 1;
      const delay = Number((Math.random() * 3).toFixed(2)); // 0-3s
      const duration = Number((speed + Math.random() * 3).toFixed(2)); // speed..speed+3
      const color = beamColors[i % beamColors.length];

      return { id: i, direction, startPosition, gridLine, delay, duration, color };
    });
  }, [count, beamColors, cols, rows, speed]);

  // inline CSS variables for background + border
  const wrapperStyle = {
    ["--grid-bg"]: background,
    ["--grid-border-color"]: borderColor,
    ["--grid-border-size"]: borderSize,
    ["--grid-border-style"]: borderStyle,
  };

  return (
    <div
      className={`grid-bg-wrapper ${className}`}
      style={wrapperStyle}
      {...rest}
    >
      {/* Grid container */}
      <div
        className="grid-bg-grid"
        style={{
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gridTemplateRows: `repeat(${rows}, 1fr)`,
          borderRight: `${borderSize} ${borderStyle} ${borderColor}`,
          borderBottom: `${borderSize} ${borderStyle} ${borderColor}`,
        }}
        aria-hidden
      >
        {Array.from({ length: cols * rows }).map((_, idx) => (
          <div
            key={idx}
            className="grid-bg-cell"
            style={{
              borderTop: `${borderSize} ${borderStyle} ${borderColor}`,
              borderLeft: `${borderSize} ${borderStyle} ${borderColor}`,
            }}
          />
        ))}
      </div>

      {/* Beams */}
      {animatedBeams.map((b) => {
        const horizontalPosPct = (b.gridLine / rows) * 100;
        const verticalPosPct = (b.gridLine / cols) * 100;

        // CSS custom props used by the stylesheet keyframes
        const beamStyle = {
          "--beam-color": b.color,
          "--beam-duration": `${b.duration}s`,
          "--beam-delay": `${b.delay}s`,
          "--beam-size": size,
          "--beam-shadow": shadow,
          // distance for translate (used in keyframes as CSS var)
          "--beam-distance": "calc(100vw + 48px)",
          // direction multiplier (1 or -1) used in calc with --beam-distance
          "--beam-dir": b.startPosition === "start" ? 1 : -1,
        };

        if (b.direction === "horizontal") {
          beamStyle.top = `${horizontalPosPct}%`;
          beamStyle.left = b.startPosition === "start" ? `-24px` : `calc(100% + 24px)`;
          // center on line
          beamStyle.transform = "translateY(-50%)";
        } else {
          beamStyle.left = `${verticalPosPct}%`;
          beamStyle.top = b.startPosition === "start" ? `-24px` : `calc(100% + 24px)`;
          beamStyle.transform = "translateX(-50%)";
        }

        const beamClass = `grid-beam ${b.direction === "horizontal" ? "beam-h" : "beam-v"}`;

        return <div key={b.id} className={beamClass} style={beamStyle} aria-hidden />;
      })}

      {/* Content layer */}
      <div className="grid-bg-content">{children}</div>
    </div>
  );
}

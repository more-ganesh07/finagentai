// "use client";

// import { Mic } from "lucide-react";
// import { useState, useEffect, useRef } from "react";
// import "./AI_Voice.css";

// /**
//  * Props:
//  *  - onTranscript(text: string) => void
//  *  - onListeningChange(isListening: boolean) => void
//  *  - autoSendOnStop (boolean) optional
//  */
// export default function AI_Voice({ onTranscript = () => {}, onListeningChange = () => {}, autoSendOnStop = false }) {
//   const [submitted, setSubmitted] = useState(false); // 'listening' state
//   const [time, setTime] = useState(0);
//   const [isClient, setIsClient] = useState(false);
//   const [isDemo, setIsDemo] = useState(false);
//   const recognitionRef = useRef(null);
//   const finalTranscriptRef = useRef("");

//   useEffect(() => setIsClient(true), []);

//   // timer while listening
//   useEffect(() => {
//     let intervalId;
//     if (submitted) {
//       intervalId = setInterval(() => setTime((t) => t + 1), 1000);
//     } else {
//       setTime(0);
//     }
//     return () => clearInterval(intervalId);
//   }, [submitted]);

//   const formatTime = (seconds) => {
//     const mins = Math.floor(seconds / 60);
//     const secs = seconds % 60;
//     return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
//   };

//   // Setup Web Speech API (if available)
//   useEffect(() => {
//     const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
//     if (!SpeechRecognition) {
//       setIsDemo(true);
//       return;
//     }

//     const r = new SpeechRecognition();
//     r.lang = "en-US";
//     r.interimResults = true;
//     r.continuous = false;
//     recognitionRef.current = r;

//     r.onstart = () => {
//       finalTranscriptRef.current = "";
//       setSubmitted(true);
//       onListeningChange(true);
//     };

//     r.onresult = (event) => {
//       let interim = "";
//       let final = "";
//       for (let i = event.resultIndex; i < event.results.length; i++) {
//         const res = event.results[i];
//         if (res.isFinal) final += res[0].transcript;
//         else interim += res[0].transcript;
//       }
//       if (final) {
//         finalTranscriptRef.current += final;
//         onTranscript(finalTranscriptRef.current.trim());
//       } else {
//         onTranscript((finalTranscriptRef.current + " " + interim).trim());
//       }
//     };

//     r.onerror = (e) => {
//       console.warn("SpeechRecognition error", e);
//       setIsDemo(true);
//       setSubmitted(false);
//       onListeningChange(false);
//     };

//     r.onend = () => {
//       setSubmitted(false);
//       onListeningChange(false);
//       if (finalTranscriptRef.current) {
//         onTranscript(finalTranscriptRef.current.trim());
//         if (autoSendOnStop) {
//           // parent handles sending if desired via onTranscript + listening change
//         }
//       }
//     };

//     return () => {
//       try {
//         r.onstart = null;
//         r.onresult = null;
//         r.onend = null;
//         r.onerror = null;
//         r.stop && r.stop();
//       } catch {}
//     };
//   }, [onTranscript, onListeningChange, autoSendOnStop]);

//   // Demo animation runner
//   useEffect(() => {
//     if (!isDemo) return;
//     let timeoutId;
//     const runAnimation = () => {
//       setSubmitted(true);
//       timeoutId = setTimeout(() => {
//         setSubmitted(false);
//         timeoutId = setTimeout(runAnimation, 1000);
//       }, 3000);
//     };
//     const initialTimeout = setTimeout(runAnimation, 100);
//     return () => {
//       clearTimeout(timeoutId);
//       clearTimeout(initialTimeout);
//     };
//   }, [isDemo]);

//   const startRecognition = () => {
//     const r = recognitionRef.current;
//     if (r) {
//       try {
//         r.start();
//       } catch (e) {
//         console.debug("recognition start failed", e);
//       }
//     } else {
//       setIsDemo(true);
//       setSubmitted(true);
//       onListeningChange(true);
//       setTimeout(() => {
//         const fake = "This is a demo transcription.";
//         onTranscript(fake);
//         setSubmitted(false);
//         onListeningChange(false);
//       }, 3000);
//     }
//   };

//   const stopRecognition = () => {
//     const r = recognitionRef.current;
//     if (r) {
//       try {
//         r.stop();
//       } catch {}
//     } else {
//       setSubmitted(false);
//       onListeningChange(false);
//     }
//   };

//   const handleClick = () => {
//     if (submitted) {
//       stopRecognition();
//     } else {
//       finalTranscriptRef.current = "";
//       startRecognition();
//     }
//   };

//   return (
//     <div className="ai-voice">
//       <div className="ai-voice__inner">
//         <button
//           className={`ai-voice__button ${submitted ? "ai-voice__button--active" : ""}`}
//           type="button"
//           onClick={handleClick}
//           aria-pressed={submitted}
//           aria-label={submitted ? "Stop listening" : "Start voice input"}
//         >
//           {submitted ? (
//             <div className="ai-voice__spinner" aria-hidden="true" />
//           ) : (
//             <Mic className="ai-voice__mic" />
//           )}
//         </button>

//         <span className={`ai-voice__time ${submitted ? "ai-voice__time--active" : ""}`}>
//           {formatTime(time)}
//         </span>

//         <div className="ai-voice__bars" aria-hidden="true">
//           {[...Array(32)].map((_, i) => {
//             const style = submitted && isClient ? { height: `${8 + Math.random() * 72}%`, animationDelay: `${i * 0.04}s` } : {};
//             return <div key={i} className={`ai-voice__bar ${submitted ? "ai-voice__bar--active" : ""}`} style={style} />;
//           })}
//         </div>

//         <p className="ai-voice__caption">{submitted ? "Listening..." : "Click to speak"}</p>
//       </div>
//     </div>
//   );
// }


"use client";
import { Mic } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import "./AI_Voice.css";
import { sttStart, sttStop, sttStream } from "../services/api";

/**
 * Small, plain-CSS mic button component.
 * Props:
 *  - variant: "button" (default) | "panel" (not used now)
 *  - disabled: boolean (if true, button is disabled and shows tooltip)
 *  - onTranscript / onListeningChange left for future use but won't be triggered when disabled
 */
export default function AI_Voice({
  variant = "button",
  disabled = false,
  onTranscript = () => { },
  onListeningChange = () => { },
}) {
  const [listening, setListening] = useState(false);
  const [countdown, setCountdown] = useState(null); // Countdown 3, 2, 1
  const abortControllerRef = useRef(null);
  const committedTextRef = useRef(""); // To store finalized sentences
  const pendingTurnRef = useRef(""); // To store the latest final version of a turn (potentially unformatted)

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (listening) {
        handleStop();
      }
    };
  }, []);

  const handleStart = async () => {
    try {
      setListening(true);
      onListeningChange(true);
      committedTextRef.current = ""; // Reset on new session
      pendingTurnRef.current = "";

      // 1. Tell backend to start recording
      await sttStart();

      // 2. Start streaming transcripts
      const controller = new AbortController();
      abortControllerRef.current = controller;

      // Start the stream in background
      sttStream(
        (data) => {
          // data = { text: "...", is_final: boolean, is_formatted: boolean }
          const text = data.text || "";
          const isFinal = data.is_final;
          const isFormatted = data.is_formatted;

          if (!isFinal && pendingTurnRef.current) {
            // A new turn started, so we commit the previous one now if it wasn't already
            const p = committedTextRef.current;
            committedTextRef.current = p ? p + " " + pendingTurnRef.current : pendingTurnRef.current;
            pendingTurnRef.current = "";
          }

          const prefix = committedTextRef.current ? committedTextRef.current + " " : "";
          const displayText = prefix + text;

          onTranscript(displayText);

          if (isFinal) {
            if (isFormatted) {
              // Definitive version received, commit immediately and clear pending
              committedTextRef.current = displayText;
              pendingTurnRef.current = "";
            } else {
              // Final but raw, hold as pending in case a formatted one follows
              pendingTurnRef.current = text;
            }
          }
        },
        controller.signal
      ).catch(err => {
        if (err.name !== 'AbortError') {
          console.error("Stream failed:", err);
          handleStop();
        }
      });

    } catch (e) {
      console.error("Failed to start voice:", e);
      setListening(false);
      onListeningChange(false);
    }
  };

  const handleStop = async () => {
    try {
      // 1. Abort the stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }

      // If we had a final unformatted turn that never got a formatted counterpart, commit it now
      if (pendingTurnRef.current) {
        const p = committedTextRef.current;
        committedTextRef.current = p ? p + " " + pendingTurnRef.current : pendingTurnRef.current;
        pendingTurnRef.current = "";
      }

      // 2. Tell backend to stop recording
      await sttStop();

    } catch (e) {
      console.error("Failed to stop voice:", e);
    } finally {
      setListening(false);
      onListeningChange(false);
    }
  };

  const handleClick = () => {
    if (disabled || countdown !== null) return;

    if (listening) {
      handleStop();
    } else {
      // Start 3-2-1 countdown
      let count = 3;
      setCountdown(count);

      const interval = setInterval(() => {
        count -= 1;
        if (count > 0) {
          setCountdown(count);
        } else {
          clearInterval(interval);
          setCountdown(null);
          handleStart();
        }
      }, 1000);
    }
  };

  // only rendering the compact button variant (as requested)
  return (
    <span className="ai-voice-tooltip" data-tooltip={disabled ? "Voice feature coming soon" : ""}>
      {listening && (
        <div className="ai-voice-waves">
          <div className="ai-voice-wave"></div>
          <div className="ai-voice-wave"></div>
          <div className="ai-voice-wave"></div>
        </div>
      )}
      <button
        className={`ai-voice-btn ${disabled ? "ai-voice-btn--disabled" : ""} ${listening ? "ai-voice-btn--listening" : ""} ${countdown !== null ? "ai-voice-btn--countdown" : ""}`}
        type="button"
        onClick={handleClick}
        aria-pressed={listening}
        aria-label={disabled ? "Voice (coming soon)" : (listening ? "Stop listening" : "Start voice input")}
        disabled={disabled}
      >
        {countdown !== null ? (
          <span className="countdown-text">{countdown}</span>
        ) : (
          <Mic className="mic-icon" />
        )}
      </button>
    </span>
  );
}

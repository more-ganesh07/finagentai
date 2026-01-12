import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { getMarketIndices, marketIndicesStream } from "../services/api";

const MarketCtx = createContext(null);
export const useMarket = () => useContext(MarketCtx);

/** App-wide market provider with live streaming during market hours and polling otherwise */
export function MarketProvider({ children, refreshMs = 30000 }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  // Helper to check if Indian Market is open (9:15 AM - 3:30 PM IST, Mon-Fri)
  const isMarketOpen = () => {
    try {
      const options = { timeZone: "Asia/Kolkata", hour12: false };
      const formatter = new Intl.DateTimeFormat("en-US", {
        ...options,
        weekday: "short",
        hour: "numeric",
        minute: "numeric",
      });
      const parts = formatter.formatToParts(new Date());
      const getValue = (type) => parts.find((p) => p.type === type).value;

      const weekday = getValue("weekday");
      const hour = parseInt(getValue("hour"), 10);
      const minute = parseInt(getValue("minute"), 10);

      const isWeekday = ["Mon", "Tue", "Wed", "Thu", "Fri"].includes(weekday);
      const totalMinutes = hour * 60 + minute;

      // 9:15 AM = 555, 3:30 PM = 930
      return isWeekday && totalMinutes >= 555 && totalMinutes <= 930;
    } catch (e) {
      console.error("Error checking market hours:", e);
      return false;
    }
  };

  // Map backend structure to frontend structure
  // Map backend structure to frontend structure
  const transformData = (raw) => {
    if (!raw || raw.status !== "success" || !raw.data) return null;
    const d = raw.data;

    // Case-insensitive lookup helper
    const getIdx = (name) => {
      const key = Object.keys(d).find(k => k.toUpperCase() === name.toUpperCase());
      return d[key] || {};
    };

    return {
      nifty: {
        price: getIdx("NIFTY").current || 0,
        pct: getIdx("NIFTY").change_percent || 0,
      },
      sensex: {
        price: getIdx("SENSEX").current || 0,
        pct: getIdx("SENSEX").change_percent || 0,
      },
      fin: {
        price: getIdx("FINNIFTY").current || 0,
        pct: getIdx("FINNIFTY").change_percent || 0,
      },
      ts: raw.timestamp ? new Date(raw.timestamp).getTime() : Date.now(),
    };
  };

  const fetchStatic = async () => {
    try {
      const snap = await getMarketIndices();
      setData(transformData(snap));
      setError(null);
    } catch (e) {
      setError(e?.message || "Market feed error");
    }
  };

  const startUpdates = () => {
    // Clear any existing listeners/timers
    if (streamRef.current) {
      streamRef.current.abort();
      streamRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (isMarketOpen()) {
      console.log("Market is open - starting live stream");
      // Use SSE for real-time updates
      streamRef.current = marketIndicesStream((rawStream) => {
        setData(transformData(rawStream));
        setError(null);
      });

      // Check once a minute if market closed so we can switch to static mode
      timerRef.current = setInterval(() => {
        if (!isMarketOpen()) {
          startUpdates();
        }
      }, 60000);

    } else {
      console.log("Market is closed - fetching LTP once");
      fetchStatic();
      // NO setInterval for fetchStatic here - we already have the LTP.

      // Check every minute ONLY to see if market has opened
      timerRef.current = setInterval(() => {
        if (isMarketOpen()) {
          startUpdates();
        }
      }, 60000);
    }
  };

  useEffect(() => {
    startUpdates();

    const onVisibility = () => {
      if (!document.hidden) {
        startUpdates();
      } else {
        // Stop stream/timers when hidden to save resources
        if (streamRef.current) streamRef.current.abort();
        if (timerRef.current) clearInterval(timerRef.current);
      }
    };

    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      if (streamRef.current) streamRef.current.abort();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const value = { data, error, refresh: fetchStatic };
  return <MarketCtx.Provider value={value}>{children}</MarketCtx.Provider>;
}

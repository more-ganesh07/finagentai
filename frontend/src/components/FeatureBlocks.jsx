import React from 'react';
import { motion } from 'motion/react';
import {
  CheckCircle2, PieChart, TrendingUp, Search, Zap,
  FileText, Mail, Shield, BarChart3, Clock
} from 'lucide-react';
import './FeatureBlocks.css';

const FeatureBlocks = () => {
  return (
    <div className="feature-blocks-container">
      {/* Block 1: Automated Reporting (Now first) */}
      <div className="feature-row">
        <div className="feature-visual">
          {/* Floating Stat Top Right */}
          <motion.div
            className="floating-stat-card top"
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
          >
            <span className="label">Portfolio Health</span>
            <span className="value" style={{ color: '#22c55e' }}>92%</span>
          </motion.div>

          {/* Floating Stat Bottom Left */}
          <motion.div
            className="floating-stat-card bottom"
            initial={{ y: -10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1, duration: 0.6 }}
          >
            <span className="label">Last Generated</span>
            <span className="value" style={{ fontSize: '0.85rem' }}>2 mins ago</span>
          </motion.div>

          {/* New Floating Stat Top Left */}
          <motion.div
            className="floating-stat-card top-left"
            initial={{ x: -10, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.6 }}
          >
            <span className="label">Risk Level</span>
            <span className="value" style={{ color: '#f59e0b' }}>Medium</span>
          </motion.div>

          {/* New Floating Stat Bottom Right */}
          <motion.div
            className="floating-stat-card bottom-right"
            initial={{ x: 10, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 1.4, duration: 0.6 }}
          >
            <span className="label">Holdings</span>
            <span className="value">24 Stocks</span>
          </motion.div>

          <motion.div
            initial={{ scale: 0.95, opacity: 0.9 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }}
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
              width: '180px',
              height: '240px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.15)',
              display: 'flex',
              flexDirection: 'column',
              padding: '24px',
              boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
              position: 'relative',
              zIndex: 1
            }}
          >
            {/* ... inner contents ... */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ width: '50%', height: '10px', background: 'rgba(255,255,255,0.25)', borderRadius: '5px' }} />
              <div style={{ width: '20%', height: '10px', background: 'rgba(255,255,255,0.1)', borderRadius: '5px' }} />
            </div>

            <div style={{
              width: '100%',
              height: '80px',
              background: 'rgba(0,0,0,0.3)',
              borderRadius: '10px',
              marginBottom: '20px',
              overflow: 'hidden',
              position: 'relative',
              border: '1px solid rgba(255,255,255,0.05)'
            }}>
              <svg viewBox="0 0 100 40" width="100%" height="100%" preserveAspectRatio="none" style={{ display: 'block' }}>
                <defs>
                  <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style={{ stopColor: 'var(--accent-orange)', stopOpacity: 0.4 }} />
                    <stop offset="100%" style={{ stopColor: 'var(--accent-orange)', stopOpacity: 0 }} />
                  </linearGradient>
                </defs>
                <path d="M0,40 Q20,35 40,15 T100,20 V40 H0 Z" fill="url(#grad)" />
                <path d="M0,40 Q20,35 40,15 T100,20" fill="none" stroke="var(--accent-orange)" strokeWidth="3" strokeLinecap="round" />
              </svg>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.15)', borderRadius: '3px' }} />
              <div style={{ width: '92%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }} />
              <div style={{ width: '60%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }} />
            </div>

            <motion.div
              initial={{ scale: 0, rotate: -45 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.5, type: 'spring', stiffness: 200, damping: 15 }}
              style={{
                position: 'absolute',
                bottom: '20px',
                right: '20px',
                background: '#22c55e',
                borderRadius: '50%',
                padding: '8px',
                display: 'flex',
                boxShadow: '0 8px 20px rgba(34, 197, 94, 0.4)'
              }}
            >
              <CheckCircle2 size={24} color="#fff" />
            </motion.div>
          </motion.div>
        </div>
        <div className="feature-content">
          <h2 className="feature-title">Portfolio Report</h2>
          <p className="feature-desc">
            Transform your portfolio data into beautiful, comprehensive PDF reports instantly.
            Get detailed holdings analysis, performance metrics, risk assessment, and visual charts—all formatted to institutional standards and ready to share with advisors or clients.
          </p>
        </div>
      </div>

      {/* Block 2: Portfolio Analytics (Second, reverse) */}
      <div className="feature-row reverse">
        <div className="feature-visual">
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1.5fr 1fr',
            gridTemplateRows: '1fr 1fr',
            gap: '12px',
            width: '90%',
            height: '80%'
          }}>
            {/* Widget 1: Bar Chart */}
            <div style={{
              gridRow: '1 / -1',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '12px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              border: '1px solid rgba(255,255,255,0.08)'
            }}>
              <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginBottom: '8px' }}>Performance</div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', height: '100%' }}>
                {[1, 2, 3, 4, 5].map((i) => (
                  <motion.div
                    key={i}
                    initial={{ height: '20%' }}
                    animate={{ height: ['20%', '60%', '40%', '80%', '50%'] }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      repeatType: "reverse",
                      delay: i * 0.1,
                      ease: "easeInOut"
                    }}
                    style={{
                      flex: 1,
                      background: 'linear-gradient(to top, var(--accent-orange), #ffb74d)',
                      borderRadius: '4px',
                      opacity: 0.8
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Widget 2: Pie Chart */}
            <div style={{
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(255,255,255,0.08)',
              position: 'relative'
            }}>
              <div style={{
                width: '50px',
                height: '50px',
                borderRadius: '50%',
                background: 'conic-gradient(var(--accent-orange) 0% 65%, #a78bfa 65% 85%, #22d3ee 85% 100%)',
                position: 'relative'
              }}>
                <div style={{ position: 'absolute', inset: '12px', background: '#1b2440', borderRadius: '50%' }} />
              </div>
              <span style={{ position: 'absolute', bottom: '8px', fontSize: '0.65rem', color: '#9ca3af' }}>Alloc</span>
            </div>

            {/* Widget 3: Stat Card */}
            <div style={{
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '12px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              border: '1px solid rgba(255,255,255,0.08)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <TrendingUp size={14} color="#22c55e" />
                <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Return</span>
              </div>
              <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>+24.8%</span>
            </div>
          </div>
        </div>
        <div className="feature-content">
          <h2 className="feature-title">Portfolio Pulse</h2>
          <p className="feature-desc">
            Talk to your portfolio like you'd talk to your financial advisor. Ask about your holdings, analyze individual stocks with live market data, check margin availability, track orders, or get portfolio insights—all through simple conversation. AI-powered analysis meets real-time Zerodha integration.          </p>
        </div>
      </div>

      {/* Block 3: Explore Markets (Third, normal) */}
      <div className="feature-row">
        <div className="feature-visual">
          <div style={{ position: 'relative', width: '100%', height: '100%', padding: '20px' }}>
            {/* Msg 1: User */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0 }}
              style={{
                position: 'absolute',
                top: '10%',
                left: '10%',
                background: 'rgba(255,255,255,0.1)',
                padding: '10px 16px',
                borderRadius: '12px 12px 12px 0',
                border: '1px solid rgba(255,255,255,0.1)',
                maxWidth: '200px'
              }}
            >
              <span style={{ color: '#fff', fontSize: '0.85rem' }}>Search Top Midcap Gains?</span>
            </motion.div>

            {/* Msg 2: Bot */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 1.2 }}
              style={{
                position: 'absolute',
                top: '32%',
                right: '10%',
                background: '#ffb74d',
                padding: '10px 16px',
                borderRadius: '12px 12px 0 12px',
                color: '#000',
                maxWidth: '200px'
              }}
            >
              <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>Fetching top performers...</span>
            </motion.div>

            {/* Msg 3: User */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 2.5 }}
              style={{
                position: 'absolute',
                top: '54%',
                left: '10%',
                background: 'rgba(255,255,255,0.1)',
                padding: '10px 16px',
                borderRadius: '12px 12px 12px 0',
                border: '1px solid rgba(255,255,255,0.1)',
                maxWidth: '200px'
              }}
            >
              <span style={{ color: '#fff', fontSize: '0.85rem' }}>Compare IT vs Energy?</span>
            </motion.div>

            {/* Msg 4: Bot */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 3.8 }}
              style={{
                position: 'absolute',
                top: '76%',
                right: '10%',
                background: '#ffb74d',
                padding: '10px 16px',
                borderRadius: '12px 12px 0 12px',
                color: '#000',
                maxWidth: '200px'
              }}
            >
              <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>IT leading by 8.4%</span>
            </motion.div>
          </div>
        </div>
        <div className="feature-content">
          <h2 className="feature-title">Market Watch</h2>
          <p className="feature-desc">
            Leverage conversational AI to conduct comprehensive market research across equities, news, and analysis. Query any sector, compare performance trends, identify gainers and losers, or discover emerging opportunities. Lightning-fast insights combining real-time data and market intelligence, delivered through simple natural language queries          </p>
        </div>
      </div>

      {/* Block 4: Stock Buddy (New, Fourth, reverse) */}
      <div className="feature-row reverse">
        <div className="feature-visual">
          <div style={{ width: '85%', height: '85%', position: 'relative' }}>
            {/* Search Mock */}
            <div style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '12px',
              padding: '10px 15px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              border: '1px solid rgba(255,255,255,0.1)',
              marginBottom: '15px'
            }}>
              <Search size={16} color="#9ca3af" />
              <div style={{ color: '#fff', fontSize: '0.9rem', flex: 1 }}>RELIANCE</div>
              <motion.div
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                style={{ width: '2px', height: '16px', background: 'var(--accent-orange)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {/* Buy, Hold, Sell Blocks */}
              <div style={{ gridColumn: '1 / -1', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                <motion.div
                  initial={{ y: 15, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  style={{
                    background: 'rgba(56, 239, 125, 0.04)',
                    border: '1px solid rgba(56, 239, 125, 0.15)',
                    borderTop: '2px solid #10b981',
                    borderRadius: '12px',
                    padding: '10px 5px',
                    textAlign: 'center'
                  }}
                >
                  <div style={{ fontSize: '0.6rem', color: '#10b981', fontWeight: '800', marginBottom: '2px' }}>BUY</div>
                  <div style={{ fontSize: '1.1rem', color: '#fff', fontWeight: '800' }}>18</div>
                </motion.div>

                <motion.div
                  initial={{ y: 15, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  style={{
                    background: 'rgba(245, 158, 11, 0.04)',
                    border: '1px solid rgba(245, 158, 11, 0.15)',
                    borderTop: '2px solid #f59e0b',
                    borderRadius: '12px',
                    padding: '10px 5px',
                    textAlign: 'center'
                  }}
                >
                  <div style={{ fontSize: '0.6rem', color: '#f59e0b', fontWeight: '800', marginBottom: '2px' }}>HOLD</div>
                  <div style={{ fontSize: '1.1rem', color: '#fff', fontWeight: '800' }}>04</div>
                </motion.div>

                <motion.div
                  initial={{ y: 15, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.7 }}
                  style={{
                    background: 'rgba(239, 68, 68, 0.04)',
                    border: '1px solid rgba(239, 68, 68, 0.15)',
                    borderTop: '2px solid #ef4444',
                    borderRadius: '12px',
                    padding: '10px 5px',
                    textAlign: 'center'
                  }}
                >
                  <div style={{ fontSize: '0.6rem', color: '#ef4444', fontWeight: '800', marginBottom: '2px' }}>SELL</div>
                  <div style={{ fontSize: '1.1rem', color: '#fff', fontWeight: '800' }}>02</div>
                </motion.div>
              </div>

              {/* Stat 1 */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.8 }}
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '12px',
                  padding: '12px',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>P/E Ratio</div>
                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>24.2</div>
              </motion.div>

              {/* Stat 2 */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 1 }}
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '12px',
                  padding: '12px',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Volatility</div>
                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>Low</div>
              </motion.div>
            </div>

            {/* Sentiment Bar */}
            <div style={{ marginTop: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.6rem', color: '#38ef7d' }}>BULLISH</span>
                <span style={{ fontSize: '0.6rem', color: '#ff6b6b' }}>BEARISH</span>
              </div>
              <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '100px', overflow: 'hidden', display: 'flex' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '75%' }}
                  transition={{ duration: 1.5, delay: 1.2 }}
                  style={{ height: '100%', background: '#38ef7d' }}
                />
                <div style={{ flex: 1, height: '100%', background: '#ff6b6b' }} />
              </div>
            </div>
          </div>
        </div>
        <div className="feature-content">
          <h2 className="feature-title">Stock Score</h2>
          <p className="feature-desc">
            Stop second-guessing stock picks. Type any company name and get instant AI analysis combining technical indicators, fundamental data, and market sentiment. Receive clear buy/sell/hold insights with confidence percentages and detailed rationale—professional-grade research, simplified.          </p>
        </div>
      </div>
    </div>
  );
};

export default FeatureBlocks;

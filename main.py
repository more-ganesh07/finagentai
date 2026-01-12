import os
import json
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from Schemas import QueryRequest, QueryResponse, MarketChatRequest

# from src.sharebot.main_sharebot import ShareBot
from src.sharebot.agent.yfinance_agent import analyze_stock
from src.sharebot.agent.tavily_agent import stream_analysis
from src.sharebot.agent.tavily_agent import analyze

from src.kite.portbot.chatbot import KiteChatbot
from src.kite.portrep.portreport.run_portfolio_report import main as generate_portfolio_report

from src.stt.assembly_streaming import VoiceToTextService

from market_indices import get_market_indices, stream_market_indices_realtime

# ─────────────────────────────────────────────
# 🪵 Logging
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MainAPI")

# ─────────────────────────────────────────────
# 🌐 Lifespan Initialization
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Initializing services...")
        
        # Initialize STT Service
        app.state.stt_service = VoiceToTextService()
        logger.info("STT Service ready")
        
        # Initialize Portfolio Chatbot (Singleton)
        logger.info("Initializing Portfolio Chatbot...")
        app.state.portfolio_bot = KiteChatbot()
        await app.state.portfolio_bot.__aenter__()
        logger.info("Portfolio Chatbot singleton ready")
        
        logger.info("Stock Buddy ready")
        
        yield
        
        # Cleanup
        logger.info("Shutting down services...")
        if hasattr(app.state, "portfolio_bot"):
            await app.state.portfolio_bot.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise

app = FastAPI(
    title="KiteInfi API",
    version="1.0.0",
    description="Unified API for Market Chat, Portfolio Chat, and Portfolio Reports",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# 📊 1️⃣ MARKET CHATBOT (Research Agent - Market Buddy)
# ─────────────────────────────────────────────
@app.post("/market_chatbot/stream")
async def market_chatbot_stream(request: MarketChatRequest):
    """Market research with real-time streaming and memory"""
    
    user_query = request.user_query.strip()
    session_id = request.session_id or f"user_{hash(request.user_query) % 10000}"  # Generate unique session if not provided
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    async def generate_stream():
        try:
            async for chunk in stream_analysis(user_query, session_id):
                chunk_type = chunk.get("type")
                
                # 1. Status updates (searching, cached, etc.)
                if chunk_type == "status":
                    yield f"data: {json.dumps({'type': 'status', 'content': chunk['content'], 'done': False})}\n\n"
                
                # 2. Sources metadata (for displaying links in UI)
                elif chunk_type == "sources":
                    sources = chunk.get("sources", [])
                    yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'done': False})}\n\n"
                
                # 3. Main content (streamed text)
                elif chunk_type == "content":
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk['content'], 'done': False})}\n\n"
                
                # 4. Error handling
                elif chunk_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error': chunk['content'], 'done': True})}\n\n"
                    return
            
            # 5. Signal completion
            yield f"data: {json.dumps({'type': 'done', 'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Market chatbot stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/market_chatbot/sync")
async def market_chatbot_sync(request: MarketChatRequest):
    """Market research with synchronous response"""
    
    user_query = request.user_query.strip()
    session_id = request.session_id or f"user_{hash(request.user_query) % 10000}"
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Get complete analysis
        result = await analyze(user_query, session_id)
        
        if result.get("status") == "error":
            # Change to 503 to reflect AI service interruption rather than client error
            raise HTTPException(status_code=503, detail=result.get("message", "Market Buddy is temporarily unavailable. Please try again in a moment."))
        
        return {
            "status": "success",
            "query": result.get("query"),
            "analysis": result.get("analysis"),
            "sources": result.get("sources", []),
            "session_id": result.get("session_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market chatbot sync error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# 💼 2️⃣ PORTFOLIO CHATBOT (KiteChatbot)
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# 🔐 2.1 KITE LOGIN MANAGEMENT
# ─────────────────────────────────────────────

@app.get("/portfolio/status")
async def get_portfolio_status():
    """Check if the Zerodha Kite session is active"""
    try:
        bot: KiteChatbot = app.state.portfolio_bot
        # Try to validate session
        is_valid = await bot.master.kite_client.validate_session()
        
        # Also check shared_state
        has_session = "session" in bot.master.shared_state
        
        return {"connected": is_valid or has_session}
    except Exception as e:
        logger.error(f"Error checking portfolio status: {e}")
        return {"connected": False, "error": str(e)}

@app.get("/portfolio/connect")
async def connect_portfolio():
    """Wipe old session and get a fresh Zerodha login URL"""
    try:
        bot: KiteChatbot = app.state.portfolio_bot
        
        # EXPLICITLY clear old session first to ensure a fresh manual login
        if bot.master and bot.master.kite_client:
            bot.master.kite_client.clear_session()
            
        login_agent = bot.master.agents.get("login")
        if not login_agent:
            raise HTTPException(status_code=500, detail="Login agent not initialized")
            
        login_url = await login_agent.get_login_url()
        return {"login_url": login_url}
    except Exception as e:
        logger.error(f"Error getting connect URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/login-confirm")
async def portfolio_login_confirm():
    """Force a session finalization (check if session is live)"""
    try:
        bot: KiteChatbot = app.state.portfolio_bot
        login_agent = bot.master.agents.get("login")
        if not login_agent:
            raise HTTPException(status_code=500, detail="Login agent not initialized")
        
        result = await login_agent.finalize_session()
        return result
    except Exception as e:
        logger.error(f"Error confirming login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/chatbot_stream")
async def portfolio_chatbot_stream(request: QueryRequest):
    """Portfolio chatbot with streaming response"""
    user_query = request.user_query.strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    async def generate_stream():
        try:
            bot: KiteChatbot = app.state.portfolio_bot
            # Use the new chat_stream generator for true word-by-word streaming
            async for token in bot.chat_stream(user_query):
                yield f"data: {json.dumps({'content': token, 'done': False})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
                    
        except Exception as e:
            logger.error(f"Portfolio chatbot stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/portfolio/chatbot_sync", response_model=QueryResponse)
async def portfolio_chatbot_sync(request: QueryRequest):
    """Portfolio chatbot with synchronous response"""
    user_query = request.user_query.strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        bot: KiteChatbot = app.state.portfolio_bot
        # Use direct return value from chat method
        response = await bot.chat(user_query)
        return QueryResponse(response=response)
                
    except Exception as e:
        logger.error(f"Portfolio chatbot sync error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/portfolio/report/preview")
async def preview_portfolio_report():
    """Generate and return HTML preview of the portfolio report"""
    try:
        bot: KiteChatbot = app.state.portfolio_bot
        # Generate report without sending email
        html_content = await generate_portfolio_report(master_agent=bot.master, send_email=False)
        
        if not html_content:
            raise HTTPException(status_code=500, detail="Failed to generate report preview")
            
        return {
            "status": "success", 
            "message": "Report preview generated successfully",
            "html": html_content
        }
    except Exception as e:
        logger.error(f"Error generating report preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/report/demo")
async def get_demo_report():
    """Return the demo portfolio report HTML file content"""
    try:
        demo_path = os.path.join(os.getcwd(), "portfolio_report.html")
        if not os.path.exists(demo_path):
            raise HTTPException(status_code=404, detail="Demo report not found")
            
        with open(demo_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        return {
            "status": "success",
            "html": html_content
        }
    except Exception as e:
        logger.error(f"Error reading demo report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/report/send")
async def send_portfolio_report():
    try:
        from src.kite.portrep.portreport.generate_report import REPORT_FILE, load_data, convert_html_to_pdf
        from src.kite.portrep.portreport.emailer import send_email_with_attachment
        import os
        from datetime import datetime
        
        pdf_file = str(REPORT_FILE).replace(".html", ".pdf")
        html_file = str(REPORT_FILE)
        
        bot: KiteChatbot = app.state.portfolio_bot
        
        # 1. Ensure HTML report exists (either from previous preview or fresh run)
        if not os.path.exists(html_file):
            logger.info("📄 No existing report found. Generating fresh analysis...")
            await generate_portfolio_report(master_agent=bot.master, send_email=False)
            
        if not os.path.exists(html_file):
            raise HTTPException(status_code=500, detail="Failed to initialize report template.")

        # 2. Get the latest HTML content for conversion
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 3. Always refresh the PDF from the current HTML to ensure latest design/data
        logger.info(f"🔄 Converting report to PDF format...")
        if not convert_html_to_pdf(html_content, pdf_file):
            raise HTTPException(status_code=500, detail="PDF conversion failed. Please check system libraries.")

        # 4. Resolve Recipient & Metadata
        data = load_data()
        user_email = data.get("profile", {}).get("email")
        if not user_email or user_email == "N/A":
            user_email = os.getenv("FALLBACK_EMAIL")
            
        if not user_email or "@" not in str(user_email):
             raise HTTPException(status_code=400, detail=f"No valid recipient email (Found: {user_email}). Please update your profile.")
             
        user_name = data.get("profile", {}).get("name", "Investor")
        if user_name == "N/A": user_name = "Investor"
        
        # 5. Direct Email Dispatch
        logger.info(f"📧 Dispatching report to {user_email}...")
        subject = f"Your Investment Portfolio Analysis - {datetime.now().strftime('%B %d, %Y')}"
        body = f"""Dear {user_name},

Please find attached your comprehensive Investment Portfolio Analysis Report.

This document contains specialized insights into your current holdings, including:
- Portfolio Performance & Profitability Tracking
- Real-time Market Sentiment Analysis
- Detailed Research on your Equity Holdings
- Scheme-wise Analysis of your Mutual Fund Portfolio

Best Regards,
Project KiteInfi Mastery Team
"""
        send_email_with_attachment(
            to_addr=user_email,
            subject=subject,
            body=body,
            attachment_path=pdf_file
        )
            
        return {
            "status": "success", 
            "message": f"Portfolio report dispatched to {user_email} successfully."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in report delivery pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Delivery failed: {str(e)}")


@app.post("/portfolio/disconnect")
async def disconnect_portfolio():
    """Wipe Zerodha session from memory and disk"""
    try:
        bot: KiteChatbot = app.state.portfolio_bot
        if bot.master and bot.master.kite_client:
            bot.master.kite_client.clear_session()
            
        if bot.master and "session" in bot.master.shared_state:
            bot.master.shared_state.pop("session", None)
            
        return {"status": "success", "message": "Disconnected from Zerodha Kite. Session cleared."}
    except Exception as e:
        logger.error(f"Error disconnecting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 📈 3️⃣ STOCK BUDDY (YFinance Agent)
# ─────────────────────────────────────────────
@app.post("/stock_buddy/stream")
async def stock_buddy_stream(request: QueryRequest):
    """Stock analysis with streaming response"""
    
    company_name = request.user_query.strip()
    
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name cannot be empty")
    
    async def generate_stream():
        try:
            # Get stock analysis
            result = analyze_stock(company_name)
            
            if result["status"] == "error":
                error_message = f"❌ Error: {result['error']}\n\n💡 Please try again with a different company name."
                for char in error_message:
                    yield f"data: {json.dumps({'content': char, 'done': False})}\n\n"
                    await asyncio.sleep(0.01)
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                return
            
            # Format success response with new 3-column UI data
            formatted_response = "=" * 60 + "\n"
            formatted_response += "UI TABLE (Parameter | Value | Meaning)\n"
            formatted_response += "=" * 60 + "\n"
            
            # Display UI table in a readable format
            if result.get("stock_data_ui"):
                for row in result["stock_data_ui"]:
                    formatted_response += f"📊 {row['parameter']}\n"
                    formatted_response += f"   Value: {row['value']}\n"
                    formatted_response += f"   Meaning: {row['meaning']}\n\n"
            
            formatted_response += "\n" + "=" * 60 + "\n"
            formatted_response += "RECOMMENDATION\n"
            formatted_response += "=" * 60 + "\n"
            formatted_response += json.dumps(result["recommendation"], indent=2, ensure_ascii=False) + "\n\n"
            formatted_response += "=" * 60 + "\n"
            formatted_response += f"✅ Analysis completed successfully for {result['symbol']}\n"
            formatted_response += "=" * 60 + "\n"
            
            # Stream the response character by character
            for char in formatted_response:
                yield f"data: {json.dumps({'content': char, 'done': False})}\n\n"
                await asyncio.sleep(0.01)  # Smooth streaming
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Stock buddy stream error: {e}", exc_info=True)
            error_msg = f"⚠️ Unexpected error: {str(e)}\n💡 Please try again with a different company name."
            for char in error_msg:
                yield f"data: {json.dumps({'content': char, 'done': False})}\n\n"
                await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/stock_buddy/sync")
async def stock_buddy_sync(request: QueryRequest):
    """Stock analysis with synchronous response"""
    
    company_name = request.user_query.strip()
    
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name cannot be empty")
    
    try:
        # Get stock analysis
        result = analyze_stock(company_name)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return the complete result with all fields from yfinance_agent
        return {
            "status": "success",
            "symbol": result["symbol"],
            "stock_data": result["stock_data"],
            "stock_data_ui": result["stock_data_ui"],  # ✅ Added 3-column UI format
            "recommendation": result["recommendation"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock buddy sync error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# ─────────────────────────────────────────────
# 🎙️ 5️⃣ VOICE-TO-TEXT (STT)
# ─────────────────────────────────────────────

@app.get("/stt/status")
async def stt_status():
    """Check STT service and microphone status"""
    stt = app.state.stt_service
    is_ok, msg = stt.test_microphone()
    return {
        "is_streaming": stt.is_streaming,
        "microphone": {
            "available": is_ok,
            "message": msg
        }
    }

@app.post("/stt/start")
async def stt_start():
    """Start the voice transcription session"""
    try:
        msg = app.state.stt_service.start_streaming()
        return {"status": "success", "message": msg}
    except Exception as e:
        logger.error(f"STT Start Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stt/stop")
async def stt_stop():
    """Stop the voice transcription session"""
    try:
        msg = app.state.stt_service.stop_streaming()
        return {"status": "success", "message": msg}
    except Exception as e:
        logger.error(f"STT Stop Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stt/stream")
async def stt_stream():
    """Stream transcripts from the microphone in real-time"""
    stt = app.state.stt_service
    
    async def event_generator():
        while True:
            # Check if we should stop
            if not stt.is_streaming and stt.transcript_queue.empty():
                break
                
            transcript = stt.get_transcript(timeout=0.1)
            if transcript:
                yield f"data: {json.dumps(transcript)}\n\n"
            
            await asyncio.sleep(0.01)
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ─────────────────────────────────────────────
# 📊 6 MARKET INDICES (Second-by-Second Real-time)
# ─────────────────────────────────────────────

@app.get("/market_indices")
async def market_indices():
    """
    Get current market indices (one-time fetch)
    Returns last traded prices if market is closed
    """
    try:
        result = get_market_indices()
        return result
    except Exception as e:
        logger.error(f"Market indices error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market_indices/stream")
async def market_indices_stream():
    """
    Stream market indices in real-time
    - Only streams during market hours (Mon-Fri 9:15 AM - 3:30 PM IST)
    - Auto-stops when market closes
    - Use /market_indices endpoint for static data outside market hours
    """
    async def generate_stream():
        try:
            async for data in stream_market_indices_realtime():
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ─────────────────────────────────────────────
# 🩺 Health Check
# ─────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "market_chatbot": "ready",
            "portfolio_chatbot": "ready",
            "stock_buddy": "ready",
            "stt_service": "ready" if hasattr(app.state, 'stt_service') and app.state.stt_service else "not_ready",
            "portfolio_report": "ready"
        }
    }


# ─────────────────────────────────────────────
# 🚀 Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting KiteInfi API on port {port}...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
 

import os
import logging
import asyncio
from typing import AsyncGenerator, List, Optional
from pathlib import Path
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from dotenv import load_dotenv

# ============================================================================
# SETUP
# ============================================================================
load_dotenv(override=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FinMentor")

# Import dependencies with fallbacks
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tool.tavily_tool import research_financial_data
except ImportError as e:
    logger.error(f"Failed to import search tool: {e}")
    research_financial_data = None

try:
    from src.utils.llm_balancer import balancer
except ImportError:
    logger.warning("LLM balancer not found, using direct API key")
    balancer = None

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
SEARCH_TIMEOUT = 30  # seconds

# ============================================================================
# IN-MEMORY STORAGE (Last 3 turns = 6 messages)
# ============================================================================
MEMORY: dict[str, List[BaseMessage]] = {}

def get_memory(session_id: str) -> List[BaseMessage]:
    """Get conversation history (last 6 messages)"""
    return MEMORY.get(session_id, [])[-6:]

def add_to_memory(session_id: str, user_msg: str, ai_msg: str):
    """Add turn and auto-prune to 6 messages"""
    if session_id not in MEMORY:
        MEMORY[session_id] = []
    
    # Prune before adding to maintain exact limit
    if len(MEMORY[session_id]) >= 6:
        MEMORY[session_id] = MEMORY[session_id][-4:]
    
    MEMORY[session_id].extend([
        HumanMessage(content=user_msg),
        AIMessage(content=ai_msg)
    ])

def clear_memory(session_id: str):
    """Reset session memory"""
    MEMORY.pop(session_id, None)
    logger.info(f"🧹 Memory cleared: {session_id}")

# ============================================================================
# QUERY INTELLIGENCE
# ============================================================================
def classify_query(query: str) -> dict:
    """
    Smart query classification for adaptive responses.
    Returns: {'needs_search': bool, 'type': str, 'max_tokens': int}
    """
    q = query.lower().strip()
    words = q.split()
    
    # Greetings & meta (no search needed)
    greetings = {"hi", "hello", "hey", "thanks", "thank you", "bye", "ok", "okay"}
    if q in greetings or (len(words) <= 4 and any(q.startswith(g) for g in greetings)):
        return {'needs_search': False, 'type': 'quick', 'max_tokens': 512}
    
    # Single-word follow-ups
    if len(words) == 1 and words[0] in {"why", "how", "elaborate"}:
        return {'needs_search': False, 'type': 'medium', 'max_tokens': 1024}
    
    # Detailed analysis triggers
    detailed = {"detailed", "complete", "full analysis", "thorough", "comprehensive", 
                "deep dive", "everything", "elaborate", "ipo", "mutual fund"}
    if any(kw in q for kw in detailed):
        return {'needs_search': True, 'type': 'detailed', 'max_tokens': 4096}
    
    # Analysis/comparison
    analysis = {"analyze", "compare", "versus", "vs", "better", "should i", 
                "worth", "outlook", "forecast", "recommend"}
    if any(kw in q for kw in analysis):
        return {'needs_search': True, 'type': 'detailed', 'max_tokens': 3072}
    
    # Quick price checks
    if any(kw in q for kw in {"price", "current price", "trading at"}) and len(words) <= 5:
        return {'needs_search': True, 'type': 'quick', 'max_tokens': 1024}
    
    # Default medium
    return {'needs_search': True, 'type': 'medium', 'max_tokens': 2048}

async def rewrite_query(query: str, history: List[BaseMessage]) -> str:
    """Make follow-up queries standalone using conversation context"""
    if not history:
        return query
    
    # Skip rewrite if query seems standalone
    follow_up = {"it", "its", "they", "them", "this", "that", "these", "those", 
                 "above", "previous", "biggest", "latest"}
    if not any(word in query.lower() for word in follow_up) and len(query.split()) > 4:
        return query
    
    try:
        llm = get_llm(max_tokens=150)
        if not llm:
            return query
        
        # Build concise history
        history_text = "\n".join([
            f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content[:150]}"
            for m in history[-4:]
        ])
        
        prompt = f"""Previous conversation:
{history_text}

Current query: {query}

Rewrite the current query as a standalone search query with full context. Output ONLY the rewritten query.
Example: "HDFC Bank stock price and latest news"

Rewritten:"""
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        rewritten = response.content.strip().strip('"')
        
        if rewritten and len(rewritten) > 5:
            logger.info(f"🔄 Rewritten: {rewritten}")
            return rewritten
            
    except Exception as e:
        logger.error(f"Query rewrite failed: {e}")
    
    return query

# ============================================================================
# LLM & SEARCH
# ============================================================================
def get_llm(max_tokens: int = 2048) -> Optional[ChatGroq]:
    """Get LLM with fallback API key handling"""
    try:
        key = balancer.get_next_key() if balancer else os.getenv("GROQ_API_KEY")
        
        if not key:
            logger.error("No GROQ API key available")
            return None
        
        return ChatGroq(
            api_key=key,
            model=GROQ_MODEL,
            temperature=0.3,
            streaming=True,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"LLM init failed: {e}")
        return None

async def search_with_timeout(query: str, days: int = 7) -> Optional[dict]:
    """Execute search with timeout protection"""
    if not research_financial_data:
        logger.warning("Search tool not available")
        return None
    
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(research_financial_data, query, days=days),
            timeout=SEARCH_TIMEOUT
        )
        return result if result.get("status") == "success" else None
    except asyncio.TimeoutError:
        logger.error("Search timeout")
        return None
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return None

# ============================================================================
# SYSTEM PROMPT
# ============================================================================
def build_system_prompt(response_type: str, has_history: bool) -> str:
    """Dynamic system prompt based on context"""
    now = datetime.now().strftime('%A, %B %d, %Y')
    
    intro = "Continue the conversation naturally." if has_history else ""
    
    length_guide = {
        'quick': "Keep responses SHORT (2-3 sentences max for greetings, 1 paragraph for facts).",
        'medium': "Provide BALANCED responses (2-3 paragraphs with key insights).",
        'detailed': "Give COMPREHENSIVE analysis with structure, metrics, and actionable insights."
    }.get(response_type, "")
    
    return f"""You are 'Market Mentor', a Senior Indian Equity Research Analyst.
Today: {now}

{intro}

RULES:
1. Professional English only (use Indian terms: lakhs, crores when natural)
2. Use search data as source of truth - cite specific numbers and dates
3. Structure: Use Markdown (# ## **bold**) for clarity
4. {length_guide}
5. For greetings/thanks: respond naturally and briefly
6. NEVER fabricate data - if uncertain, say so

FOCUS: Indian markets (NSE, BSE), rupee-denominated analysis."""

# ============================================================================
# MAIN STREAMING ENGINE
# ============================================================================
async def stream_analysis(
    query: str, 
    session_id: str = "default"
) -> AsyncGenerator[dict, None]:
    """
    Main streaming function with intelligence and error recovery.
    Yields: {"type": "status"|"sources"|"content"|"done"|"error", ...}
    """
    try:
        # 1. Classify query
        classification = classify_query(query)
        logger.info(f"📊 Query type: {classification['type']}, tokens: {classification['max_tokens']}")
        
        # 2. Get memory
        history = get_memory(session_id)
        
        # 3. Search if needed
        search_data = None
        sources = []
        
        if classification['needs_search']:
            yield {"type": "status", "content": "🔍 Researching..."}
            
            # Rewrite query with context
            search_query = await rewrite_query(query, history)
            
            # Execute search
            days = 14 if classification['type'] == 'detailed' else 7
            search_data = await search_with_timeout(search_query, days=days)
            
            if search_data and search_data.get("results"):
                sources = [
                    {"title": r.get("title"), "url": r.get("url")} 
                    for r in search_data["results"][:8]
                ]
                yield {"type": "sources", "sources": sources}
        
        # 4. Get LLM
        llm = get_llm(max_tokens=classification['max_tokens'])
        if not llm:
            yield {"type": "error", "content": "System unavailable - please try again"}
            return
        
        # 5. Build prompt
        system_prompt = build_system_prompt(classification['type'], bool(history))
        messages = [SystemMessage(content=system_prompt)]
        
        # Add history if exists
        if history:
            messages.extend(history)
        
        # Add current query with search context
        user_content = query
        if search_data:
            num_results = 8 if classification['type'] == 'detailed' else 4
            results = search_data.get('results', [])[:num_results]
            
            sources_text = "\n".join([
                f"[{i+1}] {r.get('title')}\n{r.get('content', '')[:300]}\nURL: {r.get('url')}\n"
                for i, r in enumerate(results)
            ])
            
            user_content = f"""{query}

### SEARCH CONTEXT ({datetime.now().strftime('%d %b %Y')})
Summary: {search_data.get('answer', 'N/A')}

Sources:
{sources_text}

Synthesize a professional response using the above data. Include specific numbers and dates."""
        
        messages.append(HumanMessage(content=user_content))
        

        # 6. Stream response
        full_response = ""
        try:
            async for chunk in llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield {"type": "content", "content": chunk.content}
                    await asyncio.sleep(0.03)  # Add 50ms delay between chunks for slower streaming

        except Exception as stream_err:
            logger.error(f"Stream interrupted: {stream_err}")
            if not full_response:
                yield {"type": "content", "content": "I'm experiencing connectivity issues. Please try again."}
            else:
                yield {"type": "content", "content": "\n\n*(Analysis interrupted - please retry for complete report)*"}


        # 7. Save to memory
        if full_response:
            add_to_memory(session_id, query, full_response)
        
        # 8. Done
        yield {"type": "done", "done": True}
        
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        yield {"type": "error", "content": f"System error: {str(e)}"}

# ============================================================================
# SYNC WRAPPER
# ============================================================================
async def analyze(query: str, session_id: str = "default") -> dict:
    """Non-streaming version - returns complete result"""
    content = ""
    sources = []
    error = None
    
    async for chunk in stream_analysis(query, session_id):
        chunk_type = chunk.get("type")
        
        if chunk_type == "content":
            content += chunk.get("content", "")
        elif chunk_type == "sources":
            sources = chunk.get("sources", [])
        elif chunk_type == "error":
            error = chunk.get("content")
            break
    
    if error:
        return {"status": "error", "message": error}
    
    return {
        "status": "success",
        "query": query,
        "analysis": content,
        "sources": sources,
        "session_id": session_id
    }

# ============================================================================
# CLI INTERFACE
# ============================================================================
async def cli_chat():
    """Interactive CLI for testing"""
    session = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("=" * 60)
    print("💼 Indian Financial Mentor (Production)")
    print("=" * 60)
    print("Commands: /clear (reset), /exit (quit)")
    print("=" * 60)
    
    while True:
        try:
            query = input("\n💬 You: ").strip()
            
            if query.lower() in {"/exit", "/quit", "exit", "quit"}:
                print("👋 Happy investing!")
                break
            
            if query.lower() == "/clear":
                clear_memory(session)
                print("✅ Memory cleared")
                continue
            
            if not query:
                continue
            
            print("\n🤖 Mentor: ", end="", flush=True)
            
            async for chunk in stream_analysis(query, session):
                chunk_type = chunk.get("type")
                
                if chunk_type == "status":
                    print(f"[{chunk['content']}] ", end="", flush=True)
                elif chunk_type == "sources":
                    print(f"[{len(chunk.get('sources', []))} sources] ", end="", flush=True)
                elif chunk_type == "content":
                    print(chunk["content"], end="", flush=True)
                elif chunk_type == "error":
                    print(f"\n❌ {chunk['content']}")
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}")

def main():
    """Entry point"""
    asyncio.run(cli_chat())

if __name__ == "__main__":
    main()
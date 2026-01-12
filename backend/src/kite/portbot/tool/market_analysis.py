# src/kite/portbot/tool/market_analysis.py
import os
import time
from typing import Any, Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

from src.kite.portbot.base import Agent
from tavily import TavilyClient
from src.utils.llm_balancer import balancer
from groq import AsyncGroq

class MarketAnalysisAgent(Agent):
    """
    Market analysis agent using Tavily for deep research.
    Focused on Indian markets (NSE, BSE) with domain-specific filtering.
    """
    name = "market_analysis"
    description = "Deep market research and stock analysis using Tavily (Indian Markets)"

    tools = [
        {
            "name": "analyze_stock",
            "description": "Deep analysis of a specific stock with news, fundamentals, and outlook (NSE/BSE focus)",
            "parameters": {"symbol": "str", "context": "str (optional - user's position details)"}
        },
        {
            "name": "get_market_news",
            "description": "Get latest market news and updates for stocks or sectors in India",
            "parameters": {"query": "str"}
        },
        {
            "name": "research_topic",
            "description": "Deep research on any financial topic, market trend, or investment question in India",
            "parameters": {"query": "str"}
        },
    ]

    # High-quality Indian financial domains for noise filtering
    INDIAN_FINANCE_DOMAINS = [
        "moneycontrol.com",
        "economictimes.indiatimes.com",
        "nseindia.com",
        "bseindia.com",
        "ipowatch.in",
        "livemint.com",
        "business-standard.com",
        "screener.in",
        "valueresearchonline.com",
        "tradingview.com"
    ]

    def __init__(self, kite_client=None, shared_state=None):
        super().__init__(shared_state)
        self.kite_client = kite_client
        
        # Initialize Tavily
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        self.tavily_client = TavilyClient(api_key=tavily_key)
        
        # Groq keys are handled by the balancer
        if balancer.key_count == 0:
            raise ValueError("No Groq API keys found in environment")
        
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def _get_groq_client(self):
        """Get a fresh AsyncGroq client with the next available API key"""
        return AsyncGroq(api_key=balancer.get_next_key())

    async def run(self, tool_name: str, **kwargs):
        """Execute the specified tool"""
        if tool_name == "analyze_stock":
            return await self._analyze_stock(**kwargs)
        elif tool_name == "get_market_news":
            return await self._get_market_news(**kwargs)
        elif tool_name == "research_topic":
            return await self._research_topic(**kwargs)
        raise ValueError(f"Unknown tool: {tool_name}")

    def _internet_search(self, query: str, max_results: int = 8, topic: str = "finance", days: int = 7) -> Dict[str, Any]:
        """Run Tavily search with Indian market enhancements"""
        try:
            current_date = datetime.now().strftime("%B %d, %Y")
            lower_query = query.lower()
            
            # Enhance query for Indian focus if not present
            enhanced_query = query
            if not any(word in lower_query for word in ["india", "indian", "nse", "bse", "nifty", "sensex"]):
                enhanced_query = f"{query} India NSE BSE"
            
            # IPO Optimization
            if "ipo" in lower_query:
                enhanced_query = f"latest current open upcoming IPO India today {current_date} ipowatch.in NSE BSE"
            elif any(word in lower_query for word in ["price", "current", "today", "latest"]):
                enhanced_query = f"{enhanced_query} today {current_date} latest stock price"

            return self.tavily_client.search(
                query=enhanced_query,
                search_depth="advanced",
                topic=topic,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False,
                days=days,
                include_domains=self.INDIAN_FINANCE_DOMAINS
            )
        except Exception as e:
            print(f"Tavily search error: {e}")
            return {"results": [], "answer": ""}

    async def _analyze_stock(self, symbol: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Deep stock analysis with Tavily research (Indian Market Focused)."""
        try:
            # Search for stock information
            query = f"{symbol} stock financial performance news outlook analysis"
            search_results = self._internet_search(query, max_results=8, topic="finance", days=14)
            
            if not search_results.get('results'):
                return {
                    "status": "error",
                    "message": f"No market data found for {symbol}",
                    "data": None,
                    "summary": None
                }
            
            # Build context from search results
            research_context = "\n\n".join([
                f"[{i+1}] Title: {result['title']}\nContent: {result['content']}"
                for i, result in enumerate(search_results['results'])
            ])
            ai_answer = search_results.get("answer", "")
            
            # Generate analysis using Groq
            system_prompt = """You are 'Market Mentor', a Senior Indian Equity Research Analyst.
Your goal is to provide professional, objective, and data-driven stock analysis for the Indian market.

**Guidelines:**
- Professional English only (use Indian terms like lakhs/crores where appropriate)
- Use search data as the primary source of truth - cite specific numbers and dates
- Structure: Use clean Markdown with headers and tables
- Tone: Technical, precise, and confident
- FOCUS: Indian markets (NSE, BSE), rupee-denominated analysis.

**Format:**
1. **Investment Verdict** (Buy/Hold/Sell with clear technical rationale)
2. **Recent Performance** (Key price levels, returns, and news)
3. **Fundamental Insights** (Valuation, health, catalysts)
4. **Risk Factors** (Concentration, market risks)
5. **12-Month Outlook**
"""
            
            user_prompt = f"""**Stock**: {symbol}
{"**User Portfolio Position Details**: " + context if context else ""}

**AI Preliminary Summary**: {ai_answer}

**Market Data & News Context**:
{research_context}

Provide a comprehensive professional report following the guidelines."""
            
            groq_client = self._get_groq_client()
            response = await groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            sources = [{"title": r["title"], "url": r["url"]} for r in search_results['results']]
            
            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "analysis": analysis,
                    "sources": sources
                },
                "summary": {
                    "symbol": symbol,
                    "analysis": analysis,
                    "source_count": len(sources)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to analyze {symbol}: {str(e)}",
                "data": None,
                "summary": None
            }

    async def _get_market_news(self, query: str) -> Dict[str, Any]:
        """Get latest market news with Indian market focus."""
        try:
            search_results = self._internet_search(query, max_results=6, topic="news")
            
            if not search_results.get('results'):
                return {
                    "status": "error",
                    "message": f"No news found for: {query}",
                    "data": [],
                    "summary": None
                }
            
            news_items = [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "content": r["content"],
                    "published_date": r.get("published_date", "N/A")
                }
                for r in search_results['results']
            ]
            
            return {
                "status": "success",
                "data": news_items,
                "summary": {
                    "news_items": news_items,
                    "total_count": len(news_items),
                    "ai_brief": search_results.get("answer", "")
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch news: {str(e)}",
                "data": [],
                "summary": None
            }

    async def _research_topic(self, query: str) -> Dict[str, Any]:
        """Deep research on any financial topic in the Indian Market."""
        try:
            search_results = self._internet_search(query, max_results=8, topic="finance", days=30)
            
            if not search_results.get('results'):
                return {
                    "status": "error",
                    "message": f"No information found for: {query}",
                    "data": None,
                    "summary": None
                }
            
            research_context = "\n\n".join([
                f"[{i+1}] Title: {result['title']}\nContent: {result['content']}"
                for i, result in enumerate(search_results['results'])
            ])
            ai_answer = search_results.get("answer", "")
            
            system_prompt = """You are a senior Financial Research Specialist for the Indian Market.
Provide a comprehensive, professional research summary on the requested topic.

**Guidelines:**
- Professional, objective tone
- Clean Markdown format with relevant headers
- Use Indian financial terminology and contexts
- Cite key findings from the context
- Provide actionable insights if relevant
"""
            
            user_prompt = f"""**Research Topic**: {query}

**AI Preliminary Summary**: {ai_answer}

**Research Material**:
{research_context}

Provide a detailed professional research report."""
            
            groq_client = self._get_groq_client()
            response = await groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            research = response.choices[0].message.content
            sources = [{"title": r["title"], "url": r["url"]} for r in search_results['results']]
            
            return {
                "status": "success",
                "data": {
                    "query": query,
                    "research": research,
                    "sources": sources
                },
                "summary": {
                    "query": query,
                    "research": research,
                    "source_count": len(sources)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to research topic: {str(e)}",
                "data": None,
                "summary": None
            }


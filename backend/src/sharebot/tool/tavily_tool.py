
import os
import json
import logging
from datetime import datetime, timedelta
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TavilyTool")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def get_tavily_client():
    """Initialize and return Tavily client"""
    if not TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY not found in environment variables")
        return None
    return TavilyClient(api_key=TAVILY_API_KEY)


def research_financial_data(query: str, days: int = 7) -> dict:
    """
    Fetch real-time financial data from Indian markets.
    
    Args:
        query: User's search query
        days: How many days back to search (default: 7 for fresh data)
    
    Returns:
        dict with status, query, answer, results
    """
    client = get_tavily_client()
    if not client:
        return {"status": "error", "message": "Tavily API key missing"}

    try:
        # Add current date context for real-time queries
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Smart query enhancement for Indian market
        enhanced_query = query
        lower_query = query.lower()
        
        # Only add "India" context if not already present
        if not any(word in lower_query for word in ["india", "indian", "nse", "bse", "nifty", "sensex"]):
            enhanced_query = f"{query} India NSE BSE"
        
        # SPECIAL: IPO Query Optimization
        if "ipo" in lower_query:
            # ipowatch.in is the gold standard for Indian IPO info
            enhanced_query = f"latest current open upcoming IPO India today {current_date} ipowatch.in NSE BSE"
        
        # For price queries, add "today" or "latest"
        elif any(word in lower_query for word in ["price", "current", "today", "latest"]):
            enhanced_query = f"{enhanced_query} today {current_date} latest stock price"
        
        logger.info(f"Tavily search: {enhanced_query}")
        
        # Search with optimized parameters
        search_results = client.search(
            query=enhanced_query,
            search_depth="advanced",
            topic="finance",
            max_results=8, # More results for better synthesis
            include_answer=True,
            include_raw_content=False,
            days=days,
            # Filter for high-quality Indian financial domains to avoid noise
            include_domains=[
                "moneycontrol.com",
                "economictimes.indiatimes.com",
                "nseindia.com",
                "bseindia.com",
                "ipowatch.in", # Added for IPO accuracy
                "livemint.com",
                "business-standard.com",
                "screener.in"
            ]
        )

        # Format results
        formatted_results = {
            "status": "success",
            "query": query,
            "search_date": current_date,
            "answer": search_results.get("answer", "No direct answer found."),
            "results": []
        }

        for res in search_results.get("results", []):
            formatted_results["results"].append({
                "title": res.get("title", "Untitled"),
                "url": res.get("url", "#"),
                "content": res.get("content", "")[:500],  # Increased to 500 characters
                "published_date": res.get("published_date", "N/A"),
                "score": round(res.get("score", 0), 2)
            })

        logger.info(f"Found {len(formatted_results['results'])} results")
        return formatted_results

    except Exception as e:
        logger.error(f"Tavily search error: {str(e)}")
        return {"status": "error", "message": str(e)}


def main():
    """CLI testing"""
    print("=" * 60)
    print("🔍 TAVILY FINANCIAL RESEARCH TOOL")
    print("=" * 60)
    
    query = input("\n💬 Enter query: ").strip()
    if not query:
        return

    print(f"\n📡 Searching for '{query}'...\n")
    result = research_financial_data(query)
    
    if result["status"] == "success":
        print("=" * 60)
        print(f"📊 SUMMARY ({result['search_date']}):")
        print("=" * 60)
        print(result['answer'])
        
        print(f"\n\n📚 SOURCES ({len(result['results'])} found):")
        print("=" * 60)
        for idx, item in enumerate(result["results"], 1):
            print(f"\n{idx}. {item['title']}")
            print(f"   🔗 {item['url']}")
            print(f"   📅 {item['published_date']}")
            print(f"   📝 {item['content'][:150]}...")
    else:
        print(f"❌ Error: {result['message']}")


if __name__ == "__main__":
    main()
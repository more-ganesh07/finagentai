import os
from typing import Literal, Dict, Any, List
from tavily import AsyncTavilyClient
from groq import AsyncGroq
from dotenv import load_dotenv
from datetime import datetime

from src.utils.llm_balancer import balancer

load_dotenv(override=True)

class DeepAgent:
    def __init__(self):
        self.tavily_api_key = os.environ.get("TAVILY_API_KEY")
        # Note: Groq keys are handled by the balancer
        
        if not self.tavily_api_key or balancer.key_count == 0:
            raise ValueError("Missing TAVILY_API_KEY or GROQ_API_KEYS (or GROQ_API_KEY) environment variables")

        self.tavily_client = AsyncTavilyClient(api_key=self.tavily_api_key)
        
        # High-quality Indian financial domains for accurate research
        self.indian_domains = [
            "moneycontrol.com",
            "economictimes.indiatimes.com",
            "nseindia.com",
            "bseindia.com",
            "ipowatch.in",
            "livemint.com",
            "business-standard.com",
            "screener.in",
            "valueresearchonline.com"
        ]

    def _get_groq_client(self):
        """Get a fresh AsyncGroq client with the next available API key"""
        return AsyncGroq(api_key=balancer.get_next_key())

    async def internet_search(
        self,
        query: str,
        max_results: int = 8,
        topic: Literal["general", "news", "finance"] = "finance",
        include_raw_content: bool = False,
    ):
        """Run an optimized web search for Indian markets"""
        try:
            # Enhance query with Indian context if not present
            lower_query = query.lower()
            enhanced_query = query
            if not any(word in lower_query for word in ["india", "nse", "bse", "nifty", "sensex"]):
                enhanced_query = f"{query} India NSE BSE"
            
            # Special optimization for IPOs
            if "ipo" in lower_query:
                current_date = datetime.now().strftime("%B %Y")
                enhanced_query = f"latest upcoming IPO India {current_date} details NSE BSE ipowatch.in"

            return await self.tavily_client.search(
                query=enhanced_query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic,
                include_domains=self.indian_domains
            )
        except Exception as e:
            print(f"Error during search: {e}")
            return {"results": []}

    async def analyze_asset(self, asset_name: str, asset_type: str, position_details: str) -> str:
        """
        Conducts research and generates a report for a specific asset using AsyncGroq.
        """
        query = f"Analyze {asset_name} {asset_type} financial performance news future outlook"
        print(f"Researching: {asset_name}...")
        
        search_results = await self.internet_search(query, topic="finance")
        
        if not search_results.get('results'):
            return "No search results found. Unable to generate analysis."

        context = "\n\n".join([
            f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['content']}"
            for result in search_results['results']
        ])
        
        system_prompt = """You are a senior financial analyst at a top-tier Indian investment firm. Your task is to provide a professional, data-driven equity research report.
        
        **Tone**: Formal, objective, and authoritative. Use professional Indian financial terminology.
        **Format**: Clean Markdown. **DO NOT use emojis.**
        **Structure**:
            1. **Investment Verdict**: Buy / Sell / Hold / Accumulate (with a concise rationale).
            2. **Financial Health Assessment**: Analyze key metrics (P/E, EPS, Debt-to-Equity, EBITDA) from the context.
            3. **Key Catalysts & Risks**: Recent earnings, regulatory changes (SEBI), or macroeconomic factors.
            4. **Position Analysis**: Evaluate the user's specific holding (provided in prompt). Recommend actionable steps based on Indian market conditions.
            5. **Outlook**: 12-month forecast based on fundamentals and sector trends.
        """

        user_prompt = f"""
        **Asset**: {asset_name} ({asset_type})
        **Client Position**: {position_details}
        
        **Market Data & News**:
        {context}
        
        Generate the research report following the strict guidelines above. Ensure it reflects the latest Indian market sentiments.
        """

        try:
            groq_client = self._get_groq_client()
            response = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating analysis: {e}"

    async def analyze_portfolio(self, portfolio_summary: str) -> str:
        """
        Generates an overall portfolio analysis based on the aggregated data.
        """
        print(f"Generating Overall Portfolio Strategy...")
        
        system_prompt = """You are a Chief Investment Officer (CIO) for an Indian wealth management firm. Your task is to review a client's total portfolio and provide a high-level strategic assessment.

        **Guidelines:**
        - **Tone**: Executive, strategic, and professional. **NO emojis.**
        - **Focus**: Asset allocation, sector exposure, risk assessment, and overall performance in the Indian market context.
        - **Output**:
            1. **Portfolio Health Check**: Comment on diversification and performance.
            2. **Risk Assessment**: Identify concentration risks or sector over-exposure (e.g., over-exposure to IT or Banking).
            3. **Strategic Recommendations**: High-level advice (e.g., "Rebalance into defensive sectors like FMCG", "Increase exposure to large-caps").
        """

        try:
            groq_client = self._get_groq_client()
            response = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"**Portfolio Summary**:\n{portfolio_summary}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating portfolio analysis: {e}"


if __name__ == "__main__":
    # Test run
    import asyncio
    async def test():
        agent = DeepAgent()
        res = await agent.analyze_asset("TCS", "Stock", "Qty: 10, Avg: 3500, LTP: 3800")
        print(res)
    
    asyncio.run(test())

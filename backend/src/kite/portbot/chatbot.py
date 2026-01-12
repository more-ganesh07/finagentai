
import asyncio
import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from dotenv import load_dotenv
from groq import AsyncGroq

from src.kite.portbot.agent.master_agent import MasterAgent
from src.utils.llm_balancer import balancer

load_dotenv(override=True)
logger = logging.getLogger("KiteChatbot")

def _truncate(s: str, n: int = 8000) -> str:
    return s if len(s) <= n else s[: n - 3] + "..."

class KiteChatbot:
    """
    Professional Portfolio Chatbot with financial advisor tone.
    Integrated with Indian market research via MasterAgent.
    """
    def __init__(self, user_id: Optional[str] = None):
        if balancer.key_count == 0:
            raise ValueError("Missing Groq API keys in environment")

        self.user_id = user_id or os.getenv("USER_ID", "demo-user")

        self.client = AsyncGroq(api_key=balancer.get_next_key())
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.temperature = float(os.getenv("TEMPERATURE", 0.3))
        self.max_tokens = int(os.getenv("MAX_TOKENS", 600))

        self.narrate = os.getenv("NARRATE_USING_LLM", "1").strip().lower() not in ("0", "false")
        self.memory: List[Dict[str, str]] = []
        self.master: Optional[MasterAgent] = None  

    async def __aenter__(self):
        self.master = await MasterAgent(user_id=self.user_id).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.master:
            await self.master.__aexit__(exc_type, exc, tb)

    # ------------- Query Intelligence -------------
    def _classify_query(self, query: str) -> Dict[str, Any]:
        """Classify query to handle greetings and acknowledgments gracefully."""
        q = query.lower().strip()
        words = q.split()
        
        # Greetings & Acknowledgments
        greetings = {"hi", "hello", "hey", "thanks", "thank you", "thanks!", "ok", "okay", "nice", "good", "great", "thanks for the info", "thanks buddy", "got it"}
        if q in greetings or (len(words) <= 3 and any(g in q for g in greetings)):
            return {"type": "acknowledgment", "needs_routing": False}
        
        # Out of scope detection (simple heuristic)
        out_of_scope_keywords = {"weather", "politics", "joke", "recipe", "song", "movie", "sports", "cricket"}
        if any(kw in q for kw in out_of_scope_keywords):
            return {"type": "out_of_scope", "needs_routing": False}
            
        return {"type": "financial", "needs_routing": True}

    async def _rewrite_query(self, query: str) -> str:
        """Rewrite follow-up queries with conversation context."""
        if not self.memory:
            return query
            
        # Only rewrite if it looks like a follow-up
        follow_up_indicators = {"it", "its", "they", "them", "this", "that", "those", "above", "previous", "analyze", "why", "how", "what about"}
        if not any(word in query.lower() for word in follow_up_indicators) and len(query.split()) > 4:
            return query

        try:
            # Build history text
            history_text = "\n".join([
                f"{'User' if m['role'] == 'user' else 'AI'}: {m['content'][:200]}"
                for m in self.memory[-4:]
            ])
            
            prompt = f"""Previous conversation:
{history_text}

Current query: {query}

Rewrite the current query as a standalone financial search query with full context. 
If the user says "analyze it" or "analyze Tata", and we just talked about "Tata Motors" holdings, the rewritten query should be "technical analysis and latest news for Tata Motors stock in India".
Output ONLY the rewritten query.

Rewritten:"""
            
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            rewritten = resp.choices[0].message.content.strip().strip('"')
            if rewritten and len(rewritten) > 5:
                logger.info(f"🔄 Rewritten: {query} -> {rewritten}")
                return rewritten
        except Exception as e:
            logger.error(f"Query rewrite failed: {e}")
            
        return query

    # ------------- LLM streaming -------------
    async def _stream_llm(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None):
        """Async generator that yields tokens from Groq."""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
        )
        
        stream_delay = float(os.getenv("STREAM_DELAY_MS", "20")) / 1000.0
        
        async for chunk in stream:
            delta = getattr(chunk.choices[0], "delta", None)
            if delta and getattr(delta, "content", None):
                token = delta.content
                yield token
                if stream_delay > 0:
                    await asyncio.sleep(stream_delay)

    # ------------- Professional Financial Advisor Prompt -------------
    def _detect_response_length(self, user_input: str) -> str:
        """Detect desired response length from user query."""
        query_lower = user_input.lower()
        detailed_keywords = ['detail', 'detailed', 'analyze', 'analysis', 'deep', 'explain in detail', 'comprehensive', 'full analysis', 'report', 'strategy', 'why', 'compare']
        short_keywords = ['email', 'id', 'name', 'who am i', 'hi', 'hello', 'hey', 'balance', 'total', 'pnl', 'thanks', 'ok']
        
        if any(kw in query_lower for kw in detailed_keywords):
            return "detailed"
        words = query_lower.split()
        if len(words) <= 2 or any(kw == query_lower for kw in short_keywords):
            return "short"
        return "normal"

    def _build_narration_messages(self, user_input: str, routed_result: Dict[str, Any]) -> List[Dict[str, str]]:
        response_length = self._detect_response_length(user_input)
        now = datetime.now().strftime('%A, %B %d, %Y')
        
        sys_prompt = (
            "You are a Senior Technical Portfolio Analyst and Financial Advisor for the Zerodha Kite platform. "
            f"Today is {now}.\n\n"
            
            "CORE DIRECTIVES:\n"
            "- ROLE: Act like a high-end financial advisor. Be technical, precise, and helpful.\n"
            "- TONE: Professional yet conversational. Direct, clear, and confident.\n"
            "- ADAPTIVE: Match query complexity. 'Email' -> 1 word. 'Analysis' -> Deep dive.\n"
            "- MARKET CONTEXT: You have access to 'Market Mentor' tools (Tavily search) for deep research on Indian stocks (NSE, BSE).\n\n"
            
            f"RESPONSE STRATEGY (CURRENT MODE: {response_length.upper()}):\n"
            "- SHORT: Perfect for lookups/acks. 1-2 sentence max. Direct and fast.\n"
            "- NORMAL: Balanced answer. Use a table for data + 2-3 sentences of technical context.\n"
            "- DETAILED: Multi-section report. Include performance summaries, risk notes, and strategic observations using Markdown.\n\n"
            
            "TECHNICAL GUIDELINES:\n"
            "- MARKDOWN: Use Markdown for everything. Bold critical numbers. Use tables for list data.\n"
            "- DATA: NEVER say 'Based on the provided data'. Say 'In your portfolio...' or 'Your holdings show...'.\n"
            "- CURRENCY: Use ₹ (Indian Rupee) with proper formatting (₹1,23,456).\n"
            "- PRECISION: Use technical terms (unrealized P&L, holdings, LTP, margin utilization) correctly.\n\n"
            
            "STRICT SCOPE:\n"
            "1. NO EXTERNAL DATA BEYOND TOOLS: If the info is NOT in the JSON Context and NOT from a research tool result, do not invent it.\n"
            "2. INDIAN FOCUS: All analysis should be Indian-market centric (NSE, BSE).\n"
        )

        all_results = []
        if "data" in routed_result:
            data = routed_result["data"]
            if isinstance(data, dict) and "results" in data:
                results = data["results"]
                if results and isinstance(results, list):
                    for result in results:
                        res_data = result.get("summary") or result.get("data")
                        if res_data:
                            all_results.append(res_data)
            else:
                all_results.append(data)
        
        portfolio_context = _truncate(json.dumps(all_results, indent=2, ensure_ascii=False), 7000)

        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_prompt}]
        for m in self.memory[-6:]:
            messages.append(m)
        
        messages.append({
            "role": "user", 
            "content": (
                f"User Question: {user_input}\n\n"
                f"Context Data (Zerodha/Market): {portfolio_context}\n\n"
                "Provide a professional response. If the user just acknowledged or thanked you, respond briefly and politely."
            )
        })
        
        return messages

    def _remember(self, role: str, content: str):
        self.memory.append({"role": role, "content": content})
        self._maybe_compress_memory()

    def _maybe_compress_memory(self, max_turns: int = 20):
        if len(self.memory) > max_turns:
            self.memory = self.memory[-max_turns:]

    # ------------- Chat entry -------------
    async def chat(self, user_input: str) -> str:
        full_response = ""
        async for token in self.chat_stream(user_input):
            full_response += token
        return full_response

    async def chat_stream(self, user_input: str):
        """Async generator for true streaming with query intelligence."""
        if not user_input.strip():
            yield ""
            return

        # 1. Classify Query
        classification = self._classify_query(user_input)
        
        # 2. Handle simple acknowledgments or out-of-scope without routing
        if not classification["needs_routing"]:
            self._remember("user", user_input)
            
            if classification["type"] == "acknowledgment":
                sys_msg = "You are a polite Senior Portfolio Specialist. Respond briefly (1 sentence) to the user's acknowledgment or thanks."
            else:
                sys_msg = "You are a Senior Portfolio Specialist for Zerodha. The user asked something out of scope. Politely request they stick to portfolio, holdings, margin, or Indian market research queries."
            
            messages = [{"role": "system", "content": sys_msg}] + self.memory[-4:]
            full_answer = ""
            async for token in self._stream_llm(messages, max_tokens=150):
                full_answer += token
                yield token
            self._remember("assistant", full_answer)
            return

        # 3. Financial Query -> Rewrite and Route
        search_query = await self._rewrite_query(user_input)
        
        try:
            routed = await self.master.route_query(search_query)
        except Exception as e:
            error_msg = f"I encountered an issue: {str(e)}. Please try again."
            self._remember("user", user_input)
            self._remember("assistant", error_msg)
            yield error_msg
            return

        # 4. Handle errors from MasterAgent
        if isinstance(routed, dict) and routed.get("status") == "error":
            err_msg = routed.get("message") or "I couldn't process that request."
            if "please log in" in err_msg.lower():
                err_msg = "Your Zerodha Kite session is not active. Please click **Connect** in the sidebar."
            
            self._remember("user", user_input)
            self._remember("assistant", err_msg)
            yield err_msg
            return

        # 5. Successful execution -> LLM narration
        if isinstance(routed, dict) and routed.get("status") == "success":
            if self.narrate:
                messages = self._build_narration_messages(user_input, routed)
                full_answer = ""
                async for token in self._stream_llm(messages):
                    full_answer += token
                    yield token
                self._remember("user", user_input)
                self._remember("assistant", full_answer)
                return
            else:
                pretty = self.master.prefer_message(routed)
                self._remember("user", user_input)
                self._remember("assistant", pretty)
                yield pretty
                return

        # 6. Fallback conversational mode
        self._remember("user", user_input)
        system_msg = {
            "role": "system",
            "content": (
                "You are a Senior Portfolio Specialist for Zerodha Kite. "
                "The user's query couldn't be mapped to a specific tool. \n\n"
                "RULES:\n"
                "1. If they ask about holdings/profile, remind them to stick to those parameters if tool routing failed.\n"
                "2. If they ask about general market stuff, remind them you can analyze their holdings or provide deep research using Indian market data.\n"
                "3. STICK TO SCOPE: No weather/politics/non-finance topics.\n"
                "4. Be brief and professional."
            ),
        }
        messages = [system_msg] + self.memory[-6:]
        full_answer = ""
        async for token in self._stream_llm(messages):
            full_answer += token
            yield token
        self._remember("assistant", full_answer)

async def main():
    async with KiteChatbot() as bot:
        print("💬 Kite Portfolio Chatbot Ready! (type 'quit' to exit)\n")
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input or user_input.lower() in ["quit", "exit", "bye"]: break
                async for token in bot.chat_stream(user_input):
                    print(token, end="", flush=True)
                print()
            except Exception as e:
                print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())

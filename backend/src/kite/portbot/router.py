# # router.py
# import json
# import os
# from typing import Any, Dict, List, Optional

# from groq import AsyncGroq

# ROUTER_SYSTEM = """You are a router that maps a user message to one or more tool calls.
# Return ONLY strict JSON:

# {
#   "plan": [
#     {"agent":"...", "tool":"...", "arguments":{...}},
#     ...
#   ],
#   "answer_style": "short|normal|detailed"
# }

# Rules:
# - Use only tools from the catalog provided.
# - Include as many steps as needed to answer the question end-to-end.
# - If dates are missing for historical data, default to the last 30 calendar days.
# - If a symbol is bare (e.g., INFY), prefer NSE: prefix, e.g., "NSE:INFY".
# - Prefer read-only, safe tools. Do not invent tools.
# - If you truly cannot decide, return a single step that lists or searches.
# - Never include any explanation or prose outside the JSON.
# """

# def _build_catalog_snippet(catalog: List[Dict[str, Any]]) -> str:
#     keep = []
#     for t in catalog:
#         keep.append({
#             "agent": t["agent"],
#             "tool": t["tool"],
#             "description": t.get("description",""),
#             "parameters": t.get("parameters", {}),
#         })
#     return json.dumps(keep, indent=2)


# class ToolRouter:
#     """
#     LLM-based router that can return a multi-step plan.
#     Lazily creates the Groq client; if GROQ_API_KEY is missing, routing is skipped.
#     """
#     def __init__(self, catalog: List[Dict[str, Any]]):
#         self.catalog = catalog
#         self._client: Optional[AsyncGroq] = None
#         self._model = os.getenv("GROQ_ROUTER_MODEL", os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))

#     def _ensure_client(self) -> bool:
#         api_key = os.getenv("GROQ_API_KEY")
#         if not api_key:
#             return False
#         if self._client is None:
#             self._client = AsyncGroq(api_key=api_key)
#         return True

#     async def route(self, user_query: str) -> Optional[Dict[str, Any]]:
#         if not self._ensure_client():
#             return None  # no key → allow caller fallback

#         messages = [
#             {"role": "system", "content": ROUTER_SYSTEM},
#             {"role": "user",
#              "content": f"TOOLS_CATALOG:\n{_build_catalog_snippet(self.catalog)}\n\nUSER_QUERY:\n{user_query}\n\nReturn JSON only."},
#         ]
#         try:
#             resp = await self._client.chat.completions.create(
#                 model=self._model,
#                 messages=messages,
#                 temperature=0.2,
#                 max_tokens=800,
#                 stream=False,
#                 response_format={"type": "json_object"},
#             )
#             raw = resp.choices[0].message.content or "{}"
#             data = json.loads(raw)

#             # lightweight sanity
#             if not isinstance(data, dict):
#                 return None
#             plan = data.get("plan")
#             if not isinstance(plan, list) or not plan:
#                 return None
#             for step in plan:
#                 if not isinstance(step, dict):
#                     return None
#                 if not step.get("agent") or not step.get("tool"):
#                     return None
#                 if "arguments" in step and not isinstance(step["arguments"], dict):
#                     return None
#                 step.setdefault("arguments", {})
#             data.setdefault("answer_style", "detailed")
#             return data
#         except Exception:
#             return None












# C:\Users\Ganesh.More\Desktop\GaneshMore\KiteInfi\src\kite\portbot\router.py
import json
import os
from typing import Any, Dict, List, Optional

from groq import AsyncGroq
from src.utils.llm_balancer import balancer

ROUTER_SYSTEM = """You are a router that maps a user message to one or more tool calls.
Return ONLY strict JSON:

{
  "plan": [
    {"agent":"...", "tool":"...", "arguments":{...}},
    ...
  ],
  "answer_style": "short|normal|detailed"
}

Rules:
- Use only tools from the catalog provided.
- Include as many steps as needed to answer the question end-to-end.
- For deep dives, research, analysis, or 'why/how' questions, ALWAYS use the 'market_analysis' agent.
- For account-specific lookups (holdings, profile, orders, margins), use 'portfolio', 'account', or 'orders' agents.
- If a user asks to 'analyze' a stock they just mentioned as a holding, include both the account data tool AND the market_analysis.analyze_stock tool in the plan.
- If dates are missing for historical data, default to the last 30 calendar days.
- If a symbol is bare (e.g., INFY), prefer NSE: prefix, e.g., "NSE:INFY".
- Prefer read-only, safe tools. Do not invent tools.
- If you truly cannot decide, return a single step that lists or searches.
- Never include any explanation or prose outside the JSON.
"""

def _build_catalog_snippet(catalog: List[Dict[str, Any]]) -> str:
    keep = []
    for t in catalog:
        keep.append({
            "agent": t["agent"],
            "tool": t["tool"],
            "description": t.get("description", ""),
            "parameters": t.get("parameters", {}),
        })
    return json.dumps(keep, indent=2)


class ToolRouter:
    """
    LLM-based router that can return a multi-step plan.
    Lazily creates the Groq client; if keys are missing from balancer, routing is skipped.
    """
    def __init__(self, catalog: List[Dict[str, Any]]):
        self.catalog = catalog
        self._client: Optional[AsyncGroq] = None
        self._model = os.getenv("GROQ_ROUTER_MODEL", os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))

    def _ensure_client(self) -> bool:
        if balancer.key_count == 0:
            return False
        if self._client is None:
            self._client = AsyncGroq(api_key=balancer.get_next_key())
        return True

    async def route(self, user_query: str) -> Optional[Dict[str, Any]]:
        if not self._ensure_client():
            return None  # no key → allow caller fallback

        messages = [
            {"role": "system", "content": ROUTER_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"TOOLS_CATALOG:\n{_build_catalog_snippet(self.catalog)}\n\n"
                    f"USER_QUERY:\n{user_query}\n\n"
                    "Return JSON only."
                ),
            },
        ]
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.2,
                max_tokens=800,
                stream=False,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)

            if not isinstance(data, dict):
                return None
            plan = data.get("plan")
            if not isinstance(plan, list) or not plan:
                return None
            for step in plan:
                if not isinstance(step, dict):
                    return None
                if not step.get("agent") or not step.get("tool"):
                    return None
                if "arguments" in step and not isinstance(step["arguments"], dict):
                    return None
                step.setdefault("arguments", {})
            data.setdefault("answer_style", "detailed")
            return data
        except Exception:
            return None

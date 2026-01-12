# mcp/symbol_utils.py
"""
Utility functions for handling stock symbols and formatting.
Centralized here so both MCP tools and Agent can reuse.
"""

from typing import Dict


def normalize_symbol(symbol: str) -> str:
    """
    Normalize a stock or index symbol for Yahoo Finance.

    - Remove spaces and uppercase letters
    - NSE stocks get ".NS" suffix if missing
    - Common indices mapped to Yahoo Finance codes
    """
    aliases: Dict[str, str] = {
        "SENSEX": "^BSESN",
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
    }

    symbol = symbol.strip().replace(" ", "").upper()
    if symbol in aliases:
        return aliases[symbol]

    # Append .NS only for non-index symbols
    return symbol if symbol.endswith(".NS") or symbol.startswith("^") else symbol + ".NS"

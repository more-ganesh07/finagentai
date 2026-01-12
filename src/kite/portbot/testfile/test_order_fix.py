import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Enable dummy data for testing
os.environ["DUMMY_ORDERS"] = "1"
os.environ["DUMMY_ORDER_HISTORY"] = "1"

from src.kite.portbot.chatbot import KiteChatbot

async def test_order_failure_query():
    """Test the 'why my order failed' query"""
    print("=" * 60)
    print("Testing: 'why my order if failed' query")
    print("=" * 60)
    
    async with KiteChatbot() as bot:
        await bot.chat("why my order if failed")
        print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_order_failure_query())

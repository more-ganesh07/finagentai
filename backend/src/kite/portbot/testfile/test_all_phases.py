import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Enable dummy data for testing
os.environ["DUMMY_ORDERS"] = "1"
os.environ["DUMMY_HOLDINGS"] = "1"
os.environ["DUMMY_POSITIONS"] = "1"

from src.kite.portbot.chatbot import KiteChatbot

async def test_all_phases():
    """Comprehensive test for all 6 phases"""
    print("=" * 70)
    print("COMPREHENSIVE TEST - All 6 Phases")
    print("=" * 70)
    
    async with KiteChatbot() as bot:
        # Phase 1 & 2: Order history fix + Markdown tables
        print("\n📋 Test 1: Failed orders (Phase 1 & 2)")
        print("-" * 70)
        await bot.chat("why my order failed")
        
        # Phase 6: Short response
        print("\n\n📋 Test 2: Short response (Phase 6 - Dynamic Length)")
        print("-" * 70)
        await bot.chat("quick summary of my orders")
        
        # Phase 6: Detailed response
        print("\n\n📋 Test 3: Detailed analysis (Phase 6 - Dynamic Length)")
        print("-" * 70)
        await bot.chat("analyze my portfolio in detail")
        
        # Phase 3: Tavily integration (if TAVILY_API_KEY is set)
        if os.getenv("TAVILY_API_KEY"):
            print("\n\n📋 Test 4: Stock analysis with Tavily (Phase 3)")
            print("-" * 70)
            await bot.chat("analyze INFY stock")
            
            print("\n\n📋 Test 5: Market news (Phase 3)")
            print("-" * 70)
            await bot.chat("latest news on TCS")
        else:
            print("\n\n⚠️ Skipping Tavily tests (TAVILY_API_KEY not set)")
        
        # Phase 4: Memory test
        print("\n\n📋 Test 6: Conversational memory (Phase 4)")
        print("-" * 70)
        await bot.chat("show my portfolio")
        await bot.chat("what about the rejected orders?")  # Should remember context
        
        # Phase 5: Error handling
        print("\n\n📋 Test 7: Error handling (Phase 5)")
        print("-" * 70)
        await bot.chat("show me something that doesn't exist xyz123")
        
        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_all_phases())

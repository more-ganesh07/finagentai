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

async def test_markdown_output():
    """Test the enhanced markdown table output"""
    print("=" * 60)
    print("Testing Enhanced Markdown Output (Phase 2)")
    print("=" * 60)
    
    async with KiteChatbot() as bot:
        # Test 1: Failed orders (should show table)
        print("\n📋 Test 1: Failed orders query")
        print("-" * 60)
        await bot.chat("why my order failed")
        
        print("\n\n📋 Test 2: Show all orders")
        print("-" * 60)
        await bot.chat("show my orders")
        
        print("\n\n📋 Test 3: Portfolio query")
        print("-" * 60)
        await bot.chat("show my portfolio")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_markdown_output())

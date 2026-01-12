import os
import json
import asyncio
from dotenv import load_dotenv

from src.session.manager import SessionManager
from src.session.store import SessionStore
from src.session.kite_mcp_client import KiteMCPClient

load_dotenv(override=True)


def print_separator():
    print("\n" + "="*60 + "\n")


async def test_session_storage():
    """Test session storage functionality."""
    
    print_separator()
    print("🔍 SESSION STORAGE TEST")
    print_separator()
    
    # 1. Check environment variables
    print("1️⃣ Checking Environment Variables:")
    session_file_path = os.getenv("SESSION_FILE_PATH", "./data/sessions/session.json")
    user_id = os.getenv("USER_ID", "demo-user")
    mcp_sse_url = os.getenv("MCP_SSE_URL", "http://localhost:8090/sse")
    
    print(f"   SESSION_FILE_PATH: {session_file_path}")
    print(f"   USER_ID: {user_id}")
    print(f"   MCP_SSE_URL: {mcp_sse_url}")
    print_separator()
    
    # 2. Check if session file exists
    print("2️⃣ Checking Session File:")
    store = SessionStore()
    print(f"   Session file location: {store.session_file}")
    print(f"   File exists: {os.path.exists(store.session_file)}")
    
    if os.path.exists(store.session_file):
        file_size = os.path.getsize(store.session_file)
        print(f"   File size: {file_size} bytes")
        
        # Read and display file contents
        try:
            with open(store.session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            print(f"   ✅ File is valid JSON")
            print(f"\n   File Contents:")
            print(json.dumps(session_data, indent=2))
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    else:
        print(f"   ⚠️ Session file does not exist yet.")
        print(f"   📝 Run 'python src/session/login_once.py' to create a session.")
    print_separator()
    
    # 3. Try to load session using SessionManager
    print("3️⃣ Testing SessionManager.load():")
    sm = SessionManager()
    session = sm.get_active_session(user_id, provider="kite")
    
    if session:
        print(f"   ✅ Session loaded successfully!")
        print(f"   User ID: {session.get('user_id', 'N/A')}")
        print(f"   Provider: {session.get('provider', 'N/A')}")
        print(f"   Status: {session.get('status', 'N/A')}")
        print(f"   Cookie present: {'Yes' if session.get('cookie') else 'No'}")
        if session.get('cookie'):
            cookie_preview = session['cookie'][:20] + "..." if len(session['cookie']) > 20 else session['cookie']
            print(f"   Cookie preview: {cookie_preview}")
        print(f"   Created at: {session.get('created_at', 'N/A')}")
        print(f"   Last validated: {session.get('last_validated_at', 'Never')}")
    else:
        print(f"   ❌ No session found for user_id='{user_id}'")
        print(f"   📝 Run 'python src/session/login_once.py' to create a session.")
    print_separator()
    
    # 4. Test session validation (if session exists)
    if session and session.get('cookie'):
        print("4️⃣ Testing Session Validation:")
        try:
            print(f"   Connecting to MCP server at {mcp_sse_url}...")
            client = KiteMCPClient(mode="sse", user_id=user_id)
            await client.connect()
            
            print(f"   Validating session...")
            is_valid = await client.validate_session()
            
            if is_valid:
                print(f"   ✅ Session is VALID and working!")
                sm.mark_session_valid(user_id, provider="kite")
            else:
                print(f"   ❌ Session validation FAILED")
                print(f"   ⚠️ Session may be expired or invalid")
                sm.mark_session_invalid(user_id, provider="kite")
            
            await client.close()
        except Exception as e:
            print(f"   ❌ Error during validation: {e}")
            print(f"   ⚠️ Make sure MCP server is running at {mcp_sse_url}")
    else:
        print("4️⃣ Skipping validation (no session found)")
    print_separator()
    
    # 5. Summary
    print("5️⃣ SUMMARY:")
    if session and session.get('cookie'):
        print(f"   ✅ Session storage is WORKING")
        print(f"   ✅ Session file: {store.session_file}")
        print(f"   ✅ Session can be loaded")
        if os.path.exists(store.session_file):
            print(f"   ✅ Session file exists and is readable")
    else:
        print(f"   ❌ Session storage is NOT working or session not created")
        print(f"   📝 Next steps:")
        print(f"      1. Make sure MCP server is running")
        print(f"      2. Run: python src/session/login_once.py")
        print(f"      3. Complete login in browser")
        print(f"      4. Run this test again")
    print_separator()


if __name__ == "__main__":
    asyncio.run(test_session_storage())


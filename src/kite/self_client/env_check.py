import os
from dotenv import load_dotenv
load_dotenv(override=True)

keys = [
    "SESSION_FILE_PATH","USER_ID",
    "MCP_HTTP_URL","MCP_SSE_URL","KITE_MCP_MODE",
    "APP_MODE","APP_PORT","APP_HOST",
    "AGENT_TRACE","ROUTER_ENABLED"
]
for k in keys:
    print(f"{k} = {os.getenv(k)}")

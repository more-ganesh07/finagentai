import asyncio
from src.report.data_fetch import fetch_eod_payload

payload = asyncio.run(fetch_eod_payload())
print(payload.keys())

"""
Debug script to check the structure of mcp_raw_output.json
"""
import json

RAW_FILE = r"C:\Users\Ganesh.More\Desktop\GaneshMore\KiteInfi\src\kite\portrep\portreport\mcp_raw_output.json"

with open(RAW_FILE, "r") as f:
    data = json.load(f)

print(f"Total entries in raw file: {len(data)}")
print("\n" + "="*70)

# Find the latest holdings entry
holdings_entries = []
for i, entry in enumerate(data):
    if "holdings" in entry:
        holdings_entries.append((i, entry["holdings"]))

print(f"\nFound {len(holdings_entries)} holdings entries")
if holdings_entries:
    print(f"Latest holdings entry (index {holdings_entries[-1][0]}):")
    latest_holdings = holdings_entries[-1][1]
    print(f"  Status: {latest_holdings.get('status')}")
    print(f"  Data items: {len(latest_holdings.get('data', []))}")
    if latest_holdings.get('data'):
        print(f"  First item: {json.dumps(latest_holdings['data'][0], indent=4)}")

# Find the latest mutual_funds entry
mf_entries = []
for i, entry in enumerate(data):
    if "mutual_funds" in entry:
        mf_entries.append((i, entry["mutual_funds"]))

print(f"\n\nFound {len(mf_entries)} mutual_funds entries")
if mf_entries:
    print(f"Latest mutual_funds entry (index {mf_entries[-1][0]}):")
    latest_mf = mf_entries[-1][1]
    print(f"  Status: {latest_mf.get('status')}")
    print(f"  Data items: {len(latest_mf.get('data', []))}")
    if latest_mf.get('data'):
        print(f"  First item: {json.dumps(latest_mf['data'][0], indent=4)}")

# Find the latest profile entry
profile_entries = []
for i, entry in enumerate(data):
    if "profile" in entry:
        profile_entries.append((i, entry["profile"]))

print(f"\n\nFound {len(profile_entries)} profile entries")
if profile_entries:
    print(f"Latest profile entry (index {profile_entries[-1][0]}):")
    latest_profile = profile_entries[-1][1]
    print(f"  Status: {latest_profile.get('status')}")
    print(f"  User: {latest_profile.get('data', {}).get('user_name')}")

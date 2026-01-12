import requests
from bs4 import BeautifulSoup
import feedparser
import re
from datetime import datetime

def get_ipo_calendar(_: str = "") -> str:
    """
    Fetch current and upcoming IPO details from Indian markets.
    Returns comprehensive IPO information including names, dates, prices, lot sizes, and subscription status.
    
    Usage: Call this function when user asks about IPOs, new listings, or market issues.
    """
    # _log_tool("get_ipo_calendar")  # Uncomment if you have logging
    
    ipos = []
    
    # Fetch RSS feed
    try:
        feed = feedparser.parse("https://ipowatch.in/feed/")
        for entry in feed.entries[:15]:
            name = (entry.title
                   .replace(" IPO Date, Review, Price, Allotment Details", "")
                   .replace(" IPO Allotment Status Online", "")
                   .replace(" IPO Subscription Status", "")
                   .replace(" – IPO Open", ""))
            
            ipo_data = {
                "name": name,
                "published": entry.published if hasattr(entry, 'published') else "N/A",
                "link": entry.link
            }
            
            # Extract details if subscription status page
            if "subscription-status" in entry.link:
                try:
                    resp = requests.get(entry.link, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text = soup.get_text()
                    
                    # Extract price range
                    price_match = re.search(r'₹\s*(\d+)\s*to\s*₹\s*(\d+)', text)
                    if price_match:
                        ipo_data["price_range"] = f"Rs {price_match.group(1)}-{price_match.group(2)}"
                    
                    # Extract lot size
                    lot_match = re.search(r'(\d+,?\d*)\s*shares', text)
                    if lot_match:
                        ipo_data["lot_size"] = f"{lot_match.group(1)} shares"
                    
                    # Extract application amount
                    amount_match = re.search(r'₹\s*(\d+,?\d*,?\d+)\s*application amount', text)
                    if amount_match:
                        ipo_data["application_amount"] = f"Rs {amount_match.group(1)}"
                    
                    # Extract dates
                    date_pattern = r'(\d{1,2}\s+\w+\s+\d{4})'
                    dates = re.findall(date_pattern, text)
                    if len(dates) >= 2:
                        ipo_data["open_date"] = dates[0]
                        ipo_data["close_date"] = dates[1]
                    
                    # Extract subscription status
                    subscription_match = re.search(r'subscribed\s+(?:over\s+)?(\d+\.?\d*)\s*x', text, re.IGNORECASE)
                    if subscription_match:
                        ipo_data["subscription"] = f"{subscription_match.group(1)}x subscribed"
                    
                    # Extract category
                    if "SME" in text:
                        ipo_data["category"] = "SME"
                    elif "Mainboard" in text or "Main Board" in text:
                        ipo_data["category"] = "Mainboard"
                    
                    # Extract listing exchange
                    if "NSE SME" in text:
                        ipo_data["listing"] = "NSE SME"
                    elif "BSE SME" in text:
                        ipo_data["listing"] = "BSE SME"
                    elif "NSE" in text:
                        ipo_data["listing"] = "NSE"
                    elif "BSE" in text:
                        ipo_data["listing"] = "BSE"
                except:
                    pass
            
            ipos.append(ipo_data)
    except:
        pass
    
    # Fetch from Screener.in
    try:
        resp = requests.get("https://www.screener.in/ipo/", timeout=10, 
                          headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        
        if table:
            for row in table.find_all("tr")[1:10]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    name = cols[0].get_text(strip=True)
                    if name and "Total" not in name and len(name) > 3:
                        ipos.append({
                            "name": name,
                            "open_date": cols[1].get_text(strip=True),
                            "close_date": cols[2].get_text(strip=True),
                            "listing_date": cols[3].get_text(strip=True) if len(cols) > 3 else "N/A"
                        })
    except:
        pass
    
    # Remove duplicates
    seen = set()
    unique_ipos = []
    for ipo in ipos:
        clean_name = ipo["name"].lower().replace("ipo", "").strip()[:30]
        if clean_name not in seen and len(clean_name) > 2:
            seen.add(clean_name)
            unique_ipos.append(ipo)
    
    # Return if no data
    if not unique_ipos:
        return "No IPO data available. Check manually at https://ipowatch.in/. Final Answer."
    
    # Format output
    lines = ["IPO Calendar:", "=" * 70]
    
    # Categorize
    ongoing = [ipo for ipo in unique_ipos if "subscription" in ipo.get("name", "").lower() or ipo.get("subscription")]
    upcoming = [ipo for ipo in unique_ipos if "upcoming" in ipo.get("name", "").lower()]
    others = [ipo for ipo in unique_ipos if ipo not in ongoing and ipo not in upcoming]
    
    # Ongoing IPOs
    if ongoing:
        lines.append("\nONGOING IPOs (Currently Open):")
        lines.append("-" * 70)
        for i, ipo in enumerate(ongoing[:8], 1):
            lines.append(f"\n{i}. {ipo['name']}")
            
            if ipo.get("open_date") and ipo.get("close_date"):
                lines.append(f"   Period: {ipo['open_date']} to {ipo['close_date']}")
            
            if ipo.get("price_range"):
                lot_info = f" | Lot: {ipo['lot_size']}" if ipo.get("lot_size") else ""
                lines.append(f"   Price: {ipo['price_range']}{lot_info}")
            
            if ipo.get("application_amount"):
                lines.append(f"   Min Application: {ipo['application_amount']}")
            
            if ipo.get("subscription"):
                lines.append(f"   Status: {ipo['subscription']}")
            
            if ipo.get("category"):
                listing = f" | {ipo['listing']}" if ipo.get("listing") else ""
                lines.append(f"   Type: {ipo['category']}{listing}")
            
            if ipo.get("link"):
                lines.append(f"   Details: {ipo['link']}")
    
    # Upcoming IPOs
    if upcoming:
        lines.append("\n\nUPCOMING IPOs:")
        lines.append("-" * 70)
        for i, ipo in enumerate(upcoming[:8], 1):
            lines.append(f"\n{i}. {ipo['name']}")
            
            if ipo.get("open_date"):
                close = f" to {ipo['close_date']}" if ipo.get("close_date") else ""
                lines.append(f"   Opens: {ipo['open_date']}{close}")
            
            if ipo.get("price_range"):
                lines.append(f"   Price: {ipo['price_range']}")
            
            if ipo.get("link"):
                lines.append(f"   Details: {ipo['link']}")
    
    # Recent Updates
    if others:
        lines.append("\n\nRECENT IPO UPDATES:")
        lines.append("-" * 70)
        for i, ipo in enumerate(others[:8], 1):
            lines.append(f"\n{i}. {ipo['name']}")
            
            if ipo.get("open_date"):
                close = f" to {ipo['close_date']}" if ipo.get("close_date") else ""
                lines.append(f"   Period: {ipo['open_date']}{close}")
            
            if ipo.get("listing_date"):
                lines.append(f"   Listing: {ipo['listing_date']}")
            
            if ipo.get("link"):
                lines.append(f"   Details: {ipo['link']}")
    
    lines.append("\n" + "=" * 70)
    lines.append(f"Total: {len(unique_ipos)} | Ongoing: {len(ongoing)} | Upcoming: {len(upcoming)} | Updates: {len(others)}")
    lines.append("=" * 70)
    lines.append("Final Answer.")
    
    return "\n".join(lines)


# Test function
if __name__ == "__main__":
    print("Fetching IPO Calendar...")
    print(get_ipo_calendar())
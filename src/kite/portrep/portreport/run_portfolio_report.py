
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.kite.portrep.portreport.viz.generate_charts import PortfolioChartGenerator


async def fetch_portfolio_data(master_agent=None):
    """Step 1: Login to Kite and fetch portfolio data."""
    print("\n" + "="*60)
    print("STEP 1: FETCHING PORTFOLIO DATA")
    print("="*60)
    
    try:
        # Import filter_mcp_data logic
        from src.kite.portrep.portreport.filter_mcp_data import main as fetch_data
        
        print("🔐 Logging into Kite and fetching portfolio...")
        await fetch_data(master_agent=master_agent)
        print("✅ Portfolio data fetched successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to fetch portfolio data: {e}")
        return False


def generate_charts():
    """Step 2: Generate market and stock charts."""
    print("\n" + "="*60)
    print("STEP 2: GENERATING CHARTS")
    print("="*60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        script_dir = Path(__file__).parent
        json_path = Path(os.getenv("PORTFOLIO_SUMMARY_JSON_PATH", str(script_dir / "mcp_summary.json")))
        output_dir = Path(os.getenv("CHARTS_DIR", str(script_dir / "viz" / "charts")))
        
        if not json_path.exists():
            print(f"❌ Error: {json_path} not found!")
            return False
        
        generator = PortfolioChartGenerator(json_path, output_dir)
        charts = generator.generate_all_charts()
        
        if charts:
            print(f"✅ Generated {len(charts)} charts successfully")
            return True
        else:
            print("⚠️ No charts were generated")
            return False
            
    except Exception as e:
        print(f"❌ Failed to generate charts: {e}")
        return False


async def generate_report(send_email: bool = True):
    """Step 3: Generate PDF report with charts."""
    print("\n" + "="*60)
    print("STEP 3: GENERATING REPORT")
    print("="*60)
    
    try:
        # Import and run generate_report (async version directly)
        from src.kite.portrep.portreport.generate_report import main_async as create_report
        
        print(f"📝 Creating portfolio report with charts (Email: {send_email})...")
        html_content = await create_report(send_email=send_email)
        
        if html_content:
            status_msg = "and emailed successfully" if send_email else "successfully (email skipped)"
            print(f"✅ Report generated {status_msg}")
            return html_content
        return None
    except Exception as e:
        print(f"❌ Failed to generate report: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main(master_agent=None, send_email: bool = True):
    """Main entry point - orchestrates the entire process."""
    print("\n" + "="*70)
    print(" " * 15 + "PORTFOLIO REPORT GENERATOR")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Step 1: Fetch portfolio data
    if not await fetch_portfolio_data(master_agent=master_agent):
        print("\n❌ FAILED: Could not fetch portfolio data")
        print("Please check your Kite credentials and try again.")
        return None
    
    # Step 2: Generate charts
    if not generate_charts():
        print("\n⚠️ WARNING: Chart generation failed")
        print("Continuing with report generation (without charts)...")
    
    # Step 3: Generate and email report
    html_content = await generate_report(send_email=send_email)
    if not html_content:
        print("\n❌ FAILED: Could not generate report")
        return None
    
    # Success!
    print("\n" + "="*70)
    status_msg = "and emailed!" if send_email else "successfully (preview ready)!"
    print(f"🎉 SUCCESS! Portfolio report generated {status_msg}")
    print("="*70)
    if send_email:
        print("\n📧 Check your email inbox for the PDF report.")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return html_content


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

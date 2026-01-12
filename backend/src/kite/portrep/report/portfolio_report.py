# run_eod_report.py
import os
import asyncio
import datetime as dt
from pathlib import Path

from src.report.config import (
    EOD_REPORTS_ENABLED,
    REPORTS_DIR,
    FALLBACK_EMAIL,
)

from src.report.data_fetch import fetch_eod_payload, extract_recipient_email
from src.report.pdf_builder import build_eod_pdf
from src.report.emailer import send_email_with_attachment


async def main():
    if not EOD_REPORTS_ENABLED:
        print("EOD reports disabled by env. Set EOD_REPORTS_ENABLED=1 to enable.")
        return

    payload = await fetch_eod_payload()

    # recipient
    to = extract_recipient_email(payload.get("profile", {}), fallback_email=FALLBACK_EMAIL)
    if not to:
        print("No recipient email found (profile or FALLBACK_EMAIL). Exiting.")
        return

    # filename
    today = dt.date.today().isoformat()
    out_dir = Path(REPORTS_DIR)
    out_path = out_dir / f"{today}_EOD.pdf"

    # build pdf
    build_eod_pdf(payload, str(out_path))

    # send
    send_email_with_attachment(
        to_addr=to,
        subject=f"EOD Portfolio Brief — {dt.date.today():%d %b %Y}",
        body="Attached is your daily portfolio brief.\n\n(Reply STOP to opt out.)",
        attachment_path=str(out_path),
    )
    print(f"✅ Sent EOD report to {to}: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())

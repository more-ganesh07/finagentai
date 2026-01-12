# emailer.py
import os
from email.message import EmailMessage
import email.utils
import smtplib
import markdown
from xhtml2pdf import pisa

from .mail_config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_FROM


def convert_md_to_pdf(md_content: str, output_path: str):
    """Converts Markdown content to PDF and saves it."""
    html_text = markdown.markdown(md_content, extensions=['tables'])
    
    # Add some basic styling
    full_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; font-size: 12px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_text}
    </body>
    </html>
    """
    
    with open(output_path, "wb") as result_file:
        pisa_status = pisa.CreatePDF(full_html, dest=result_file)
        
    if pisa_status.err:
        raise Exception(f"PDF generation failed: {pisa_status.err}")
    print(f"✅ PDF Report generated: {output_path}")


def send_email_with_attachment(to_addr: str, subject: str, body: str, attachment_path: str):
    if not to_addr:
        raise ValueError("No recipient email address")

    msg = EmailMessage()
    msg["To"] = to_addr
    msg["From"] = MAIL_FROM
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg.set_content(body)

    with open(attachment_path, "rb") as f:
        data = f.read()
    msg.add_attachment(data, maintype="application", subtype="pdf", filename=os.path.basename(attachment_path))

    # SSL (465) is simplest for Gmail
    with smtplib.SMTP_SSL(host=SMTP_HOST, port=SMTP_PORT) as s:
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    print(f"✅ Email sent successfully to {to_addr}")

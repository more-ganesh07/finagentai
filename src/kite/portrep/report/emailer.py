# emailer.py
import os
from email.message import EmailMessage
import email.utils
import smtplib

from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_FROM


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

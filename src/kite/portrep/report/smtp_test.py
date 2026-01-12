import smtplib, ssl
from email.mime.text import MIMEText

msg = MIMEText("Hello, this is a test email!")
msg["Subject"] = "SMTP Test"
msg["From"] = "finagentai.team@gmail.com"
msg["To"] = "moreganesh631.team@gmail.com"

context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login("finagentai.team@gmail.com", "rypgjltehyhlimsg")
    server.send_message(msg)

print("✅ Email sent successfully!")

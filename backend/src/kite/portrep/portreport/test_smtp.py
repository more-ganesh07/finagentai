import smtplib
from src.kite.portrep.portreport.mail_config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

def test_smtp():
    print(f"Testing SMTP connection to {SMTP_HOST}:{SMTP_PORT}...")
    try:
        with smtplib.SMTP_SSL(host=SMTP_HOST, port=SMTP_PORT) as s:
            print("Connected. Logging in...")
            s.login(SMTP_USER, SMTP_PASS)
            print("✅ Login successful!")
    except Exception as e:
        print(f"❌ SMTP Test Failed: {e}")

if __name__ == "__main__":
    test_smtp()

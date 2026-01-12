# config.py
import os
from dotenv import load_dotenv

# Load env once for the report package
load_dotenv(override=True)

# Feature flag
EOD_REPORTS_ENABLED = os.getenv("EOD_REPORTS_ENABLED", "1").strip().lower() not in ("0", "false", "no")

# SMTP / Mail
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # 465 SSL by default
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER or "noreply@example.com")
FALLBACK_EMAIL = os.getenv("FALLBACK_EMAIL", "")

# Output dir for generated PDFs
REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")

# Optional tracing from agents
AGENT_TRACE = os.getenv("AGENT_TRACE", "0").strip().lower() not in ("0", "false")

# Groq routing toggle (FYI, not used directly here)
ROUTER_ENABLED = os.getenv("ROUTER_ENABLED", "1").strip().lower() not in ("0", "false")

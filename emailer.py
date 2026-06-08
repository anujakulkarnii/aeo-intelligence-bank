"""
AEO Intelligence System — Emailer
Sends the AEO digest via Resend API.
"""

import resend
from config import RESEND_API_KEY, EMAIL_RECIPIENT, COMPANY


def send_digest(digest: str, run_date: str) -> bool:
    """
    Send digest email via Resend.
    Returns True on success, False on failure.
    """
    if not RESEND_API_KEY:
        print("[emailer] ERROR: RESEND_API_KEY not set.")
        return False

    if not EMAIL_RECIPIENT:
        print("[emailer] ERROR: EMAIL_RECIPIENT not set.")
        return False

    resend.api_key = RESEND_API_KEY

    subject = f"AEO Pulse — {COMPANY} — {run_date[:10]}"

    try:
        params: resend.Emails.SendParams = {
            "from":    "onboarding@resend.dev",
            "to":      [EMAIL_RECIPIENT],
            "subject": subject,
            "html":    digest,
        }
        result = resend.Emails.send(params)
        email_id = result.get("id", "unknown") if isinstance(result, dict) else getattr(result, "id", "unknown")
        print(f"[emailer] Email sent successfully. ID: {email_id}")
        print(f"[emailer] To: {EMAIL_RECIPIENT} | Subject: {subject}")
        return True

    except Exception as e:
        print(f"[emailer] ERROR sending email: {e}")
        return False

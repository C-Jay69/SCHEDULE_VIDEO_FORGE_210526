"""Email sending via SMTP. Optional — all callers must handle failure."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from ..config import settings

logger = logging.getLogger(__name__)


def _send(subject: str, recipient: str, text: str) -> None:
    if not (settings.smtp_host and settings.smtp_from):
        raise RuntimeError("SMTP not configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("VideoForge", settings.smtp_from))
    msg["To"] = recipient
    msg.attach(MIMEText(text, "plain"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, [recipient], msg.as_string())


async def send_password_reset_email(recipient: str, reset_token: str) -> None:
    reset_url = f"{settings.next_public_app_url}/reset-password?token={reset_token}"
    text = (
        f"Hello,\n\n"
        f"We received a request to reset your VideoForge password.\n"
        f"Open the link below to choose a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in 1 hour. If you didn't request it, you can ignore this email.\n"
    )
    _send("Reset your VideoForge password", recipient, text)

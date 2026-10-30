import logging
import smtplib
from email.message import EmailMessage

from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_reset_email(to_email: str, reset_link: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Reset your TeamFlow password"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.set_content(
        "Hi,\n\n"
        "We received a request to reset your TeamFlow password.\n"
        f"Use the link below (valid for {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes):\n\n"
        f"{reset_link}\n\n"
        "If you didn't request this, you can safely ignore this email.\n"
    )
    msg.add_alternative(
        f"""\
<html>
  <body>
    <p>Hi,</p>
    <p>We received a request to reset your TeamFlow password.</p>
    <p><a href="{reset_link}">Reset password</a></p>
    <p>This link is valid for {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.</p>
    <p>If you didn't request this, you can safely ignore this email.</p>
  </body>
</html>
""",
        subtype="html",
    )
    return msg


@celery_app.task(
    name="auth.send_password_reset_email",
    autoretry_for=(smtplib.SMTPException, OSError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_password_reset_email(to_email: str, reset_link: str) -> None:
    msg = _build_reset_email(to_email, reset_link)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    logger.info("Password reset email sent")
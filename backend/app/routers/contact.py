import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.core.rate_limit import client_key, limiter
from app.schemas.contact import ContactRequest, ContactResponse

router = APIRouter(prefix="/api/contact", tags=["contact"])
settings = get_settings()


def _send_contact_email(payload: ContactRequest) -> None:
    if not settings.contact_owner_email or not settings.contact_smtp_host:
        raise RuntimeError("Contact delivery has not been configured.")

    message = EmailMessage()
    message["Subject"] = f"[PawAI Contact] {payload.subject}"
    message["From"] = settings.contact_smtp_from_email or settings.contact_owner_email
    message["To"] = settings.contact_owner_email
    message["Reply-To"] = str(payload.email)
    message.set_content(
        f"Name: {payload.name}\nEmail: {payload.email}\n\nMessage:\n{payload.message}"
    )

    with smtplib.SMTP(settings.contact_smtp_host, settings.contact_smtp_port, timeout=10) as smtp:
        if settings.contact_smtp_starttls:
            smtp.starttls()
        if settings.contact_smtp_username and settings.contact_smtp_password:
            smtp.login(settings.contact_smtp_username, settings.contact_smtp_password)
        smtp.send_message(message)


@router.post("", response_model=ContactResponse, status_code=status.HTTP_202_ACCEPTED)
def send_contact_message(payload: ContactRequest, request: Request):
    """Validate and forward a contact form message without exposing SMTP secrets."""
    if settings.rate_limit_enabled:
        ip = request.client.host if request.client else None
        key = f"contact:{client_key(ip, str(payload.email))}"
        if not limiter.allow(key, limit=5, window_seconds=3600):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many messages. Please wait and try again later.",
            )

    try:
        _send_contact_email(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except (OSError, smtplib.SMTPException):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="We could not deliver your message right now. Please try again later.",
        )

    return ContactResponse(message="Thanks for contacting PawAI. We will get back to you soon.")

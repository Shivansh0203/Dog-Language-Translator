import uuid
from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.session import SessionModel
from app.models.user import User

settings = get_settings()


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def current_session(
    db: Session = Depends(get_db),
    session_cookie: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> SessionModel:
    if not session_cookie:
        raise _unauthorized()

    try:
        session_uuid = uuid.UUID(session_cookie)
    except ValueError:
        raise _unauthorized()

    session = db.get(SessionModel, session_uuid)
    if session is None:
        raise _unauthorized()

    if session.expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise _unauthorized()

    session.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return session


def current_user(
    db: Session = Depends(get_db),
    session: SessionModel = Depends(current_session),
) -> User:
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user

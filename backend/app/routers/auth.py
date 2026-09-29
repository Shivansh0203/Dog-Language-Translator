import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.rate_limit import client_key, limiter
from app.core.security import clear_session_cookie, set_session_cookie
from app.db import get_db
from app.deps import current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    UserOut,
)
from app.services.auth_service import (
    DuplicateUserError,
    InvalidCredentialsError,
    authenticate_user,
    create_session,
    delete_session,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

def _check_rate_limit(request: Request, identifier: str, *, limit: int, window_seconds: int, action: str) -> None:
    if not settings.rate_limit_enabled:
        return
    key = f"{action}:{client_key(request.client.host if request.client else None, identifier)}"
    if not limiter.allow(key, limit=limit, window_seconds=window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait and try again.",
            headers={"Retry-After": str(window_seconds)},
        )



@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    _check_rate_limit(request, payload.email, limit=5, window_seconds=3600, action="register")
    try:
        user, pet = register_user(db, payload)
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with that {exc.field} already exists.",
        )

    # Auto-login after successful registration.
    session = create_session(
        db,
        user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    set_session_cookie(response, str(session.id))

    return RegisterResponse(user=UserOut.model_validate(user), pet=pet)


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    _check_rate_limit(request, payload.identifier, limit=10, window_seconds=900, action="login")
    try:
        user = authenticate_user(db, payload.identifier, payload.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )

    session = create_session(
        db,
        user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    set_session_cookie(response, str(session.id))

    return UserOut.model_validate(user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_cookie: str | None = Cookie(default=None, alias=settings.session_cookie_name),
):
    # Logout is intentionally idempotent: a stale/expired cookie still
    # receives a successful response and is cleared in the browser.
    if session_cookie:
        try:
            delete_session(db, uuid.UUID(session_cookie))
        except ValueError:
            pass
    clear_session_cookie(response)
    return MessageResponse(message="Logged out.")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return UserOut.model_validate(user)


# ---------------------------------------------------------------------------
# Deferred endpoints. Deliberately NOT implemented in this milestone - wired
# here only so the API surface/documentation is explicit about what's coming,
# and so the frontend can point at a stable path later. Calling either of
# these right now returns 501 Not Implemented.
# ---------------------------------------------------------------------------
class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/password/forgot", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def forgot_password(payload: ForgotPasswordRequest):
    """DEFERRED: will email a time-limited reset token. Not implemented yet."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset is not implemented yet.",
    )


@router.post("/password/reset", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def reset_password(payload: ResetPasswordRequest):
    """DEFERRED: will consume the reset token and set a new password hash. Not implemented yet."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset is not implemented yet.",
    )

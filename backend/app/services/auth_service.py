import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, needs_rehash, new_session_expiry, verify_password
from app.models.pet import Pet
from app.models.session import SessionModel
from app.models.user import User
from app.schemas.auth import PetCreate, RegisterRequest

DUMMY_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=2$SO0dmzF8dIcath6YQoykXQ$mgU/4dj8JvBYfrfKbWCzG3Yh8fgsycPOY4KD7TDXLgo"


class AuthError(Exception):
    """Base class for auth-flow errors that routers translate into HTTP responses."""


class DuplicateUserError(AuthError):
    def __init__(self, field: str):
        self.field = field
        super().__init__(f"{field} already in use")


class InvalidCredentialsError(AuthError):
    pass


def register_user(db: Session, payload: RegisterRequest) -> tuple[User, Pet | None]:
    existing_email = db.scalar(select(User).where(User.email == payload.email))
    if existing_email:
        raise DuplicateUserError("email")

    existing_username = db.scalar(select(User).where(User.username == payload.username))
    if existing_username:
        raise DuplicateUserError("username")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()  # get user.id without committing yet

    pet: Pet | None = None
    if payload.pet is not None:
        pet = _create_pet_for_user(db, user.id, payload.pet)

    db.commit()
    db.refresh(user)
    if pet is not None:
        db.refresh(pet)
    return user, pet


def _create_pet_for_user(db: Session, user_id: uuid.UUID, pet_in: PetCreate) -> Pet:
    pet = Pet(
        user_id=user_id,
        name=pet_in.name,
        breed=pet_in.breed,
        age=pet_in.age,
        gender=pet_in.gender,
        species=pet_in.species,
    )
    db.add(pet)
    db.flush()
    return pet


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    """Look up by email or username. Always raise the same error on any
    failure so we never reveal which part of the credential was wrong."""
    user = db.scalar(
        select(User).where(or_(User.email == identifier, User.username == identifier))
    )
    if user is None or not user.is_active:
        # Burn roughly the same password-hash verification work for unknown
        # accounts so timing leaks reveal less about account existence.
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise InvalidCredentialsError()

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
        db.refresh(user)

    return user


def create_session(
    db: Session, user_id: uuid.UUID, user_agent: str | None, ip_address: str | None
) -> SessionModel:
    session = SessionModel(
        user_id=user_id,
        expires_at=new_session_expiry(),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: uuid.UUID) -> None:
    session = db.get(SessionModel, session_id)
    if session is not None:
        db.delete(session)
        db.commit()

"""Import every model module so SQLAlchemy's mapper registry knows about all
of them before relationships (declared as string references) are resolved.
Anything that needs Base.metadata (Alembic, create_all in tests) should import
this package rather than individual model modules."""

from app.models.user import User  # noqa: F401
from app.models.pet import Pet  # noqa: F401
from app.models.session import SessionModel  # noqa: F401
from app.models.media import Media  # noqa: F401

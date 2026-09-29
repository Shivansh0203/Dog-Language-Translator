import uuid
from datetime import datetime
from pydantic import BaseModel


class MediaOut(BaseModel):
    id: uuid.UUID
    pet_id: uuid.UUID | None
    animal_type: str
    media_type: str
    original_filename: str
    content_type: str | None
    created_at: datetime
    url: str

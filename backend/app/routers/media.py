import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import current_user
from app.models.media import Media
from app.models.pet import Pet
from app.models.user import User
from app.schemas.media import MediaOut

router = APIRouter(prefix="/api/media", tags=["media"])
MEDIA_DIR = Path(__file__).resolve().parents[2] / "media"

def output(record):
    return MediaOut(id=record.id, pet_id=record.pet_id, animal_type=record.animal_type, media_type=record.media_type, original_filename=record.original_filename, content_type=record.content_type, created_at=record.created_at, url=f"/api/media/{record.id}/file")

@router.post("", response_model=MediaOut, status_code=201)
def upload(file: UploadFile = File(...), animal_type: str = Form(...), pet_id: uuid.UUID | None = Form(None), db: Session = Depends(get_db), user: User = Depends(current_user)):
    animal_type = animal_type.lower()
    if animal_type != "dog": raise HTTPException(422, "animal_type must be dog.")
    if pet_id:
        pet = db.get(Pet, pet_id)
        if pet is None or pet.user_id != user.id: raise HTTPException(404, "Pet not found.")
        if pet.species != animal_type: raise HTTPException(422, "Pet species does not match media type.")
    media_type = (file.content_type or "").split("/", 1)[0]
    if media_type not in {"image", "video", "audio"}: raise HTTPException(415, "Upload an image, video, or audio file.")
    original = Path(file.filename or "upload").name[:255]
    stored = f"{uuid.uuid4()}{Path(original).suffix.lower()[:16]}"
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    with (MEDIA_DIR / stored).open("wb") as destination: shutil.copyfileobj(file.file, destination)
    record = Media(user_id=user.id, pet_id=pet_id, animal_type=animal_type, media_type=media_type, original_filename=original, stored_filename=stored, content_type=file.content_type)
    db.add(record); db.commit(); db.refresh(record)
    return output(record)

@router.get("", response_model=list[MediaOut])
def list_media(animal_type: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Media).where(Media.user_id == user.id).order_by(Media.created_at.desc())
    if animal_type: query = query.where(Media.animal_type == animal_type.lower())
    return [output(item) for item in db.scalars(query).all()]

def owned(db, media_id, user):
    record = db.get(Media, media_id)
    if record is None or record.user_id != user.id: raise HTTPException(404, "Media not found.")
    return record

@router.get("/{media_id}/file")
def download(media_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    record = owned(db, media_id, user); path = MEDIA_DIR / record.stored_filename
    if not path.is_file(): raise HTTPException(404, "Stored file not found.")
    return FileResponse(path, media_type=record.content_type, filename=record.original_filename)

@router.delete("/{media_id}", status_code=204)
def delete(media_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    record = owned(db, media_id, user); (MEDIA_DIR / record.stored_filename).unlink(missing_ok=True); db.delete(record); db.commit()

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models.pet import Pet
from app.models.user import User
from app.schemas.pet import PetCreate, PetOut

router = APIRouter(prefix="/api/pets", tags=["pets"])


@router.get("", response_model=list[PetOut])
def list_my_pets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    pets = db.scalars(select(Pet).where(Pet.user_id == user.id)).all()
    return pets


@router.post("", response_model=PetOut, status_code=status.HTTP_201_CREATED)
def create_pet(
    payload: PetCreate, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    pet = Pet(
        user_id=user.id,
        name=payload.name,
        breed=payload.breed,
        age=payload.age,
        gender=payload.gender,
        species=payload.species,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def _get_owned_pet_or_404(db: Session, pet_id: uuid.UUID, user: User) -> Pet:
    pet = db.get(Pet, pet_id)
    if pet is None or pet.user_id != user.id:
        # Same 404 whether the pet doesn't exist or belongs to someone else -
        # never reveal that another user's pet ID is valid.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")
    return pet


@router.get("/{pet_id}", response_model=PetOut)
def get_pet(pet_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _get_owned_pet_or_404(db, pet_id, user)


@router.patch("/{pet_id}", response_model=PetOut)
def update_pet(
    pet_id: uuid.UUID,
    payload: PetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    pet = _get_owned_pet_or_404(db, pet_id, user)
    pet.name = payload.name
    pet.breed = payload.breed
    pet.age = payload.age
    pet.gender = payload.gender
    pet.species = payload.species
    db.commit()
    db.refresh(pet)
    return pet

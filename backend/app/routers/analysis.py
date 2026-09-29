import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models.media import Media
from app.models.user import User
from app.services.gemini_services import generate_sentence


router = APIRouter(
    prefix="/api/analyze",
    tags=["analysis"],
)

MEDIA_DIR = Path(__file__).resolve().parents[2] / "media"

ML_API_URL = "http://127.0.0.1:8001"


@router.post("/{media_id}")
async def analyze_media(
    media_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    # --------------------------------------------------
    # Find media
    # --------------------------------------------------

    media = db.get(Media, media_id)

    if media is None or media.user_id != user.id:
        raise HTTPException(
            status_code=404,
            detail="Media not found.",
        )

    # --------------------------------------------------
    # Currently we support dog videos
    # --------------------------------------------------

    if media.animal_type != "dog":
        raise HTTPException(
            status_code=422,
            detail="Only dog analysis is currently supported.",
        )

    if media.media_type != "video":
        raise HTTPException(
            status_code=422,
            detail="This endpoint currently expects a video.",
        )

    # --------------------------------------------------
    # Locate stored video
    # --------------------------------------------------

    video_path = MEDIA_DIR / media.stored_filename

    if not video_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored media file not found.",
        )

    # --------------------------------------------------
    # Send video to ML API
    # --------------------------------------------------

    try:
        async with httpx.AsyncClient(
            timeout=300.0
        ) as client:

            with video_path.open("rb") as video_file:

                response = await client.post(
                    f"{ML_API_URL}/predict-video",
                    files={
                        "file": (
                            media.original_filename,
                            video_file,
                            media.content_type
                            or "video/mp4",
                        )
                    },
                )

        if response.status_code != 200:

            raise HTTPException(
                status_code=502,
                detail=f"ML API error: {response.text}",
            )

        result = response.json()
        
        try:
            ai_sentence = generate_sentence(video_path,result)
            result["ai_interpretation"] = ai_sentence

        except Exception as e:
            print(f"AI interpretation failed: {e}")
            result["ai_interpretation"] = None

    except httpx.RequestError as e:

        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to ML API: {str(e)}",
        )

    # --------------------------------------------------
    # Return ML result
    # --------------------------------------------------

    return {
        "media_id": str(media.id),
        "filename": media.original_filename,
        "media_type": media.media_type,
        "result": result,
    }
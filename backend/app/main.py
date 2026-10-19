from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, contact, media, pets, analysis, chat, mobile_camera

settings = get_settings()

app = FastAPI(title="PawAI API", version="0.1.0")

# credentials=True is required so the browser sends the HttpOnly session
# cookie cross-origin; allow_origins must therefore be an explicit list,
# never "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pets.router)
app.include_router(contact.router)
app.include_router(media.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(mobile_camera.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

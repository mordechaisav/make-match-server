from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers all mappers before requests are served)
from app.core.config import settings
from app.routers import shadchanim

app = FastAPI(
    title="Shadchan Server",
    servers=[{"url": settings.public_api_url}] if settings.public_api_url else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(shadchanim.router)

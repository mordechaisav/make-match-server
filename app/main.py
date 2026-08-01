from fastapi import FastAPI

from app import models  # noqa: F401  (registers all mappers before requests are served)
from app.routers import shadchanim

app = FastAPI(title="Shadchan Server")

app.include_router(shadchanim.router)

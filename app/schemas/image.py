from typing import Literal

from pydantic import BaseModel

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class UploadUrlIn(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"]


class UploadUrlOut(BaseModel):
    upload_url: str
    path: str
    expires_in: int

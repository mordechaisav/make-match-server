import uuid
from typing import Callable

from botocore.exceptions import ClientError

from app.core.b2_client import get_b2_client
from app.core.config import settings
from app.schemas.image import CONTENT_TYPE_EXTENSIONS, UploadUrlOut


def generate_upload_url(shadchan_id: int, content_type: str) -> UploadUrlOut:
    extension = CONTENT_TYPE_EXTENSIONS[content_type]
    key = f"candidates/{shadchan_id}/{uuid.uuid4()}{extension}"
    upload_url = get_b2_client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.b2_bucket_name, "Key": key, "ContentType": content_type},
        ExpiresIn=settings.b2_upload_url_expires_in,
    )
    return UploadUrlOut(upload_url=upload_url, path=key, expires_in=settings.b2_upload_url_expires_in)


def object_exists(key: str) -> bool:
    try:
        get_b2_client().head_object(Bucket=settings.b2_bucket_name, Key=key)
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
            return False
        raise


def generate_read_url(key: str) -> str:
    return get_b2_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.b2_bucket_name, "Key": key},
        ExpiresIn=settings.b2_read_url_expires_in,
    )


def delete_object(key: str) -> None:
    try:
        get_b2_client().delete_object(Bucket=settings.b2_bucket_name, Key=key)
    except ClientError:
        pass  # best-effort - don't fail the request over B2 cleanup


def get_upload_url_generator() -> Callable[[int, str], UploadUrlOut]:
    return generate_upload_url


def get_object_checker() -> Callable[[str], bool]:
    return object_exists


def get_read_url_generator() -> Callable[[str], str]:
    return generate_read_url


def get_object_deleter() -> Callable[[str], None]:
    return delete_object

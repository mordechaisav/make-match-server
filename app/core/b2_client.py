import boto3

from app.core.config import settings

_client = None


def get_b2_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.b2_endpoint_url,
            aws_access_key_id=settings.b2_key_id,
            aws_secret_access_key=settings.b2_application_key,
            region_name=settings.b2_region,
        )
    return _client

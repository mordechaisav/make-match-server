import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

_app: firebase_admin.App | None = None


def get_firebase_app() -> firebase_admin.App:
    global _app
    if _app is None:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        try:
            _app = firebase_admin.initialize_app(cred)
        except ValueError:
            # another thread's concurrent first call already initialized the default app
            _app = firebase_admin.get_app()
    return _app

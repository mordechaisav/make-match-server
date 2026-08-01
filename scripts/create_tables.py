"""Dev-only helper: create all tables directly from the ORM models.

Run with: python -m scripts.create_tables
For real deployments, use Alembic migrations instead.
"""

from app.core.database import init_db

if __name__ == "__main__":
    init_db()

"""add firebase_uid to shadchanim

Revision ID: b29eb184fccf
Revises: fdc5c8385f41
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b29eb184fccf'
down_revision: Union[str, Sequence[str], None] = 'fdc5c8385f41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('shadchanim', sa.Column('firebase_uid', sa.String(length=128), nullable=True))
    op.create_unique_constraint('uq_shadchanim_firebase_uid', 'shadchanim', ['firebase_uid'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_shadchanim_firebase_uid', 'shadchanim', type_='unique')
    op.drop_column('shadchanim', 'firebase_uid')

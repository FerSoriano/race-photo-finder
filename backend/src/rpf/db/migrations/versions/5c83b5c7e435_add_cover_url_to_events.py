"""Add cover_url to events

Revision ID: 5c83b5c7e435
Revises: 81bb3bf5563d
Create Date: 2026-08-12 17:50:06.562802

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c83b5c7e435"
down_revision: str | Sequence[str] | None = "81bb3bf5563d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Autogenerate also proposed dropping ix_photo_bibs_number_trgm -- a false
    # positive, since that index is raw SQL and not represented in the models'
    # metadata. Removed by hand; see db/migrations/versions/81bb3bf5563d.
    op.add_column("events", sa.Column("cover_url", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("events", "cover_url")

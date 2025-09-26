"""final_test

Revision ID: bbc966852674
Revises: 55fd7c3635c3
Create Date: 2025-09-26 19:20:22.713220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbc966852674'
down_revision: Union[str, Sequence[str], None] = '55fd7c3635c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

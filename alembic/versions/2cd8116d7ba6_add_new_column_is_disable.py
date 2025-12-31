"""add new column is_disable

Revision ID: 2cd8116d7ba6
Revises: d33b3dc1b891
Create Date: 2025-12-28 15:05:16.639636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cd8116d7ba6'
down_revision: Union[str, Sequence[str], None] = 'd33b3dc1b891'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

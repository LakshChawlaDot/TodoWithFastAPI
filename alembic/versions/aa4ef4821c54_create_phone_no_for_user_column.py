"""create phone_no for user column

Revision ID: aa4ef4821c54
Revises: 
Create Date: 2026-01-31 09:58:16.835912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa4ef4821c54'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('phone_no', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    pass

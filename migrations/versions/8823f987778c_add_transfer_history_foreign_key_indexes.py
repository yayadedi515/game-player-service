"""add transfer history foreign key indexes

Revision ID: 8823f987778c
Revises: 019dd3348d7e
Create Date: 2026-09-02 22:41:22.532577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8823f987778c'
down_revision: Union[str, Sequence[str], None] = '019dd3348d7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_transfer_history_sender_id",
        "transfer_history",
        ["sender_id"],
        unique=False
    )
    op.create_index(
        "ix_transfer_history_receiver_id",
        "transfer_history",
        ["receiver_id"],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transfer_history_receiver_id",
        table_name="transfer_history"
    )
    op.drop_index(
        "ix_transfer_history_sender_id",
        table_name="transfer_history"
    )

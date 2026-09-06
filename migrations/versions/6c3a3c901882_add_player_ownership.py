"""add player ownership

Revision ID: 6c3a3c901882
Revises: b0aae66c3618
Create Date: 2026-09-06 18:29:35.246943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c3a3c901882'
down_revision: Union[str, Sequence[str], None] = 'b0aae66c3618'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "players",
        sa.Column(
            "owner_user_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.create_foreign_key(
        "players_owner_user_id_fkey",
        "players",
        "users",
        ["owner_user_id"],
        ["user_id"],
        ondelete="RESTRICT"
    )

    op.create_unique_constraint(
        "players_owner_user_id_key",
        "players",
        ["owner_user_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "players_owner_user_id_key",
        "players",
        type_="unique"
    )

    op.drop_constraint(
        "players_owner_user_id_fkey",
        "players",
        type_="foreignkey"
    )

    op.drop_column(
        "players",
        "owner_user_id"
    )
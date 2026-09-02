"""create players and transfer history tables

Revision ID: 019dd3348d7e
Revises:
Create Date: 2026-09-02 21:23:01.343732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '019dd3348d7e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.Identity(),
            nullable=False
        ),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False
        ),
        sa.Column(
            "score",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False
        ),
        sa.CheckConstraint("score >= 0"),
        sa.PrimaryKeyConstraint("player_id"),
        sa.UniqueConstraint("name")
    )

    op.create_table(
        "transfer_history",
        sa.Column(
            "transfer_id",
            sa.Integer(),
            sa.Identity(),
            nullable=False
        ),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("receiver_id", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False
        ),
        sa.CheckConstraint("points > 0"),
        sa.CheckConstraint(
            "sender_id <> receiver_id",
            name="transfer_different_players"
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["players.player_id"],
            ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["receiver_id"],
            ["players.player_id"],
            ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("transfer_id")
    )


def downgrade() -> None:
    op.drop_table("transfer_history")
    op.drop_table("players")

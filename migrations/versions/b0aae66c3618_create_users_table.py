"""create users table

Revision ID: b0aae66c3618
Revises: 8823f987778c
Create Date: 2026-09-05 16:44:52.714659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0aae66c3618'
down_revision: Union[str, Sequence[str], None] = '8823f987778c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.Identity(),
            nullable=False
        ),
        sa.Column(
            "username",
            sa.String(length=50),
            nullable=False
        ),
        sa.Column(
            "password_hash",
            sa.Text(),
            nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("username")
    )


def downgrade() -> None:
    op.drop_table("users")
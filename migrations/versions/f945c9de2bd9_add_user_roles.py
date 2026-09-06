"""add user roles

Revision ID: f945c9de2bd9
Revises: 6c3a3c901882
Create Date: 2026-09-06 21:37:35.988827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f945c9de2bd9'
down_revision: Union[str, Sequence[str], None] = '6c3a3c901882'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="user"
        )
    )

    op.create_check_constraint(
        "users_role_check",
        "users",
        "role IN ('user', 'admin')"
    )


def downgrade() -> None:
    op.drop_constraint(
        "users_role_check",
        "users",
        type_="check"
    )

    op.drop_column(
        "users",
        "role"
    )

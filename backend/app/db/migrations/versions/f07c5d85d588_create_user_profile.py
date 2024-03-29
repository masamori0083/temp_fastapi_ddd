"""create user profile

Revision ID: f07c5d85d588
Revises: 28ade8767099
Create Date: 2024-03-27 12:16:57.561927

"""

from typing import Tuple

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f07c5d85d588"
down_revision = "28ade8767099"
branch_labels = None
depends_on = None


def create_updated_at_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )


def timestamps(indexed: bool = False) -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
    )


def create_profiles_table() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("full_name", sa.TEXT, nullable=False),
        sa.Column("phone_number", sa.TEXT, nullable=True),
        sa.Column("bio", sa.TEXT, nullable=True),
        sa.Column("image", sa.TEXT, nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        *timestamps()  # new
    )

    op.execute(
        """
        CREATE TRIGGER update_profiles_modtime
            BEFORE UPDATE
            ON profiles
            FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )


def upgrade() -> None:
    create_updated_at_trigger()
    create_profiles_table()


def downgrade() -> None:
    op.drop_table("profiles")

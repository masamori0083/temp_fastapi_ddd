"""create_first_tables

Revision ID: d146353c08c0
Revises: 
Create Date: 2024-03-20 11:56:29.354861

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d146353c08c0"
down_revision = None
branch_labels = None
depends_on = None


def create_hedgehogs_table() -> None:
    op.create_table(
        "hedgehogs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("color_type", sa.Text, nullable=False),
        sa.Column("age", sa.Numeric(10, 1), nullable=False),
    )


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

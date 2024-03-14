"""add is_read to translation table

Revision ID: 367a41c75ca2
Revises: b8c0579e739b
Create Date: 2023-12-29 19:08:05.114313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "367a41c75ca2"
down_revision: Union[str, None] = "b8c0579e739b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Step 1: Add the column as nullable
    op.add_column("translations", sa.Column("is_read", sa.Integer(), nullable=True))

    # Step 2: Update existing rows with a default value
    op.execute("UPDATE translations SET is_read = 1")

    # Step 3: Alter column to be non-nullable
    op.alter_column("translations", "is_read", nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("translations", "is_read")
    # ### end Alembic commands ###
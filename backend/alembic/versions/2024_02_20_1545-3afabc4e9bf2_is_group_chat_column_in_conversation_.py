"""is_group_chat column in Conversation table

Revision ID: 3afabc4e9bf2
Revises: 2e2526fccf6b
Create Date: 2024-02-20 15:45:17.861268

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3afabc4e9bf2"
down_revision: Union[str, None] = "2e2526fccf6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "conversations", sa.Column("is_group_chat", sa.Boolean(), nullable=True)
    )

    op.execute("UPDATE conversations SET is_group_chat = TRUE")

    op.alter_column("conversations", "is_group_chat", nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("conversations", "is_group_chat")
    # ### end Alembic commands ###
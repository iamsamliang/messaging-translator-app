"""fix ambiguous foreign keys

Revision ID: 674326c5f1ea
Revises: 3926483656d5
Create Date: 2023-12-27 16:01:43.005824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '674326c5f1ea'
down_revision: Union[str, None] = '3926483656d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

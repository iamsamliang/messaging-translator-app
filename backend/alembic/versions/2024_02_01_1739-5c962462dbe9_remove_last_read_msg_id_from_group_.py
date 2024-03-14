"""remove last_read_msg_id from group_member association

Revision ID: 5c962462dbe9
Revises: 967ba8404b77
Create Date: 2024-02-01 17:39:43.475519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c962462dbe9'
down_revision: Union[str, None] = '967ba8404b77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('group_member_last_read_message_id_fkey', 'group_member', type_='foreignkey')
    op.drop_column('group_member', 'last_read_message_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('group_member', sa.Column('last_read_message_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('group_member_last_read_message_id_fkey', 'group_member', 'messages', ['last_read_message_id'], ['id'])
    # ### end Alembic commands ###

"""changed role column to enum

Revision ID: 2b8ead36b0a0
Revises: 633183604f88
Create Date: 2026-06-05 16:11:50.078626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b8ead36b0a0'
down_revision: Union[str, Sequence[str], None] = '633183604f88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    member_role_enum = sa.Enum('owner', 'admin', 'member', name='member_role_enum')
    member_role_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column('workspace_members', 'role',
               existing_type=sa.VARCHAR(length=50),
               type_=member_role_enum,
               existing_nullable=False,
               postgresql_using='role::text::member_role_enum')


def downgrade() -> None:
    op.alter_column('workspace_members', 'role',
               existing_type=sa.Enum('owner', 'admin', 'member', name='member_role_enum'),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False,
               postgresql_using='role::text')
    sa.Enum(name='member_role_enum').drop(op.get_bind(), checkfirst=True)

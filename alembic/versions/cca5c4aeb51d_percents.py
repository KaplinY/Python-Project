"""percents

Revision ID: cca5c4aeb51d
Revises: 
Create Date: 2023-05-03 17:01:56.245066

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import relationship

# revision identifiers, used by Alembic.
revision = 'cca5c4aeb51d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('user_id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(100), unique=True),
        sa.Column('password', sa.Text),
    )
    op.create_table(
        'percents_data',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('added', sa.Float),
        sa.Column('subtracted', sa.Float),
        sa.Column('percent', sa.Float),
        sa.Column('time', sa.DateTime(timezone=True)),
        sa.Column('user_id', sa.ForeignKey("users.user_id")),
    )

def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('percents_data')

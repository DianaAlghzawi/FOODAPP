"""add uuid.py

Revision ID: 36cdfcd15269
Revises: 135abb12ecec
Create Date: 2023-07-09 05:17:19.854098

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '36cdfcd15269'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')


def downgrade():
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')

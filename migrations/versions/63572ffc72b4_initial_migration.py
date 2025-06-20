"""Initial migration

Revision ID: 63572ffc72b4
Revises: 
Create Date: 2025-06-09 20:36:28.421682

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63572ffc72b4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('people',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('expenses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('paid_by_id', sa.Integer(), nullable=False),
    sa.Column('split_method', sa.Enum('EQUAL', 'EXACT', 'PERCENTAGE', name='splitmethod'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['paid_by_id'], ['people.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('expense_splits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('expense_id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['expense_id'], ['expenses.id'], ),
    sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('expense_id', 'person_id', name='unique_expense_person_split')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('expense_splits')
    op.drop_table('expenses')
    op.drop_table('people')
    # ### end Alembic commands ###
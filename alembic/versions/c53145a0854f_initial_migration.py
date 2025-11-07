"""Initial migration

Revision ID: c53145a0854f
Revises: 
Create Date: 2025-09-19 07:52:49.871825

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c53145a0854f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ingredient_qualities table
    op.create_table('ingredient_qualities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protein', sa.String(length=100), nullable=True),
        sa.Column('fat', sa.String(length=100), nullable=True),
        sa.Column('fiber', sa.String(length=100), nullable=True),
        sa.Column('carbohydrate', sa.String(length=100), nullable=True),
        sa.Column('dirty_dozen', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingredient_qualities_id'), 'ingredient_qualities', ['id'], unique=False)
    
    # Create guaranteed_analyses table
    op.create_table('guaranteed_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protein', sa.String(length=100), nullable=True),
        sa.Column('fat', sa.String(length=100), nullable=True),
        sa.Column('fiber', sa.String(length=100), nullable=True),
        sa.Column('moisture', sa.String(length=100), nullable=True),
        sa.Column('ash', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guaranteed_analyses_id'), 'guaranteed_analyses', ['id'], unique=False)
    
    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=500), nullable=True),
        sa.Column('product_name', sa.String(length=500), nullable=False),
        sa.Column('ingredient_quality_id', sa.Integer(), nullable=True),
        sa.Column('guaranteed_analysis_id', sa.Integer(), nullable=True),
        sa.Column('flavors', sa.String(length=500), nullable=True),
        sa.Column('processing_method', sa.String(length=100), nullable=True),
        sa.Column('nutritionally_adequate', sa.String(length=100), nullable=True),
        sa.Column('ingredients', sa.Text(), nullable=True),
        sa.Column('food_storage', sa.String(length=100), nullable=True),
        sa.Column('packaging_size', sa.String(length=100), nullable=True),
        sa.Column('shelf_life', sa.Integer(), nullable=True),
        sa.Column('num_servings', sa.Text(), nullable=True),
        sa.Column('container_weight', sa.Text(), nullable=True),
        sa.Column('serving_size', sa.Text(), nullable=True),
        sa.Column('feeding_guidelines', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('product_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['guaranteed_analysis_id'], ['guaranteed_analyses.id'], ),
        sa.ForeignKeyConstraint(['ingredient_quality_id'], ['ingredient_qualities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_product_name'), 'products', ['product_name'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_products_product_name'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_guaranteed_analyses_id'), table_name='guaranteed_analyses')
    op.drop_table('guaranteed_analyses')
    op.drop_index(op.f('ix_ingredient_qualities_id'), table_name='ingredient_qualities')
    op.drop_table('ingredient_qualities')

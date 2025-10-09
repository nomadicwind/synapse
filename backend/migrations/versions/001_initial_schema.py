"""Initial schema for Synapse database

Revision ID: 001
Revises: 
Create Date: 2025-10-09 16:33:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create knowledge_items table
    op.create_table(
        'knowledge_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('processed_text_content', sa.Text(), nullable=True),
        sa.Column('processed_html_content', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('author', sa.Text(), nullable=True),
        sa.Column('published_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('status', sa.VARCHAR(30), nullable=False, server_default='pending'),
        sa.Column('source_type', sa.VARCHAR(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        # Add constraints
        sa.CheckConstraint("status IN ('pending', 'processing', 'ready_for_distillation', 'error')", name='ck_knowledge_items_status'),
        sa.CheckConstraint("source_type IN ('webpage', 'video', 'audio', 'voicememo', 'note')", name='ck_knowledge_items_source_type')
    )
    
    # Create indexes
    op.create_index('idx_knowledge_items_user_id', 'knowledge_items', ['user_id'])
    op.create_index('idx_knowledge_items_status', 'knowledge_items', ['status'])
    
    # Create image_assets table
    op.create_table(
        'image_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('knowledge_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storage_key', sa.Text(), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=True),
        sa.Column('mime_type', sa.VARCHAR(50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        # Add foreign key constraint
        sa.ForeignKeyConstraint(['knowledge_item_id'], ['knowledge_items.id'], ondelete='CASCADE')
    )
    
    # Create index for image_assets
    op.create_index('idx_image_assets_knowledge_item_id', 'image_assets', ['knowledge_item_id'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_image_assets_knowledge_item_id', table_name='image_assets')
    op.drop_index('idx_knowledge_items_status', table_name='knowledge_items')
    op.drop_index('idx_knowledge_items_user_id', table_name='knowledge_items')
    
    # Drop tables
    op.drop_table('image_assets')
    op.drop_table('knowledge_items')

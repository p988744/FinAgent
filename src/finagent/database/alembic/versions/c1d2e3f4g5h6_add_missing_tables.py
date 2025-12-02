"""Add missing tables and columns

Revision ID: c1d2e3f4g5h6
Revises: b8b4f491f6c7
Create Date: 2025-12-02 16:30:00.000000

This migration adds:
- research_sessions table
- tool_executions table
- document_pipelines table
- metadata column to history table
- missing columns to concepts table (keywords, document_count, metadata)
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: str | Sequence[str] | None = 'b8b4f491f6c7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing tables and columns."""

    # Add document_pipelines table
    op.create_table('document_pipelines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('stage', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index('ix_document_pipelines_document_id', 'document_pipelines', ['document_id'], unique=False)
    op.create_index('ix_document_pipelines_status', 'document_pipelines', ['status'], unique=False)

    # Add research_sessions table
    op.create_table('research_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Text(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('celery_task_id', sa.Text(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('current_agent', sa.Text(), nullable=True),
        sa.Column('agent_steps', sa.Text(), nullable=True),
        sa.Column('todos', sa.Text(), nullable=True),
        sa.Column('activity_log', sa.Text(), nullable=True),
        sa.Column('research_plan', sa.Text(), nullable=True),
        sa.Column('dynamic_plan', sa.Text(), nullable=True),
        sa.Column('tool_executions', sa.Text(), nullable=True),
        sa.Column('step_history', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('model_used', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('is_bookmarked', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('ix_research_sessions_session_id', 'research_sessions', ['session_id'], unique=True)
    op.create_index('ix_research_sessions_status', 'research_sessions', ['status'], unique=False)
    op.create_index('ix_research_sessions_celery_task_id', 'research_sessions', ['celery_task_id'], unique=False)
    op.create_index('ix_research_sessions_user_id', 'research_sessions', ['user_id'], unique=False)
    op.create_index('ix_research_sessions_is_bookmarked', 'research_sessions', ['is_bookmarked'], unique=False)
    op.create_index('ix_research_sessions_created_at', 'research_sessions', ['created_at'], unique=False)

    # Add tool_executions table
    op.create_table('tool_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('query_id', sa.Text(), nullable=False),
        sa.Column('tool_name', sa.Text(), nullable=False),
        sa.Column('parameters', sa.Text(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=False),
        sa.Column('sample_results', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_executions_query_id', 'tool_executions', ['query_id'], unique=False)
    op.create_index('ix_tool_executions_tool_name', 'tool_executions', ['tool_name'], unique=False)
    op.create_index('ix_tool_executions_success', 'tool_executions', ['success'], unique=False)
    op.create_index('ix_tool_executions_created_at', 'tool_executions', ['created_at'], unique=False)

    # Add missing columns to history table
    op.add_column('history', sa.Column('metadata', sa.Text(), nullable=True))

    # Add missing columns to concepts table
    op.add_column('concepts', sa.Column('keywords', sa.Text(), nullable=True))
    op.add_column('concepts', sa.Column('document_count', sa.Integer(), nullable=True, default=0))
    op.add_column('concepts', sa.Column('metadata', sa.Text(), nullable=True))

    # Add missing columns to documents table
    op.add_column('documents', sa.Column('mime_type', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('file_size', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove added tables and columns."""

    # Remove columns from documents
    op.drop_column('documents', 'file_size')
    op.drop_column('documents', 'mime_type')

    # Remove columns from concepts
    op.drop_column('concepts', 'metadata')
    op.drop_column('concepts', 'document_count')
    op.drop_column('concepts', 'keywords')

    # Remove metadata column from history
    op.drop_column('history', 'metadata')

    # Drop tool_executions table
    op.drop_index('ix_tool_executions_created_at', table_name='tool_executions')
    op.drop_index('ix_tool_executions_success', table_name='tool_executions')
    op.drop_index('ix_tool_executions_tool_name', table_name='tool_executions')
    op.drop_index('ix_tool_executions_query_id', table_name='tool_executions')
    op.drop_table('tool_executions')

    # Drop research_sessions table
    op.drop_index('ix_research_sessions_created_at', table_name='research_sessions')
    op.drop_index('ix_research_sessions_is_bookmarked', table_name='research_sessions')
    op.drop_index('ix_research_sessions_user_id', table_name='research_sessions')
    op.drop_index('ix_research_sessions_celery_task_id', table_name='research_sessions')
    op.drop_index('ix_research_sessions_status', table_name='research_sessions')
    op.drop_index('ix_research_sessions_session_id', table_name='research_sessions')
    op.drop_table('research_sessions')

    # Drop document_pipelines table
    op.drop_index('ix_document_pipelines_status', table_name='document_pipelines')
    op.drop_index('ix_document_pipelines_document_id', table_name='document_pipelines')
    op.drop_table('document_pipelines')

"""add_indexes_and_foreign_key_constraints

Revision ID: 22afc74213d0
Revises: 770066964e79
Create Date: 2026-10-30 14:48:54.833415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22afc74213d0'
down_revision: Union[str, Sequence[str], None] = '770066964e79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_activity_logs_actor_id'), 'activity_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_comments_author_id'), 'comments', ['author_id'], unique=False)
    op.drop_constraint('comments_author_id_fkey', 'comments', type_='foreignkey')
    op.create_foreign_key('comments_author_id_fkey', 'comments', 'users', ['author_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_projects_created_by'), 'projects', ['created_by'], unique=False)
    op.drop_constraint('projects_created_by_fkey', 'projects', type_='foreignkey')
    op.create_foreign_key('projects_created_by_fkey', 'projects', 'users', ['created_by'], ['id'], ondelete='RESTRICT')
    op.create_index(op.f('ix_tasks_created_by'), 'tasks', ['created_by'], unique=False)
    op.drop_constraint('tasks_created_by_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_created_by_fkey', 'tasks', 'users', ['created_by'], ['id'], ondelete='RESTRICT')
    op.create_index(op.f('ix_teams_created_by'), 'teams', ['created_by'], unique=False)
    op.drop_constraint('teams_created_by_fkey', 'teams', type_='foreignkey')
    op.create_foreign_key('teams_created_by_fkey', 'teams', 'users', ['created_by'], ['id'], ondelete='RESTRICT')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('teams_created_by_fkey', 'teams', type_='foreignkey')
    op.create_foreign_key('teams_created_by_fkey', 'teams', 'users', ['created_by'], ['id'])
    op.drop_index(op.f('ix_teams_created_by'), table_name='teams')

    op.drop_constraint('tasks_created_by_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_created_by_fkey', 'tasks', 'users', ['created_by'], ['id'])
    op.drop_index(op.f('ix_tasks_created_by'), table_name='tasks')

    op.drop_constraint('projects_created_by_fkey', 'projects', type_='foreignkey')
    op.create_foreign_key('projects_created_by_fkey', 'projects', 'users', ['created_by'], ['id'])
    op.drop_index(op.f('ix_projects_created_by'), table_name='projects')

    op.drop_constraint('comments_author_id_fkey', 'comments', type_='foreignkey')
    op.create_foreign_key('comments_author_id_fkey', 'comments', 'users', ['author_id'], ['id'])
    op.drop_index(op.f('ix_comments_author_id'), table_name='comments')

    op.drop_index(op.f('ix_activity_logs_actor_id'), table_name='activity_logs')

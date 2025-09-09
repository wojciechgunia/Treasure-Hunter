"""Initial tables

Revision ID: 3302422059bd
Revises: 
Create Date: 2025-09-03 20:24:17.398112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '3302422059bd'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.Column('createAt', sa.DateTime(), nullable=True),
    sa.Column('isBlocked', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('login')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('missions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('userId', sa.Integer(), nullable=False),
    sa.Column('createdAt', sa.DateTime(), nullable=True),
    sa.Column('lastRouteUpdate', sa.DateTime(), nullable=True),
    sa.Column('lastRunning', sa.DateTime(), nullable=True),
    sa.Column('waypointsNo', sa.Integer(), nullable=True),
    sa.Column('pointsOfInterestsNo', sa.Integer(), nullable=True),
    sa.Column('runningsNo', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['userId'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_missions_id'), 'missions', ['id'], unique=False)
    op.create_table('points_of_interests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('missionId', sa.Integer(), nullable=False),
    sa.Column('createAt', sa.DateTime(), nullable=True),
    sa.Column('lat', sa.String(), nullable=False),
    sa.Column('lon', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('pictures', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['missionId'], ['missions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_points_of_interests_id'), 'points_of_interests', ['id'], unique=False)
    op.create_table('runnings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('missionId', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('stats', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['missionId'], ['missions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_runnings_id'), 'runnings', ['id'], unique=False)
    op.create_table('waypoints',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('missionId', sa.Integer(), nullable=False),
    sa.Column('no', sa.Integer(), nullable=False),
    sa.Column('lat', sa.String(), nullable=False),
    sa.Column('lon', sa.String(), nullable=False),
    sa.Column('lastUpdate', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['missionId'], ['missions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waypoints_id'), 'waypoints', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_waypoints_id'), table_name='waypoints')
    op.drop_table('waypoints')
    op.drop_index(op.f('ix_runnings_id'), table_name='runnings')
    op.drop_table('runnings')
    op.drop_index(op.f('ix_points_of_interests_id'), table_name='points_of_interests')
    op.drop_table('points_of_interests')
    op.drop_index(op.f('ix_missions_id'), table_name='missions')
    op.drop_table('missions')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

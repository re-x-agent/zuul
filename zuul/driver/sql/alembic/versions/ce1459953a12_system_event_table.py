# Copyright 2025 Acme Gating, LLC
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""system_event_table

Revision ID: ce1459953a12
Revises: 6c1582c1d08c
Create Date: 2025-11-19 11:18:16.472373

"""

# revision identifiers, used by Alembic.
revision = 'ce1459953a12'
down_revision = '6c1582c1d08c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

SYSTEM_EVENT_TABLE = "zuul_system_event"


def upgrade(table_prefix=''):
    op.create_table(
        table_prefix + SYSTEM_EVENT_TABLE,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column('tenant', sa.String(255)),
        sa.Column('event_id', sa.String(255)),
        sa.Column("event_time", sa.DateTime),
        sa.Column("event_type", sa.String(255)),
        sa.Column("description", sa.TEXT()),
    )
    op.create_index(
        f'{table_prefix}zuul_system_event_tenant_idx',
        f'{table_prefix}zuul_system_event', ['tenant'])
    op.create_index(
        f'{table_prefix}zuul_system_event_event_id_idx',
        f'{table_prefix}zuul_system_event', ['event_id'])
    op.create_index(
        f'{table_prefix}zuul_system_event_event_time_idx',
        f'{table_prefix}zuul_system_event', ['event_time'])
    op.create_index(
        f'{table_prefix}zuul_system_event_event_type_idx',
        f'{table_prefix}zuul_system_event', ['event_type'])


def downgrade():
    raise Exception("Downgrades not supported")

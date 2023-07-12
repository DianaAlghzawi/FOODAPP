from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import (ARRAY, Column, DateTime, Integer, PrimaryKeyConstraint,
                        String, Table, UniqueConstraint, text)
from sqlalchemy.dialects.postgresql import UUID

from food.infra.db.engine import metadata

new_uuid = text('uuid_generate_v4()')
now = datetime.utcnow()
default_now = dict(default=now, server_default=sa.func.now())


food = Table(
    'food',
    metadata,
    Column('id', UUID(as_uuid=True), nullable=False, server_default=new_uuid),
    Column('name', String, nullable=False),
    Column('size', String, nullable=False),
    Column('type', String, nullable=False),
    Column('category', String, nullable=False),
    Column('price', Integer, nullable=False),
    Column('content', ARRAY(UUID), nullable=False),
    Column('prepared_time', DateTime, nullable=False),
    Column('calories', Integer, nullable=False),
    Column('created_at', DateTime, nullable=False, default=now, server_default=sa.func.now()),
    Column('updated_at', DateTime, nullable=True, onupdate=now, default=now, server_default=sa.func.now()),
    PrimaryKeyConstraint('id', name='food_pk'))

contents = Table(
    'contents',
    metadata,
    Column('id', UUID(as_uuid=True), nullable=False, server_default=new_uuid),
    Column('name', String, nullable=False),
    Column('calories', Integer, nullable=False),
    Column('count', Integer, nullable=False),
    Column('created_at', DateTime, nullable=False, default=now, server_default=sa.func.now()),
    Column('updated_at', DateTime, nullable=True, onupdate=now, default=now, server_default=sa.func.now()),
    PrimaryKeyConstraint('id', name='id_pk'),
    UniqueConstraint('name', name='name_key'),
)

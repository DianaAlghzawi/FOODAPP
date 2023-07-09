from sqlalchemy import Table, Identity, ARRAY, String, DateTime, Float, Column, text, Integer
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
from datetime import datetime
from food.infra.db.engine import metadata
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint


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
    Column('price', Float, nullable=False),
    Column('contents', ARRAY(String), nullable=False),
    Column('time_to_be_prepared', Integer, nullable=False),
    Column('calories', Integer, nullable=False),
    Column('food_number', Integer, Identity(start=100, cycle=True), nullable=False,),
    Column('created_at', DateTime, nullable=False, default=now, server_default=sa.func.now()),
    Column('updated_at', DateTime, nullable=True, onupdate=now, default=now, server_default=sa.func.now()),
    PrimaryKeyConstraint("id", name="food_pk"),
    UniqueConstraint("food_number", name="food_number_key")
)

contents = Table(
    'contents',
    metadata,
    Column('id', UUID(as_uuid=True), nullable=False, server_default=new_uuid),
    Column('food_id', UUID(as_uuid=True)),
    Column('name', String, nullable=False),
    Column('calories', Integer, nullable=False),
    Column('count', Integer, nullable=False),
    Column('created_at', DateTime, nullable=False, default=now, server_default=sa.func.now()),
    Column('updated_at', DateTime, nullable=True, onupdate=now, default=now, server_default=sa.func.now()),
    ForeignKeyConstraint(['food_id'], ['food.id'], name='contents_food_food_id_fk'),
    PrimaryKeyConstraint("id", name="id_pk"),
    UniqueConstraint('name', name='name_key'),
)

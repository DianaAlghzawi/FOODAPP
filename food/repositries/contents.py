from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from sqlalchemy.engine import Connection
from food.infra.db.schema import contents
from sqlalchemy.dialects.postgresql import insert
from food.exception import ModelNotFoundException
from typing import List
from sqlalchemy.sql.expression import UnaryExpression
from sqlalchemy.sql.selectable import Select
from typing import Optional


@dataclass
class Content:
    id: UUID
    name: str
    calories: int
    count: int
    created_at: datetime
    updated_at: datetime

    def __init__(self, id, name, calories, count, created_at, updated_at):
        self.id = id
        self.name = name
        self.calories = calories
        self.count = count
        self.created_at = created_at
        self.updated_at = updated_at


def add_sort_order_filter(query: Select, filter: UnaryExpression) -> Select:
    """ Add a sort order filter for unary expresission to order the conetnts in ascending or descinding order base on the calories. """
    return query.order_by(filter)


def apply_sort_order_filter(conn: Connection, query: Select) -> List[Content]:
    """ Apply the sort order filter and return a list of the ordered contents base on the calories. """
    return [Content(**content._asdict()) for content in conn.execute(query).fetchall()]


def get_by_id(conn: Connection, id: UUID) -> Content:
    """ Get the content item by id, Returns The content and raise if the id not found. """
    if content := conn.execute(contents.select().where(contents.c.id == id)).fetchone():
        return Content(**content._asdict())
    raise ModelNotFoundException('Contents', 'id', id)


def get_by_name(conn: Connection, name: str) -> Optional[Content | None]:
    """ Get the content item by name, Returns The content or none if the content name not exist. """
    if content := conn.execute(contents.select().where(contents.c.name == name)).fetchone():
        return Content(**content._asdict())


def get_by_name_or_raise(conn: Connection, name: str):
    """ Get the content item by name, Returns The content and raise if the name not found. """

    if content := get_by_name(conn, name):
        return content
    raise ModelNotFoundException('Contents', 'name', name)


def new(conn: Connection, name: str, count: int, calories: int) -> Content:
    """ Insert a new content item into the database and return the inserted content. """

    return Content(**(conn.execute(insert(contents).values(name=name, count=count, calories=calories)
                                   .returning(contents)).fetchone())._asdict())


def delete(conn: Connection, id: UUID) -> None:
    """ Delete content item from the database. Raises: If the content id not exist """
    if not conn.execute(contents.delete().where(contents.c.id == id)).rowcount:
        raise ModelNotFoundException('Contents', 'id', id)


def persist(conn: Connection, content: Content) -> Content:
    """ Persist a content item in the database. Returns: The persisted content object """
    return Content(**(conn.execute(insert(contents)
                                   .values(name=content.name,
                                           calories=content.calories,
                                           count=content.count).on_conflict_do_update(
        constraint='name_key',
        set_={'count': content.count,
              'updated_at': datetime.now()}).returning(contents)).fetchone())._asdict())

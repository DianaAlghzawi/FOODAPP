from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from food.exception import ModelNotFoundException
from food.infra.db.enumerations import SortOrderEnum
from food.infra.db.schema import contents


@dataclass(frozen=True)
class Content:
    id: UUID
    name: str
    calories: int
    count: int
    created_at: datetime
    updated_at: datetime

    def block_count(self, count: int) -> "Content":
        return replace(self, count=count)


def filter_by_calories(conn: Connection, order_type: SortOrderEnum) -> list[Content]:
    """ Filter and return a list of the ordered contents base on the calories. """
    match order_type:
        case order_type.ASCENDING:
            sel = contents.select().order_by(contents.c.calories.asc())
        case order_type.DESCINDING:
            sel = contents.select().order_by(contents.c.calories.desc())
    return [Content(**content._asdict()) for content in conn.execute(sel).fetchall()]


def get_by_id(conn: Connection, id: UUID) -> Content:
    """ Get the content item by id, Returns The content and raise if the id not found. """
    if content := conn.execute(contents.select().where(contents.c.id == id)).fetchone():
        return Content(**content._asdict())
    raise ModelNotFoundException('Contents', 'id', id)


def get_by_name(conn: Connection, name: str) -> Content:
    """ Get the content item by name, Returns The content or none if the content name not exist. """
    if content := conn.execute(contents.select().where(contents.c.name == name)).fetchone():
        return Content(**content._asdict())
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

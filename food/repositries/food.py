from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from sqlalchemy.engine import Connection
from food.infra.db.schema import food, contents
from food.exception import ModelNotFoundException
from sqlalchemy.dialects.postgresql import insert
# from food.repositries.contents import get_by_name as get_by_content_name
from sqlalchemy import select, func
from sqlalchemy.sql.expression import UnaryExpression
from sqlalchemy.sql.selectable import Select
from typing import List
from datetime import timedelta
from sqlalchemy import or_
from typing import Optional


@dataclass
class Food:
    id: UUID
    name: str
    size: int
    type: str
    price: float
    calories: int
    time_to_be_prepared: int
    contents: list[str]
    category: str
    food_number: int
    created_at: datetime
    updated_at: datetime


MEAL_ADDIONAL_CALORIES = 300
MEDUIM_SIZE = 2
LARGE_SIZE = 3


def add_sort_order_filter(query: Select, filter: UnaryExpression) -> Select:
    """ Add a sort order filter for unary expresission to order the food in ascending or descinding order base on the calories, price. """
    return query.order_by(filter)


def apply_sort_order_filter(conn: Connection, query: Select) -> List[Food]:
    """ Apply the sort order filter and return a list of the ordered food base on the calories, price. """
    return [Food(**food_info._asdict()) for food_info in conn.execute(query).fetchall()]


def calculate_calories(conn: Connection, food_contents: list[str], size: str, category: str) -> int:
    """ Calculate calories based on size, content, and meal type, and returns the calories value. Raise if one of the contents not exist. """

    if missing_contents := set(food_contents) - set(conn.execute(select(contents.c.name).where(contents.c.name.in_(food_contents))).scalars()):
        raise ModelNotFoundException('Food', 'contents', missing_contents)

    if contents_calories_summation := conn.execute(select(func.sum(contents.c.calories))
                                                   .where(contents.c.name.in_(food_contents))).scalar():
        calories = contents_calories_summation * MEDUIM_SIZE if size == 'MEDUIM' else contents_calories_summation * \
            LARGE_SIZE if size == 'LARGE' else contents_calories_summation
        calories = calories + MEAL_ADDIONAL_CALORIES if category == 'MEAL' else calories

        return calories


def new(conn: Connection, calories: int, category: str, name: str, size: str, type: str, price: float, food_contents: list[str],
        time_to_be_prepared: int) -> Food:
    """ Insert a new food item into the database and return the inserted food object. """

    return Food(**(conn.execute(insert(food).values(
                name=name,
                size=size,
                type=type,
                price=price,
                contents=food_contents,
                time_to_be_prepared=time_to_be_prepared,
                calories=calories,
                category=category
                ).returning(food)).fetchone()._asdict()))


def update_time_until_prepared(conn: Connection, name: Optional[str] = None, id: Optional[UUID] = None) -> None:
    """ Update a time_to_be_prepared for food items into the database by name or by id. """

    if food_info := conn.execute(select([food.c.time_to_be_prepared, food.c.created_at]).
                                 where(or_(food.c.id == id, food.c.name == name))).fetchone():
        time_until_prepared = \
            max(food_info.time_to_be_prepared - int((datetime.now() - timedelta(seconds=food_info.created_at.timestamp())).second), 0)
        conn.execute(food.update().where(or_(food.c.id == id, food.c.name == name)).values(time_to_be_prepared=time_until_prepared))
    else:
        raise (ModelNotFoundException('Food', 'name', name) if name else ModelNotFoundException('Food', 'id', id))


def get_by_name(conn: Connection, name: str) -> List[Food]:
    """ Get a list of food by the food name, and raise if food name not found"""

    if food_info := conn.execute(food.select().where(food.c.name == name)).fetchall():
        return [Food(**food_info._asdict()) for food_info in food_info]
    raise ModelNotFoundException('Food', 'name', name)


def get_by_id(conn: Connection, id: UUID) -> Food:
    """ Get the food item by id and returns The food object"""

    if food_info := conn.execute(food.select().where(food.c.id == id)).fetchone():
        return Food(**food_info._asdict())
    raise ModelNotFoundException('Food', 'id', id)


def persist(conn: Connection, name: str, size: str, type: str, price: str, calories: str, time_to_be_prepared: str,
            contents: list[str], category: str) -> Food:
    """ Persist a food item in the database. Returns: The persisted Food object """

    return Food(**(conn.execute(insert(food).values(
        name=name,
        size=size,
        type=type,
        category=category,
        price=price,
        contents=contents,
        time_to_be_prepared=time_to_be_prepared,
        calories=calories
    ).on_conflict_do_update(
        constraint='food_number_key',
        set_={
            'contents': contents,
            'updated_at': datetime.now()}
    ).returning(food)).fetchone()))


def delete(conn: Connection, id: UUID) -> None:
    """ Delete Food item from the database. Raises: If the Food id not exist """

    if not conn.execute(food.delete().where(food.c.id == id)).rowcount:
        raise ModelNotFoundException('Food', 'id', id)

from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from sqlalchemy.engine import Connection
from food.infra.db.schema import food, contents
from food.exception import ModelNotFoundException
from sqlalchemy.dialects.postgresql import insert, array
from sqlalchemy import select, func, String
from sqlalchemy.sql.selectable import Select
from typing import List
from sqlalchemy import or_
from typing import Optional
import math
from food.repositries.contents import Content
from food.infra.db.enumerations import SortOrderEnum


@dataclass
class Food:
    id: UUID
    name: str
    size: int
    type: str
    price: float
    calories: int
    prepared_time: datetime
    content: list[Content]
    category: str
    created_at: datetime
    updated_at: datetime


MEAL_ADDIONAL_CALORIES = 300
MEDUIM_SIZE = 2
LARGE_SIZE = 3


def get_contents_by_id(conn: Connection, contents_list: list[UUID]) -> list[Content]:
    """ Get contents by id from contents table base on food contents list. """
    return conn.execute(contents.select().where(contents.c.id.in_(contents_list))).fetchall()


def apply_filter(conn: Connection, query: Select) -> list[food]:
    """ Apply the sort order filter and return a list of the ordered food base on the price, calories. """
    food_result = [Food(**{**food._asdict()}) for food in conn.execute(query).fetchall()]
    for food_info in food_result:
        food_info.content = get_contents_by_id(conn, food_info.content)
    return food_result


def filter(conn: Connection, calories_order_type: SortOrderEnum, price_order_type: SortOrderEnum) -> Select:
    """ Add the sort order filter and return a select query """
    query = food.select()

    if calories_order_type:
        query = add_filter(conn, calories_order_type, query, food.c.calories)
    if price_order_type:
        query = add_filter(conn, price_order_type, query, food.c.price)

    return query


def add_filter(conn: Connection, order_type: SortOrderEnum, select_query: Select, filter: Select) -> Select:
    match order_type:
        case order_type.ASCENDING:
            select_query = select_query.order_by(filter.asc())
        case order_type.DESCINDING:
            select_query = select_query.order_by(filter.desc())

    return select_query


def convert_contents_string_list_to_uuid_list(conn: Connection, food_contents: List[str]) -> List[UUID]:
    """ Convert contents from list of string to list of uuid """
    if missing_contents := set(food_contents) - set(conn.execute(select(contents.c.name).where(contents.c.name.in_(food_contents))).scalars()):
        raise ModelNotFoundException('Food', 'contents', missing_contents)

    return conn.execute(select(contents.c.id).where(contents.c.name.in_(food_contents))).scalars().fetchall()


def calculate_calories(conn: Connection, food_contents_ids: list[UUID], size: str, category: str) -> int:
    """ Calculate calories based on size, content, and meal type, and returns the calories value. Raise if one of the contents not exist. """
    if contents_calories_summation := conn.execute(select(func.sum(contents.c.calories)).where(contents.c.id.in_(food_contents_ids))).scalar():
        calories = contents_calories_summation * MEDUIM_SIZE if size == 'MEDUIM' else contents_calories_summation * \
            LARGE_SIZE if size == 'LARGE' else contents_calories_summation
        calories = calories + MEAL_ADDIONAL_CALORIES if category == 'MEAL' else calories

        return calories


def new(conn: Connection, calories: int, category: str, name: str, size: str, type: str, price: float,
        content: List[UUID], prepared_time: datetime) -> Food:
    """ Insert a new food item into the database and return the inserted food object. """
    food_info = Food(**(conn.execute(insert(food).values(
        name=name,
        size=size,
        type=type,
        price=price,
        content=array(content),
        prepared_time=prepared_time,
        calories=calories,
        category=category
    ).returning(food)).fetchone()._asdict()))
    food_info.content = get_contents_by_id(conn, food_info.content)
    return food_info


def get_time_until_prepared(conn: Connection, name: Optional[str] = None, id: Optional[UUID] = None) -> String:
    """ Update a time_to_be_prepared for food items into the database by name or by id. """
    if food_info := conn.execute(select(food.c.prepared_time).where(or_(food.c.id == id, food.c.name == name))).fetchone():
        return str(max(math.ceil(((food_info.prepared_time - datetime.now()).total_seconds() / 60)), 0)) + ' Minutes'
    else:
        raise ModelNotFoundException('Food', 'name', name) if name else ModelNotFoundException('Food', 'id', id)


def get_by_name(conn: Connection, name: str) -> List[Food]:
    """ Get a list of food by the food name, and raise if food name not found"""
    if food_info := conn.execute(food.select().where(food.c.name == name)).fetchall():
        return [
            Food(**{**food_info_row._asdict(), 'content': get_contents_by_id(conn, food_info_row.content),
                    'prepared_time': get_time_until_prepared(conn, id=food_info_row.id)})
            for food_info_row in food_info
        ]

    raise ModelNotFoundException('Food', 'name', name)


def get_by_id(conn: Connection, id: UUID) -> Food:
    """ Get the food item by id and returns The food object"""
    if food_info := Food(**conn.execute(food.select().where(food.c.id == id)).fetchone()._asdict()):
        food_info.content = get_contents_by_id(conn, food_info.content)
        return food_info
    raise ModelNotFoundException('Food', 'id', id)


def persist(conn: Connection, name: str, size: str, type: str, price: str, calories: str, prepared_time: datetime,
            content: List[UUID], category: str) -> Food:
    """ Persist a food item in the database. Returns: The persisted Food object """
    food_info = Food(**(conn.execute(insert(food).values(
        name=name,
        size=size,
        type=type,
        category=category,
        price=price,
        content=array(content),
        prepared_time=prepared_time,
        calories=calories
    ).on_conflict_do_update(
        index_elements=['id'],
        set_={
            'content': array(content),
            'updated_at': datetime.now()}
    ).returning(food)).fetchone()))
    food_info.content = get_contents_by_id(conn, food_info.content)
    return food_info


def delete(conn: Connection, id: UUID) -> None:
    """ Delete Food item from the database. Raises: If the Food id not exist """
    if not conn.execute(food.delete().where(food.c.id == id)).rowcount:
        raise ModelNotFoundException('Food', 'id', id)

from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from sqlalchemy.engine import Connection
from food.infra.db.schema import food, contents
from food.exception import ModelNotFoundException
from sqlalchemy.dialects.postgresql import insert, array
from sqlalchemy import select, func, String
from sqlalchemy.sql.expression import UnaryExpression
from sqlalchemy.sql.selectable import Select
from typing import List
from sqlalchemy import or_, any_
from typing import Optional
import math
from food.repositries.contents import Content


@dataclass
class Food:
    id: UUID
    name: str
    size: int
    type: str
    price: float
    calories: int
    prepared_time: datetime
    content: list[UUID]
    category: str
    created_at: datetime
    updated_at: datetime

    def __init__(self, id, name, size, type, price, calories, prepared_time, content,
                 category, created_at, updated_at):
        self.id = id
        self.name = name
        self.size = size
        self.type = type
        self.price = price
        self.calories = calories
        self.prepared_time = prepared_time
        self.content = content
        self.category = category
        self.created_at = created_at
        self.updated_at = updated_at


@dataclass
class CombinedResponses:
    food: Food
    contents: List[Content]


MEAL_ADDIONAL_CALORIES = 300
MEDUIM_SIZE = 2
LARGE_SIZE = 3


def add_sort_order_filter(query: Select, filter: UnaryExpression) -> Select:
    """ Add a sort order filter for unary expresission to order the food in ascending or descinding order base on the price. """
    return query.order_by(filter)


def add_sort_order_filter_by_calories(filter: UnaryExpression) -> Select:
    """ Add a sort order filter for unary expresission to order the food in ascending or descinding order base on the calories. """
    return select([food, contents]).select_from(food.join(contents, any_(food.c.content) == contents.c.id)).order_by(filter)


def get_combined_response(conn: Connection, query: Select) -> List[CombinedResponses]:
    """ Apply the sort order filter and return a list of the ordered food with it's contents base on the calories. """

    food_dict = {}
    for row in conn.execute(query).fetchall():
        food_data = Food(
            id=row.id,
            name=row.name,
            size=row.size,
            type=row.type,
            price=row.price,
            calories=row.calories,
            prepared_time=row.prepared_time,
            content=row.content,
            category=row.category,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        content = Content(
            id=row.id_1,
            name=row.name_1,
            calories=row.calories,
            count=row.count,
            created_at=row.created_at_1,
            updated_at=row.updated_at_1)

        food_dict.setdefault(food_data.id, {"food": food_data, "contents": []})["contents"].append(content)

    return [CombinedResponses(food=food_data['food'], contents=food_data['contents']) for _, food_data in food_dict.items()]


def apply_sort_order_filter(conn: Connection, query: Select) -> List[Food]:
    """ Apply the sort order filter and return a list of the ordered food base on the price. """
    return [Food(**food_info._asdict()) for food_info in conn.execute(query).fetchall()]


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

    return Food(**(conn.execute(insert(food).values(
                name=name,
                size=size,
                type=type,
                price=price,
                content=array(content),
                prepared_time=prepared_time,
                calories=calories,
                category=category
                ).returning(food)).fetchone()._asdict()))


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
            Food(**{**food_info_row._asdict(), 'prepared_time': get_time_until_prepared(conn, id=food_info_row.id)})
            for food_info_row in food_info
        ]

    raise ModelNotFoundException('Food', 'name', name)


def get_by_id(conn: Connection, id: UUID) -> Food:
    """ Get the food item by id and returns The food object"""

    if food_info := conn.execute(food.select().where(food.c.id == id)).fetchone():
        Food(**{**food_info._asdict(), 'prepared_time': get_time_until_prepared(conn, id=food_info.id)})
        return Food(**food_info._asdict())
    raise ModelNotFoundException('Food', 'id', id)


def persist(conn: Connection, name: str, size: str, type: str, price: str, calories: str, prepared_time: datetime,
            content: List[UUID], category: str) -> Food:
    """ Persist a food item in the database. Returns: The persisted Food object """

    return Food(**(conn.execute(insert(food).values(
        name=name,
        size=size,
        type=type,
        category=category,
        price=price,
        content=array(content),
        prepared_time=prepared_time,
        calories=calories
    ).on_conflict_do_update(
        constraint='name_created_at_key',
        set_={
            'content': array(content),
            'updated_at': datetime.now()}
    ).returning(food)).fetchone()))


def delete(conn: Connection, id: UUID) -> None:
    """ Delete Food item from the database. Raises: If the Food id not exist """

    if not conn.execute(food.delete().where(food.c.id == id)).rowcount:
        raise ModelNotFoundException('Food', 'id', id)

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from food.infra.db.engine import engine
from uuid import UUID
from food.controllers.models.food import Food, PatchFood
from food.repositries import food
from typing import Optional
from sqlalchemy import select, desc
from food.infra.db.schema import food as food_schema
from food.infra.db.enumerations import SortOrderEnum

food_router = APIRouter(
    prefix='/food-type',
    tags=['Food Types']
)


@food_router.get('/{id}/')
async def get_by_id(id: UUID) -> JSONResponse:
    with engine.connect() as conn:
        food.update_time_until_prepared(conn, id=id)
        return JSONResponse(content=jsonable_encoder(food.get_by_id(conn, id)), status_code=status.HTTP_200_OK)


@food_router.get('/{name}')
async def get_by_name(name: str) -> JSONResponse:
    with engine.connect() as conn:
        food.update_time_until_prepared(conn, name=name)
        return JSONResponse(content=jsonable_encoder(food.get_by_name(conn, name)), status_code=status.HTTP_200_OK)


@food_router.get('/')
async def get_by_sort_order(calories: Optional[SortOrderEnum] = None, price: Optional[SortOrderEnum] = None) -> JSONResponse:
    query = select(food_schema)

    if calories:
        query = food.add_sort_order_filter(query, desc(food_schema.c.calories)) if calories == 'DESCINDING'\
            else food.add_sort_order_filter(query, food_schema.c.calories)

    if price:
        query = food.add_sort_order_filter(query, desc(food_schema.c.price)) if price == 'DESCINDING'\
            else food.add_sort_order_filter(query, food_schema.c.price)

    with engine.connect() as conn:
        return JSONResponse(content=jsonable_encoder(food.apply_sort_order_filter(conn, query)), status_code=status.HTTP_200_OK)


@food_router.post('/')
async def insert(food_data: Food) -> JSONResponse:
    with engine.begin() as conn:
        calories = food.calculate_calories(conn, food_data.content, food_data.size, food_data.category)
        return JSONResponse(content=jsonable_encoder(food.new(conn, calories, food_data.category, food_data.name, food_data.size, food_data.type,
                                                              food_data.price, food_data.content,
                                                              food_data.time_to_be_prepared)), status_code=status.HTTP_201_CREATED)


@food_router.patch('/{id}')
async def update(id: UUID, patch_meal: PatchFood) -> JSONResponse:
    with engine.begin() as conn:
        meal = food.get_by_id(conn, id)
        meal.contents = patch_meal.contents if patch_meal.contents else meal.contents
        return JSONResponse(content=jsonable_encoder(food.persist(conn, meal.name, meal.size, meal.type, meal.price, meal.calories,
                                                                  meal.time_to_be_prepared, meal.contents, meal.category)))


@food_router.delete('/{id}')
async def delete(id: UUID) -> Response:
    with engine.begin() as conn:
        food.delete(conn, id)
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

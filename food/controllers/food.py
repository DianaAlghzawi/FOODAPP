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


@food_router.get('/{id}')
async def get_by_id(id: UUID) -> JSONResponse:
    with engine.connect() as conn:
        food_info = food.get_by_id(conn, id)
        return JSONResponse(content=jsonable_encoder(food_info), status_code=status.HTTP_200_OK)


@food_router.get('')
async def get(name: Optional[str] = None, calories: Optional[SortOrderEnum] = None, price: Optional[SortOrderEnum] = None) -> JSONResponse:
    query = select(food_schema)

    if calories:
        query = food.add_sort_order_filter_by_calories(desc(food_schema.c.calories)) if calories == 'DESCINDING'\
            else food.add_sort_order_filter_by_calories(food_schema.c.calories)

    if price:
        query = food.add_sort_order_filter(query, desc(food_schema.c.price)) if price == 'DESCINDING'\
            else food.add_sort_order_filter(query, food_schema.c.price)

    with engine.connect() as conn:
        if name:
            food_info = food.get_by_name(conn, name)
            return JSONResponse(content=jsonable_encoder(food_info), status_code=status.HTTP_200_OK)

        if calories:
            return food.get_combined_response(conn, query)
        return JSONResponse(content=jsonable_encoder(food.apply_sort_order_filter(conn, query)), status_code=status.HTTP_200_OK)


@food_router.post('')
async def insert(food_data: Food) -> JSONResponse:
    with engine.begin() as conn:
        food_data.content = food.convert_contents_string_list_to_uuid_list(conn, food_data.content)
        calories = food.calculate_calories(conn, food_data.content, food_data.size, food_data.category)
        return JSONResponse(content=jsonable_encoder(food.new(conn, calories, food_data.category, food_data.name, food_data.size, food_data.type,
                                                              food_data.price, food_data.content,
                                                              food_data.prepared_time)), status_code=status.HTTP_201_CREATED)


@food_router.patch('/{id}')
async def update(id: UUID, patch_meal: PatchFood) -> JSONResponse:
    with engine.begin() as conn:
        food_info = food.get_by_id(conn, id)
        food_info.content = patch_meal.contents if patch_meal.contents else food_info.content
        food_info.content = food.convert_contents_string_list_to_uuid_list(conn, patch_meal.contents)
        print(food_info.name)
        print(food_info.created_at)
        return JSONResponse(content=jsonable_encoder(food.persist(conn, food_info.name, food_info.size, food_info.type, food_info.price,
                                                                  food_info.calories, food_info.prepared_time, food_info.content,
                                                                  food_info.category)))


@food_router.delete('/{id}')
async def delete(id: UUID) -> Response:
    with engine.begin() as conn:
        food.delete(conn, id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

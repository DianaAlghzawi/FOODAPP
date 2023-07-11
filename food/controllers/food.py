from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from food.infra.db.engine import engine
from uuid import UUID
from food.controllers.models.food import Food, PatchFood
from food.repositries import food
from typing import Optional
from food.infra.db.enumerations import SortOrderEnum

food_router = APIRouter(
    prefix='/food-type',
    tags=['Food Types']
)


@food_router.get('/{id}')
async def get_by_id(id: UUID) -> JSONResponse:
    with engine.connect() as conn:
        food_info = food.get_by_id(conn, id)
        food_info.prepared_time = food.get_time_until_prepared(conn, id=food_info.id)
        return JSONResponse(content=jsonable_encoder(food_info), status_code=status.HTTP_200_OK)


@food_router.get('')
async def get(name: Optional[str] = None, calories: Optional[SortOrderEnum] = None, price: Optional[SortOrderEnum] = None) -> JSONResponse:
    with engine.connect() as conn:
        if name:
            return JSONResponse(content=jsonable_encoder(food.get_by_name(conn, name)), status_code=status.HTTP_200_OK)
        return JSONResponse(content=jsonable_encoder(food.apply_filter(conn, food.filter(conn, calories, price))),
                            status_code=status.HTTP_200_OK)


@food_router.post('')
async def insert(food_data: Food) -> JSONResponse:
    with engine.begin() as conn:
        food_data.content = food.convert_contents_string_list_to_uuid_list(conn, food_data.content)
        calories = food.calculate_calories(conn, food_data.content, food_data.size, food_data.category)
        return JSONResponse(content=jsonable_encoder(food.new(conn, calories, food_data.category, food_data.name,
                                                              food_data.size, food_data.type,
                                                              food_data.price, food_data.content,
                                                              food_data.prepared_time)), status_code=status.HTTP_201_CREATED)


@food_router.patch('/{id}')
async def update(id: UUID, patch_meal: PatchFood) -> JSONResponse:
    with engine.begin() as conn:
        food_info = food.get_by_id(conn, id)
        food_info.content = patch_meal.contents if patch_meal.contents else food_info.content
        food_info.content = food.convert_contents_string_list_to_uuid_list(conn, patch_meal.contents)

        return JSONResponse(content=jsonable_encoder(food.persist(conn, food_info.name, food_info.size, food_info.type,
                                                                  food_info.price, food_info.calories,
                                                                  food_info.prepared_time, food_info.content,
                                                                  food_info.category)), status_code=status.HTTP_200_OK)


@food_router.delete('/{id}')
async def delete(id: UUID) -> Response:
    with engine.begin() as conn:
        food.delete(conn, id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

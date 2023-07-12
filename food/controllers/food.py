from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from food.controllers.models.food import Food, PatchFood
from food.infra.db.engine import engine
from food.infra.db.enumerations import SortOrderEnum
from food.repositries import food

food_router = APIRouter(
    prefix='/food-type',
    tags=['Food Types']
)


@food_router.get('/{id}')
async def get_by_id(id: UUID) -> JSONResponse:
    with engine.connect() as conn:
        return JSONResponse(content=jsonable_encoder(food.get_by_id(conn, id)), status_code=status.HTTP_200_OK)


@food_router.get('')
async def get(name: Optional[str] = None, calories: Optional[SortOrderEnum] = None, price: Optional[SortOrderEnum] = None) -> JSONResponse:
    with engine.connect() as conn:
        if name:
            return JSONResponse(content=jsonable_encoder(food.get_by_name(conn, name)), status_code=status.HTTP_200_OK)
        return JSONResponse(content=jsonable_encoder(food.apply_filter(conn, food.filter(calories, price))),
                            status_code=status.HTTP_200_OK)


@food_router.post('')
async def insert(food_data: Food) -> JSONResponse:
    with engine.begin() as conn:
        contents_uuid = food.convert_contents_string_to_uuid(conn, food_data.content)
        return JSONResponse(content=jsonable_encoder(food.new(conn, food_data.category, food_data.name,
                                                              food_data.size, food_data.type,
                                                              food_data.price, contents_uuid,
                                                              food_data.prepared_time)), status_code=status.HTTP_201_CREATED)


@food_router.patch('/{id}')
async def update(id: UUID, patch_meal: PatchFood) -> JSONResponse:
    with engine.begin() as conn:
        food_info = food.get_by_id(conn, id)
        contents_ids = food.convert_contents_string_to_uuid(conn, patch_meal.contents)
        return JSONResponse(content=jsonable_encoder(food.persist(conn, food_info, contents_ids)), status_code=status.HTTP_200_OK)


@food_router.delete('/{id}')
async def delete(id: UUID) -> Response:
    with engine.begin() as conn:
        food.delete(conn, id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from food.controllers.models.contents import Content, ContentPatch
from food.exception import ModelNotFoundException
from food.infra.db.engine import engine
from food.infra.db.enumerations import SortOrderEnum
from food.repositries import contents

contents_router = APIRouter(
    prefix='/contents',
    tags=['Contents']
)


@contents_router.get('')
async def get(name: Optional[str] = None, calories_order: Optional[SortOrderEnum] = None) -> JSONResponse:
    with engine.connect() as conn:
        if name:
            return JSONResponse(content=jsonable_encoder(contents.get_by_name(conn, name)), status_code=status.HTTP_200_OK)
        if calories_order:
            return JSONResponse(content=jsonable_encoder(contents.filter_by_calories(conn, calories_order)), status_code=status.HTTP_200_OK)


@contents_router.get('/{id}')
async def get_by_id(id: UUID) -> JSONResponse:
    with engine.connect() as conn:
        return JSONResponse(content=jsonable_encoder(contents.get_by_id(conn, id)), status_code=status.HTTP_200_OK)


@contents_router.post('')
def insert(content: Content) -> JSONResponse:
    with engine.begin() as conn:
        try:
            return JSONResponse(content=jsonable_encoder(contents.get_by_name(conn, content.name)), status_code=status.HTTP_200_OK)
        except ModelNotFoundException:
            return JSONResponse(content=jsonable_encoder(contents.new(conn, content.name, content.count, content.calories)),
                                status_code=status.HTTP_201_CREATED)


@contents_router.delete('')
def delete(id: UUID) -> Response:
    with engine.begin() as conn:
        contents.delete(conn, id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@contents_router.patch('/{id}')
def update(id: UUID, content_patch: ContentPatch) -> JSONResponse:
    with engine.begin() as conn:
        content = contents.get_by_id(conn, id)
        content.count = content_patch.count if content_patch.count else content.count
        return JSONResponse(content=jsonable_encoder(contents.persist(conn, content)), status_code=status.HTTP_200_OK)

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from food.infra.db.engine import engine
from food.controllers.models.contents import Content, ContentPatch
from food.repositries import contents
from uuid import UUID
from food.infra.db.enumerations import SortOrderEnum
from typing import Optional
from sqlalchemy import select, desc
from food.infra.db.schema import contents as contents_schema


contents_router = APIRouter(
    prefix='/contents',
    tags=['Contents']
)


@contents_router.get('')
async def get(name: Optional[str] = None, calories_order: Optional[SortOrderEnum] = None) -> JSONResponse:
    query = select(contents_schema)

    if calories_order:
        query = contents.add_sort_order_filter(query, desc(contents_schema.c.calories))\
            if calories_order == 'DESCINDING' else contents.add_sort_order_filter(query, contents_schema.c.calories)

    with engine.connect() as conn:
        if name:
            return JSONResponse(content=jsonable_encoder(contents.get_or_raise_by_name(conn, name)), status_code=status.HTTP_200_OK)

        return JSONResponse(content=jsonable_encoder(contents.apply_sort_order_filter(conn, query)), status_code=status.HTTP_200_OK)


@contents_router.get('/{id}/')
async def get_by_id(id: UUID) -> JSONResponse:
    with engine.connect() as conn:
        return JSONResponse(content=jsonable_encoder(contents.get_by_id(conn, id)), status_code=status.HTTP_200_OK)


@contents_router.post('')
def insert(content: Content) -> JSONResponse:
    with engine.begin() as conn:
        if content_info := contents.get_by_name(conn, content.name):
            return JSONResponse(content=jsonable_encoder(content_info), status_code=status.HTTP_200_OK)
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

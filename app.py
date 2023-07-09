from fastapi import FastAPI, Request, status
from food.controllers.contents import contents_router
from food.controllers.food import food_router
from food.exception import ModelNotFoundException
from fastapi.responses import JSONResponse

app = FastAPI()
app.include_router(contents_router)
app.include_router(food_router)


@app.exception_handler(ModelNotFoundException)
async def unicorn_not_found_exception_handler(request: Request, exc: ModelNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": exc.content},
    )

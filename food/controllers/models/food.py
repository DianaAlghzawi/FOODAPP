from datetime import datetime

from pydantic import BaseModel, Field

from food.infra.db.enumerations import (ContentsMealType, FoodsTypeEnum,
                                        SizeEnum)


class Food(BaseModel):
    name: FoodsTypeEnum
    size: SizeEnum
    type: str = Field(min_length=0)
    price: int = Field(gt=0)
    content: list[str] = Field(min_items=2)
    prepared_time: datetime
    category: ContentsMealType


class PatchFood(BaseModel):
    contents: list[str] = Field(min_items=2)

from pydantic import BaseModel, Field
from food.infra.db.enumerations import FoodsTypeEnum, SizeEnum, ContentsMealType


class Food(BaseModel):
    name: FoodsTypeEnum
    size: SizeEnum
    type: str = Field(min_length=0)
    price: float = Field(gt=0)
    content: list[str] = Field(min_items=2)
    time_to_be_prepared: int = Field(gt=30)
    category: ContentsMealType


class PatchFood(BaseModel):
    contents: list[str] = Field(min_items=2)

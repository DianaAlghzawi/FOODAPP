from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class Content(BaseModel):
    name: str = Field(regex=r'^[A-Z]+$', min_length=2)
    calories: int = Field(gt=0)
    count: int = Field(gt=0)
    food_id: Optional[UUID]


class ContentPatch(BaseModel):
    count: int = Field(gt=0)

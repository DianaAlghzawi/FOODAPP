from pydantic import BaseModel, Field


class Content(BaseModel):
    name: str = Field(regex=r'^[A-Z]+$', min_length=2)
    calories: int = Field(gt=0)
    count: int = Field(gt=0)


class ContentPatch(BaseModel):
    count: int = Field(gt=0)

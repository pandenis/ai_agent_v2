from typing import List

from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str


class ModelList(BaseModel):
    models: List[ModelInfo]


class ModelDetail(BaseModel):
    name: str
    modelfile: str

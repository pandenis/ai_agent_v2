from typing import List, Optional

from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str


class ModelList(BaseModel):
    models: List[ModelInfo]


class ModelDetail(BaseModel):
    name: str
    modelfile: str


class ModelfileCreate(BaseModel):
    name: str
    modelfile: str


class ModelCreateResponse(BaseModel):
    success: bool
    name: str
    output: str
    error: Optional[str] = None

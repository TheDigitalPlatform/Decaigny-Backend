from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field
from datetime import datetime

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseSchema(BaseModel):
    class Config:
        orm_mode = True
        populate_by_name = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
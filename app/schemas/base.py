from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None

def ok(data: T) -> ApiResponse[T]:
    return ApiResponse(success=True, data=data)

def fail(error: str) -> ApiResponse[None]:
    return ApiResponse(success=False, error=error)

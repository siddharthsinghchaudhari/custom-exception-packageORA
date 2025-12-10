from pydantic import BaseModel
from typing import Optional
from fastapi import status


class ErrorInfo(BaseModel):
    code: str
    category: str
    message: str
    status: int = status.HTTP_400_BAD_REQUEST


class ErrorResponse(BaseModel):
    code: str
    category: str
    message: str
    status: int

from typing import List
from pydantic import BaseModel


class LogLinesResponse(BaseModel):
    lines: List[str]
    total: int
    skip: int
    limit: int

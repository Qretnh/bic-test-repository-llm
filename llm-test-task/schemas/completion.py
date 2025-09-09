from typing import Optional

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str
    model: str
    max_tokens: Optional[int] = 512


class GenerateResponse(BaseModel):
    response: str
    tokens_used: int
    latency_seconds: float

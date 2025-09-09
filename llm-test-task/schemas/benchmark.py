from pydantic import BaseModel, Field


class BenchmarkRequest(BaseModel):
    prompt_file: str
    model: str
    runs: int = Field(5, ge=1, le=20)


class BenchmarkResult(BaseModel):
    prompt: str
    latency: float
    tokens_used: int


class BenchmarkStats(BaseModel):
    avg_latency: float
    min_latency: float
    max_latency: float
    std_dev: float
    total_tokens: int

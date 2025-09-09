import uvicorn
from fastapi import FastAPI

from api import benchmark, completion, health, models

app = FastAPI(
    title="OpenRouter API Proxy",
    description="API для работы с OpenRouter моделями",
    version="1.0.0",
)

app.include_router(models.router)
app.include_router(health.router)
app.include_router(completion.router)
app.include_router(benchmark.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

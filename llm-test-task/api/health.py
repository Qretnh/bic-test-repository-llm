from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "OpenRouter API Proxy is running"}


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }

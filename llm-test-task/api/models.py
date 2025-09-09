from fastapi import APIRouter, Depends, HTTPException

from core.logging import logger
from services.openrouter import get_models_manager

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def get_models(models_manager=Depends(get_models_manager)):
    try:
        models = models_manager.get_model_names()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching models: {e}")

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.logging import logger
from services.benchmark import (calculate_statistics, chunks,
                                run_parallel_benchmark, save_benchmark_results)
from services.openrouter import OpenRouterManager, get_models_manager

router = APIRouter()


@router.post("/benchmark")
async def run_benchmark(
    prompt_file: UploadFile = File(...),
    model: str = "deepseek/deepseek-chat-v3.1:free",
    runs: int = 5,
    manager: OpenRouterManager = Depends(get_models_manager),
):
    if not manager.check_correct_model(model):
        logger.error(f"Model '{model}' not found. Try again.")
        raise HTTPException(400, f"Model {model} not available")

    content = await prompt_file.read()
    prompts = [p.strip() for p in content.decode().splitlines() if p.strip()]

    if not prompts:
        logger.error(f"No prompts for {model}")
        raise HTTPException(400, "No valid prompts in file")

    results = await run_parallel_benchmark(prompts, model, runs)

    save_benchmark_results(results)

    return calculate_statistics(results)

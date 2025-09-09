import json
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.responses import StreamingResponse

from core.config import settings
from core.logging import logger
from schemas.completion import GenerateRequest, GenerateResponse
from services.openrouter import OpenRouterManager, get_models_manager

router = APIRouter(prefix="/generate", tags=["generate"])


async def stream_openrouter_to_client(payload: dict, headers: dict, url: str):
    """Асинхронный генератор для стриминга"""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", url, json=payload, headers=headers, timeout=30.0
        ) as response:

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break

                    try:
                        data_obj = json.loads(data)
                        if "choices" in data_obj and data_obj["choices"]:
                            delta = data_obj["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield f"data: {json.dumps({'content': delta['content']}, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        continue


@router.post("", response_model=GenerateResponse)
async def generate_text(
    request: GenerateRequest,
    stream: bool = Query(False, description="Enable streaming"),
    manager: OpenRouterManager = Depends(get_models_manager),
):
    if not manager.check_correct_model(request.model):
        logger.error(f"Model {request.model} is not valid")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {request.model} is not available. Use GET /models to see available models.",
        )

    url = settings.openrouter_api_url

    payload = {
        "model": request.model,
        "prompt": request.prompt,
        "max_tokens": request.max_tokens,
        "stream": stream,
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    logger.info(f"Generating text with model: {request.model}, stream: {stream}")

    if stream:
        try:
            return StreamingResponse(
                stream_openrouter_to_client(payload, headers, url),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        except Exception as e:
            logger.error(e)

    start_time = time.time()

    try:

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=30.0
            )
            result = response.json()
            end_time = time.time()

            generated_text = result["choices"][0]["text"]
            tokens_used = result["usage"]["total_tokens"]

            logger.info(f"Successfully generated text, tokens used: {tokens_used}")

            return GenerateResponse(
                response=generated_text,
                tokens_used=tokens_used,
                latency_seconds=end_time - start_time,
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from OpenRouter: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenRouter API error: {e.response.text}",
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

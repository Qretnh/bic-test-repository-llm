import asyncio
import csv
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from core.config import settings
from core.logging import logger


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Вычисляет статистику по результатам"""
    successful_runs = [r for r in results if r["success"]]
    latencies = [r["latency"] for r in successful_runs]

    if not latencies:
        return {"error": "No successful runs"}

    return {
        "total_runs": len(results),
        "successful_runs": len(successful_runs),
        "avg": statistics.mean(latencies),
        "min": min(latencies),
        "max": max(latencies),
        "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "total_tokens": sum(r["tokens_used"] for r in successful_runs),
    }


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def save_benchmark_results(results: List[Dict[str, Any]]):
    """Сохраняет результаты в CSV"""
    with open(
        "benchmark_results/benchmark_results.csv", "w", newline="", encoding="utf-8"
    ) as f:
        fieldnames = [
            "timestamp",
            "prompt",
            "run",
            "latency",
            "tokens_used",
            "success",
            "error",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


async def run_parallel_benchmark(
    prompts: List[str], model: str, runs: int, max_parallel_requests: int = 6
) -> List[Dict[str, Any]]:
    """Запускает все тесты параллельно"""
    tasks = []

    for prompt in prompts:
        for run_num in range(runs):
            task = run_single_test(prompt, model, run_num + 1)
            tasks.append(task)

    results = []
    semaphore = asyncio.Semaphore(max_parallel_requests)

    async def limited_task(task):
        async with semaphore:
            return await task

    for chunk in chunks(tasks, max_parallel_requests):
        chunk_results = await asyncio.gather(*[limited_task(task) for task in chunk])
        results.extend(chunk_results)

    return results


async def run_single_test(prompt: str, model: str, run_num: int) -> Dict[str, Any]:
    """Выполняет один тестовый запрос"""
    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"model": model, "prompt": prompt, "max_tokens": 512}

            headers = {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            }

            async with session.post(
                settings.openrouter_api_url, json=payload, headers=headers, timeout=30
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()

                    return {
                        "prompt": prompt,
                        "run": run_num,
                        "latency": end_time - start_time,
                        "tokens_used": result["usage"]["total_tokens"],
                        "success": True,
                        "error": None,
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    logger.error("Error in API request: ", response)
                    return {
                        "prompt": prompt,
                        "run": run_num,
                        "latency": 0,
                        "tokens_used": 0,
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat(),
                    }

    except Exception as e:
        logger.error("Exception while benchmark request: ", e)
        return {
            "prompt": prompt,
            "run": run_num,
            "latency": 0,
            "tokens_used": 0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }

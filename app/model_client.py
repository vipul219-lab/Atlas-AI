
import os 
from fastapi import HTTPException
import httpx

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama").strip().lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen3-4B")

FLUX_BASE_URL = os.getenv("FLUX_BASE_URL", "http://127.0.0.1:8010")
FLUX_MODEL = os.getenv("FLUX_MODEL", "black-forest-labs/FLUX.1-schnell")

VIDEO_BASE_URL = os.getenv("VIDEO_BASE_URL", "http://127.0.0.1:8020")
VIDEO_MODEL = os.getenv("VIDEO_MODEL", "Wan-AI/Wan2.1-T2V-1.3B")


async def ask_text_model(message: str, mode: str) -> str:
    if MODEL_PROVIDER == "ollama":
        return await ask_ollama(message, mode)
    return await ask_vllm(message, mode)


def get_system_prompt(mode: str) -> str:
    if mode == "code":
        return "You are Atlas Code. Return the code block first. Keep explanation short."
    if mode == "document":
        return "You are Atlas Document. Summarize clearly, list key points, and answer only from provided text."
    return "You are Atlas, a helpful assistant."


def clean_answer(text: str) -> str:
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    return text.strip()


async def ask_vllm(message: str, mode: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{VLLM_BASE_URL}/chat/completions",
                json={
                    "model": VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": get_system_prompt(mode)},
                        {"role": "user", "content": message},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="vLLM is not running on port 8000.",
        )
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"vLLM error: {error.response.text}",
        )

    data = response.json()
    return clean_answer(data["choices"][0]["message"]["content"])


async def ask_ollama(message: str, mode: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": "qwen3:4b",
                    "messages": [
                        {"role": "system", "content": get_system_prompt(mode)},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                    "think": False,
                },
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        )

    data = response.json()
    return clean_answer(data["message"]["content"])




async def generate_image(prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{FLUX_BASE_URL}/generate",
                json={
                    "model": FLUX_MODEL,
                    "prompt": prompt,
                },
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="FLUX image server is not running on port 8010.",
        )
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"FLUX error: {error.response.text}",
        )

    data = response.json()
    return data["image_url"]


async def generate_video(prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{VIDEO_BASE_URL}/generate",
                json={
                    "model": VIDEO_MODEL,
                    "prompt": prompt,
                },
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Video diffusion server is not running on port 8020.",
        )
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Video diffusion error: {error.response.text}",
        )

    data = response.json()
    return data["video_url"]



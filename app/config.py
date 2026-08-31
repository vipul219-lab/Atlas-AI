import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelRoute:
    mode: str
    base_url: str
    model: str
    system_prompt: str
    provider: str


VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

FLUX_BASE_URL = os.getenv("FLUX_BASE_URL", "http://127.0.0.1:8010")
FLUX_MODEL = os.getenv("FLUX_MODEL", "black-forest-labs/FLUX.1-schnell")

VIDEO_BASE_URL = os.getenv("VIDEO_BASE_URL", "http://127.0.0.1:8020")
VIDEO_MODEL = os.getenv("VIDEO_MODEL", "Wan-AI/Wan2.1-T2V-1.3B")


MODEL_ROUTES = {
    "chat": ModelRoute(
        mode="chat",
        base_url=VLLM_BASE_URL,
        model=VLLM_MODEL,
        provider="vllm",
        system_prompt="You are Atlas Chat. Be helpful and concise.",
    ),
    "code": ModelRoute(
        mode="code",
        base_url=VLLM_BASE_URL,
        model=VLLM_MODEL,
        provider="vllm",
        system_prompt="You are Atlas Code. Return code first. Keep explanation short.",
    ),
    "document": ModelRoute(
        mode="document",
        base_url=VLLM_BASE_URL,
        model=VLLM_MODEL,
        provider="vllm",
        system_prompt="You are Atlas Document. Summarize clearly and answer only from the provided text.",
    ),
    "image": ModelRoute(
        mode="image",
        base_url=FLUX_BASE_URL,
        model=FLUX_MODEL,
        provider="flux",
        system_prompt="Generate an image from the user prompt.",
    ),
    "video": ModelRoute(
        mode="video",
        base_url=VIDEO_BASE_URL,
        model=VIDEO_MODEL,
        provider="video_diffusion",
        system_prompt="Generate a video from the user prompt.",
    ),
}
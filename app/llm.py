"""Utilities for interacting with the OpenRouter-hosted LLM."""

from __future__ import annotations

import base64
import os
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from .schemas import FaceAnalysisResult

load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parent.parent / "docs" / "prompt.md"


@lru_cache
def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache
def _get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model=os.getenv("OPENROUTER_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct"),
    )


def get_chat_model() -> ChatOpenAI:
    return _get_chat_model()


def get_structured_model(output_schema: Type[BaseModel] = FaceAnalysisResult):
    return _get_chat_model().with_structured_output(output_schema)


def _encode_image(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    return {"type": "image", "base64": base64.b64encode(image_bytes).decode("utf-8"), "mime_type": mime_type}


def build_user_message(image_bytes: bytes, mime_type: str) -> List[Dict[str, Any]]:
    return [
        {"type": "text", "text": "Analyze this face image and fill every field."},
        _encode_image(image_bytes, mime_type),
    ]


def build_multistep_user_message(
    image_bytes: bytes,
    mime_type: str,
    instructions: str,
    previous_results: Optional[Dict[str, Any]] = None,
    real_age: Optional[int] = None,
) -> List[Dict[str, Any]]:
    sections: list[str] = [instructions.strip()]
    if real_age is not None:
        sections.append(f"Reported real_age: {real_age}")
    if previous_results:
        sections.append(
            "previous_results (JSON):\n```json\n"
            + json.dumps(previous_results, ensure_ascii=False)
            + "\n```"
        )
    text_block = "\n\n".join(sections)
    return [{"type": "text", "text": text_block}, _encode_image(image_bytes, mime_type)]

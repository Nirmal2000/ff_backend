#!/usr/bin/env python3
"""Simple helper script to exercise /start-task and /tasks/{task_id}."""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
from pathlib import Path
from typing import Any

import httpx


def _guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


async def _start_task(client: httpx.AsyncClient, image_path: Path, real_age: int | None) -> str:
    image_bytes = image_path.read_bytes()
    files = {
        "image": (image_path.name, image_bytes, _guess_mime(image_path)),
    }
    data: dict[str, Any] = {}
    if real_age is not None:
        data["real_age"] = str(real_age)
    response = await client.post("/start-task", files=files, data=data)
    response.raise_for_status()
    return response.json()["task_id"]


async def _poll_task(client: httpx.AsyncClient, task_id: str, interval: float) -> dict[str, Any]:
    while True:
        response = await client.get(f"/tasks/{task_id}")
        response.raise_for_status()
        payload = response.json()
        status = payload["status"]
        print(f"status={status}")
        if status in {"completed", "failed"}:
            return payload
        await asyncio.sleep(interval)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test the upgraded task endpoints.")
    parser.add_argument("image", type=Path, help="Path to the selfie to upload.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI base URL.")
    parser.add_argument("--real-age", type=int, default=None, help="Optional real age to include.")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between status polls.")
    args = parser.parse_args()

    async with httpx.AsyncClient(base_url=args.base_url) as client:
        task_id = await _start_task(client, args.image, args.real_age)
        print(f"task_id={task_id}")
        final_payload = await _poll_task(client, task_id, args.interval)

    print("--- final response ---")
    print(json.dumps(final_payload, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

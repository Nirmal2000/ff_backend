"""Send the sample image to the FastAPI analyzer endpoint."""

from __future__ import annotations

from pathlib import Path

import requests

API_URL = "http://localhost:8000/analyze"


def main() -> None:
    image_path = Path(__file__).resolve().parent / "face.png"
    with image_path.open("rb") as image_file:
        files = {"image": ("face.png", image_file, "image/png")}
        response = requests.post(
            API_URL,
            headers={"Accept": "application/json"},
            files=files,
            timeout=60,
        )
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()

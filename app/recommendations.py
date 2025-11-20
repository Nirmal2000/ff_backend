"""Utilities for generating skincare recommendations."""

from __future__ import annotations

import difflib
from typing import Any, Dict

from .llm import get_structured_model
from .prompts import build_routine_prompt_messages, product_links
from .schemas import RoutineIntake, RoutinePlan
from .storage import TaskRepository


def find_product_url(product_name: str) -> str:
    """Find the best matching product URL using edit distance."""
    if product_name in product_links:
        return product_links[product_name]

    # Find closest match using edit distance
    closest_match = difflib.get_close_matches(
        product_name,
        product_links.keys(),
        n=1,
        cutoff=0.6
    )

    if closest_match:
        return product_links[closest_match[0]]

    # If no good match found, return empty string
    return ""


def add_urls_to_routine(routine_json: Dict[str, Any]) -> Dict[str, Any]:
    """Add URLs to products in routine using edit distance matching."""
    routine = routine_json.get("routine", {})

    for section_name in ["am", "pm", "midday"]:
        section = routine.get(section_name, [])
        if not section:
            continue

        for step in section:
            products = step.get("products", [])
            for product in products:
                product_name = product.get("name", "")
                if product_name:
                    url = find_product_url(product_name)
                    product["url"] = url

    return routine_json


async def generate_routine_plan(
    task_id: str,
    analysis: Dict[str, Any],
    intake: RoutineIntake,
    repository: TaskRepository,
) -> None:
    print(f"[generate_routine_plan] task_id={task_id} starting")
    intake_payload = intake.model_dump()
    messages = build_routine_prompt_messages(analysis or {}, intake_payload)
    model = get_structured_model(RoutinePlan)

    try:
        routine_plan = await model.ainvoke(messages)
    except Exception as exc:  # noqa: BLE001
        print(f"[generate_routine_plan] task_id={task_id} ERROR: {type(exc).__name__}: {exc}")
        await repository.update_task(task_id, error_value=str(exc))
        return

    try:
        # Add URLs to products using edit distance matching
        routine_json_with_urls = add_urls_to_routine(routine_plan.model_dump())

        await repository.save_routine_plan(
            task_id,
            intake=intake_payload,
            routine_json=routine_json_with_urls,
        )
        print(f"[generate_routine_plan] task_id={task_id} saved routine with URLs")
    except Exception as exc:  # noqa: BLE001
        print(f"[generate_routine_plan] task_id={task_id} ERROR saving routine: {exc}")
        await repository.update_task(task_id, error_value=str(exc))

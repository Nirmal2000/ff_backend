"""Application routes."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from .auth import AuthenticatedUser, require_supabase_user
from .llm import build_user_message, get_structured_model, load_prompt
from .recommendations import generate_routine_plan
from .schemas import (
    FaceAnalysisResult,
    RecommendationRequest,
    RecommendationResponse,
    TaskCreatedResponse,
    TaskStatusResponse,
)
from .storage import TaskRepository, get_task_repository
from .workflow import run_upgraded_workflow

router = APIRouter()


@router.get("/", tags=["root"])
async def read_root() -> dict[str, str]:
    return {"message": "FastAPI is running"}


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze", response_model=FaceAnalysisResult, tags=["analysis"])
async def analyze_face(image: UploadFile = File(...)) -> FaceAnalysisResult:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Provide a valid image file.")

    payload = [
        {"role": "system", "content": load_prompt()},
        {"role": "user", "content": build_user_message(await image.read(), image.content_type)},
    ]
    structured_model = get_structured_model()
    result = await structured_model.ainvoke(payload)
    print(result)
    return result


async def _process_task(
    task_id: str,
    image_bytes: bytes,
    mime_type: str,
    real_age: int | None,
    repository: TaskRepository,
) -> None:
    print(f"[_process_task] Starting task_id={task_id}, mime_type={mime_type}, real_age={real_age}, image_size={len(image_bytes)} bytes")

    progress_tasks: set[asyncio.Task[Any]] = set()

    async def _set_progress(status: str, snapshot: Dict[str, Any]) -> None:
        print(f"[_process_task] task_id={task_id} Progress update: status={status}")
        await repository.update_task(task_id, status_value=status, result_value=snapshot)

    def _progress(status: str, snapshot: Dict[str, Any]) -> None:
        task = asyncio.create_task(_set_progress(status, snapshot))
        progress_tasks.add(task)

        def _cleanup(t: asyncio.Task[Any]) -> None:
            progress_tasks.discard(t)
            if t.exception():  # noqa: PERF203 - logs help debugging
                print(f"[_process_task] task_id={task_id} Progress task error: {t.exception()}")

        task.add_done_callback(_cleanup)

    print(f"[_process_task] task_id={task_id} Setting status to 'processing'")
    await repository.update_task(task_id, status_value="processing")
    try:
        print(f"[_process_task] task_id={task_id} Running upgraded workflow")
        final = await run_upgraded_workflow(
            image_bytes,
            mime_type,
            real_age=real_age,
            progress_callback=_progress,
        )
        print(f"[_process_task] task_id={task_id} Workflow completed successfully")
    except Exception as exc:  # noqa: BLE001
        print(f"[_process_task] task_id={task_id} ERROR: {type(exc).__name__}: {str(exc)}")
        await repository.update_task(task_id, status_value="failed", error_value=str(exc))
        return

    if progress_tasks:
        print(f"[_process_task] task_id={task_id} Waiting for {len(progress_tasks)} progress tasks to finish")
        await asyncio.gather(*progress_tasks, return_exceptions=True)

    print(f"[_process_task] task_id={task_id} Saving final result to database")
    await repository.update_task(task_id, status_value="completed", result_value=final.model_dump(), error_value=None)
    print(f"[_process_task] task_id={task_id} Task completed and saved")


@router.post("/start-task", response_model=TaskCreatedResponse, tags=["analysis"])
async def start_task(
    image: UploadFile = File(...),
    real_age: int | None = Form(None),
    current_user: AuthenticatedUser = Depends(require_supabase_user),
    repository: TaskRepository = Depends(get_task_repository),
) -> TaskCreatedResponse:
    print(f"[/start-task] Received request from user_id={current_user.id}, real_age={real_age}, image_type={image.content_type}")

    if not image.content_type or not image.content_type.startswith("image/"):
        print(f"[/start-task] ERROR: Invalid image type: {image.content_type}")
        raise HTTPException(status_code=400, detail="Provide a valid image file.")

    image_bytes = await image.read()
    print(f"[/start-task] Image read: {len(image_bytes)} bytes")

    task_record = await repository.create_task(user_id=current_user.id, real_age=real_age)
    print(f"[/start-task] Task created: task_id={task_record.id}")

    asyncio.create_task(_process_task(task_record.id, image_bytes, image.content_type, real_age, repository))
    print(f"[/start-task] Background processing started for task_id={task_record.id}")

    return TaskCreatedResponse(task_id=task_record.id)


@router.get("/tasks", response_model=list[TaskStatusResponse], tags=["analysis"])
async def list_tasks(
    current_user: AuthenticatedUser = Depends(require_supabase_user),
    repository: TaskRepository = Depends(get_task_repository),
    limit: int = 10,
) -> list[TaskStatusResponse]:
    tasks = await repository.list_tasks(current_user.id, limit=limit)    
    print(tasks[-1])
    return [
        TaskStatusResponse(
            task_id=task.id,
            status=task.status,
            result=task.result,
            error=task.error,
            routine_json=task.routine_json,
        )
        for task in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse, tags=["analysis"])
async def get_task(
    task_id: str,
    current_user: AuthenticatedUser = Depends(require_supabase_user),
    repository: TaskRepository = Depends(get_task_repository),
) -> TaskStatusResponse:
    task = await repository.get_task(task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    print(f"[get_task] Retrieved task_id={task.id} for user_id={current_user.id}, {task}")
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        result=task.result,
        error=task.error,
        routine_json=task.routine_json,
    )


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    status_code=202,
    tags=["recommendations"],
)
async def generate_recommendation(
    payload: RecommendationRequest,
    current_user: AuthenticatedUser = Depends(require_supabase_user),
    repository: TaskRepository = Depends(get_task_repository),
) -> RecommendationResponse:
    task = await repository.get_task(payload.task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.result is None:
        raise HTTPException(status_code=400, detail="Analysis not ready.")

    asyncio.create_task(
        generate_routine_plan(
            payload.task_id,
            task.result,
            payload.intake,
            repository,
        )
    )

    return RecommendationResponse(task_id=payload.task_id, poll_path=f"/tasks/{payload.task_id}")

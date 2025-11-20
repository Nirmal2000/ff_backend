"""Persistence helpers for skin analysis tasks."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def _get_supabase_rest_config() -> tuple[str, str]:
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase database credentials are not configured.",
        )
    return supabase_url.rstrip("/"), service_role_key


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@dataclass(slots=True)
class TaskRecord:
    id: str
    user_id: str
    status: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    intake: Optional[Dict[str, Any]] = None
    routine_json: Optional[Dict[str, Any]] = None


class TaskRepository:
    """Light-weight wrapper around Supabase's PostgREST endpoint."""

    def __init__(self, table_name: str = "skin_analysis_tasks") -> None:
        self._table_name = table_name

    def _table_url(self) -> str:
        supabase_url, _ = _get_supabase_rest_config()
        return f"{supabase_url}/rest/v1/{self._table_name}"

    def _headers(self) -> dict[str, str]:
        _, service_role_key = _get_supabase_rest_config()
        return {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def create_task(self, *, user_id: str, real_age: int | None = None) -> TaskRecord:
        payload: Dict[str, Any] = {
            "user_id": user_id,
            "status": "queued",
            "result": None,
            "error": None,
            "real_age": real_age,
            "intake": None,
            "routine_json": None,
        }
        return await self._insert(payload)

    async def update_task(
        self,
        task_id: str,
        *,
        status_value: str | None = None,
        result_value: Dict[str, Any] | None = None,
        error_value: str | None = None,
        routine_json_value: Dict[str, Any] | None = None,
    ) -> TaskRecord | None:
        data: Dict[str, Any] = {}
        if status_value is not None:
            data["status"] = status_value
        if result_value is not None:
            data["result"] = result_value
        if error_value is not None:
            data["error"] = error_value
        if routine_json_value is not None:
            data["routine_json"] = routine_json_value
        if not data:
            return None
        return await self._patch(task_id, data)

    async def get_task(self, task_id: str, *, user_id: str | None = None) -> TaskRecord | None:
        params = {"id": f"eq.{task_id}", "limit": "1"}
        if user_id is not None:
            params["user_id"] = f"eq.{user_id}"
        url = self._table_url()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=self._headers(), params=params)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise _unauthorized()
        if response.status_code >= 400:
            logger.error("Failed to fetch task %s: %s - %s", task_id, response.status_code, response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch task status.",
            )
        records = response.json()
        if not records:
            return None
        return self._from_row(records[0])

    async def list_tasks(self, user_id: str, limit: int = 10) -> list[TaskRecord]:
        params = {
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": str(limit),
        }
        url = self._table_url()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=self._headers(), params=params)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise _unauthorized()
        if response.status_code >= 400:
            logger.error("Failed to list tasks for %s: %s - %s", user_id, response.status_code, response.text)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to list tasks.")
        return [self._from_row(row) for row in response.json()]

    async def _insert(self, payload: Dict[str, Any]) -> TaskRecord:
        url = self._table_url()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
        return self._handle_mutation_response(response)

    async def _patch(self, task_id: str, payload: Dict[str, Any]) -> TaskRecord | None:
        url = f"{self._table_url()}?id=eq.{task_id}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.patch(url, headers=self._headers(), json=payload)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None
        return self._handle_mutation_response(response)

    async def save_routine_plan(self, task_id: str, *, intake: Dict[str, Any], routine_json: Dict[str, Any]) -> TaskRecord | None:
        payload: Dict[str, Any] = {
            "intake": intake,
            "routine_json": routine_json,
        }
        return await self._patch(task_id, payload)

    def _handle_mutation_response(self, response: httpx.Response) -> TaskRecord:
        if response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            payload = response.json()
            if isinstance(payload, list):
                payload = payload[0]
            return self._from_row(payload)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise _unauthorized()
        logger.error(
            "Unexpected response from Supabase when mutating %s: %s - %s",
            self._table_name,
            response.status_code,
            response.text,
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Database operation failed.")

    @staticmethod
    def _from_row(row: Dict[str, Any]) -> TaskRecord:
        return TaskRecord(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            status=row.get("status", "queued"),
            result=row.get("result"),
            error=row.get("error"),
            intake=row.get("intake"),
            routine_json=row.get("routine_json"),
        )


_repository = TaskRepository()


def get_task_repository() -> TaskRepository:
    return _repository

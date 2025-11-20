"""Supabase authentication helpers."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AuthenticatedUser:
    """Minimal representation of the Supabase user making the request."""

    id: str
    email: str | None = None
    raw: dict[str, Any] | None = None


_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def _get_supabase_config() -> tuple[str, str]:
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase authentication is not configured.",
        )
    return supabase_url.rstrip("/"), service_role_key


async def verify_supabase_token(token: str) -> AuthenticatedUser:
    """Validate a Supabase JWT and return the associated user record."""

    supabase_url, service_role_key = _get_supabase_config()
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": service_role_key,
    }
    user_endpoint = f"{supabase_url}/auth/v1/user"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(user_endpoint, headers=headers)
    except httpx.HTTPError as exc:  # pragma: no cover - network failure path
        logger.exception("Failed to contact Supabase auth endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable.",
        ) from exc

    if response.status_code == status.HTTP_200_OK:
        payload: dict[str, Any] = response.json()
        user_id = payload.get("id")
        if not user_id:
            logger.error("Supabase returned payload without user id: %s", payload)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from authentication service.",
            )
        return AuthenticatedUser(id=user_id, email=payload.get("email"), raw=payload)

    if response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
        raise _unauthorized()

    logger.error(
        "Unexpected response from Supabase auth endpoint: %s - %s",
        response.status_code,
        response.text,
    )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Failed to verify auth token.",
    )


async def require_supabase_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    """FastAPI dependency that ensures the request has a valid Supabase JWT."""

    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise _unauthorized()

    user = await verify_supabase_token(credentials.credentials)
    request.state.supabase_user = user
    request.state.user_id = user.id
    return user


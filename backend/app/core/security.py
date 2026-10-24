"""Authentication for the fraud API.

Two mechanisms, both opt-in via env vars so the project still runs
out-of-the-box in dev with no keys configured:

- API_KEY: required as `X-API-Key` on every protected route (dashboard +
  n8n use this).
- WEBHOOK_SECRET: HMAC-SHA256 signature required on the n8n ingestion
  endpoints (`X-Webhook-Signature`), so a stolen API key alone can't be
  replayed from outside the automation pipeline.

If API_KEY is unset the dependency is a no-op — this keeps `docker compose
up` and local dev friction-free while making production lockdown a single
env var away.
"""

from __future__ import annotations

import hashlib
import hmac

from fastapi import Header, HTTPException, Request, status

from ..config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency: enforce X-API-Key when API_KEY is configured."""
    if not settings.api_key:
        return  # auth disabled — dev mode
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key",
        )


async def verify_webhook_signature(
    request: Request,
    x_webhook_signature: str | None = Header(default=None),
) -> None:
    """FastAPI dependency for n8n-triggered ingestion endpoints.

    Validates an HMAC-SHA256 signature of the raw request body against
    WEBHOOK_SECRET, in addition to (not instead of) the API key. No-op when
    WEBHOOK_SECRET is unset.
    """
    if not settings.webhook_secret:
        return
    body = await request.body()
    expected = hmac.new(
        settings.webhook_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    if not x_webhook_signature or not hmac.compare_digest(x_webhook_signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Webhook-Signature",
        )

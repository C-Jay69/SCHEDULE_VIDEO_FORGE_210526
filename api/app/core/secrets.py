"""
Secrets loading abstraction.

Production deployments should never have secrets in environment variables
checked into git. This module provides a single get_secret(key) entry point
that resolves a secret from one of several backends, selected by the
SECRETS_BACKEND env var:

    SECRETS_BACKEND=env      (default)   — read from os.environ
    SECRETS_BACKEND=file                — read from files in SECRETS_DIR (Docker
                                          secrets, k8s mounted secrets)
    SECRETS_BACKEND=aws                 — read from AWS Secrets Manager

In dev, you don't need to do anything — it falls back to env. In prod,
set SECRETS_BACKEND=aws and SECRETS_MANAGER_PREFIX=videoforge/prod/.

All access is lazy + cached so a missing backend doesn't blow up at import.
"""
from __future__ import annotations

import functools
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_BACKEND_ENV = "SECRETS_BACKEND"
_BACKEND_FILE = "file"
_BACKEND_AWS = "aws"
_BACKEND_DEFAULT = "env"


def _backend() -> str:
    return os.getenv(_BACKEND_ENV, _BACKEND_DEFAULT).lower()


@functools.lru_cache(maxsize=256)
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Resolve a secret value from the configured backend.

    Args:
        key:     The secret name (for env: bare key; for file: filename minus
                 .txt; for AWS: secret name)
        default: Returned if the secret is missing in every backend.

    Returns:
        The secret string, or `default` if no backend has it.
    """
    backend = _backend()
    value: Optional[str] = None

    if backend == _BACKEND_FILE:
        value = _from_file(key)
    elif backend == _BACKEND_AWS:
        value = _from_aws(key)
    else:
        value = os.getenv(key)

    if value is None:
        value = default
        if value is None:
            logger.debug("secret %r not found in backend %r", key, backend)
    return value


def _from_file(key: str) -> Optional[str]:
    """Read a secret from a file. Used for Docker/Kubernetes secret mounts."""
    directory = os.getenv("SECRETS_DIR", "/run/secrets")
    path = os.path.join(directory, key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError as exc:
        logger.warning("failed to read secret file %s: %s", path, exc)
        return None


def _from_aws(key: str) -> Optional[str]:
    """Read a secret from AWS Secrets Manager.

    Requires `boto3` (already in api/requirements.txt) and AWS credentials
    available in the environment (IAM role, env vars, or ~/.aws/credentials).
    """
    try:
        import boto3
        from botocore.exceptions import ClientError, BotoCoreError
    except ImportError:
        logger.error("boto3 not installed; cannot use AWS secrets backend")
        return None

    prefix = os.getenv("SECRETS_MANAGER_PREFIX", "")
    region = os.getenv("AWS_REGION", "us-east-1")
    full_name = f"{prefix}{key}" if prefix else key

    try:
        client = boto3.client("secretsmanager", region_name=region)
        resp = client.get_secret_value(SecretId=full_name)
        return resp.get("SecretString")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code == "ResourceNotFoundException":
            logger.debug("AWS secret %r not found", full_name)
        else:
            logger.warning("AWS Secrets Manager error for %r: %s", full_name, exc)
        return None
    except BotoCoreError as exc:
        logger.warning("AWS boto error for %r: %s", full_name, exc)
        return None


def require_secret(key: str) -> str:
    """Like get_secret but raises if the secret is missing."""
    val = get_secret(key)
    if val is None:
        raise RuntimeError(
            f"Required secret {key!r} not found in backend {_backend()!r}. "
            "Set the env var, mount a Docker secret, or configure AWS Secrets Manager."
        )
    return val


def clear_cache() -> None:
    """Reset the LRU cache (useful in tests)."""
    get_secret.cache_clear()


# Keys we try to pull from a secrets backend on startup. Pydantic-settings
# reads these from os.environ; by populating os.environ here we let it work
# unchanged for both dev (env) and prod (AWS / file) backends.
_POPULATE_KEYS = (
    "SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PUBLISHABLE_KEY",
    "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
    "STRIPE_FREE_PRICE_ID",
    "STRIPE_SCHEDULER_PRICE_ID",
    "STRIPE_COMMITTED_PRICE_ID",
    "STRIPE_INTENSE_PRICE_ID",
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
)


def populate_environ(keys: tuple[str, ...] = _POPULATE_KEYS) -> int:
    """Read each key from the secrets backend and inject into os.environ.

    Only sets keys that are not already present in os.environ — so local
    overrides still win. Returns the number of keys injected.
    """
    backend = _backend()
    if backend == _BACKEND_DEFAULT:
        # Default (env) backend IS os.environ; no work needed.
        return 0
    injected = 0
    for key in keys:
        if key in os.environ:
            continue
        value = get_secret(key)
        if value is not None:
            os.environ[key] = value
            injected += 1
    logger.info(
        "secrets backend=%s injected=%d/%d",
        backend, injected, len(keys),
    )
    return injected
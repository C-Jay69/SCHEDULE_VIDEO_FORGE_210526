"""Tests for the secrets abstraction."""
import os
import textwrap
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_secrets_cache():
    """Clear the LRU cache between tests so backend switches take effect."""
    from app.core.secrets import clear_cache
    clear_cache()
    yield
    clear_cache()


def test_env_backend_reads_os_environ(monkeypatch):
    from app.core.secrets import get_secret
    monkeypatch.setenv("SECRETS_BACKEND", "env")
    monkeypatch.setenv("MY_SECRET_KEY", "hello-world")
    assert get_secret("MY_SECRET_KEY") == "hello-world"


def test_env_backend_returns_default_when_missing(monkeypatch):
    from app.core.secrets import get_secret
    monkeypatch.setenv("SECRETS_BACKEND", "env")
    monkeypatch.delenv("DEFINITELY_NOT_SET", raising=False)
    assert get_secret("DEFINITELY_NOT_SET", default="fallback") == "fallback"
    assert get_secret("DEFINITELY_NOT_SET") is None


def test_file_backend_reads_secret_files(monkeypatch, tmp_path: Path):
    (tmp_path / "MY_SECRET").write_text("file-content\n")
    monkeypatch.setenv("SECRETS_BACKEND", "file")
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))

    from app.core.secrets import get_secret
    assert get_secret("MY_SECRET") == "file-content"


def test_file_backend_returns_none_when_file_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SECRETS_BACKEND", "file")
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))

    from app.core.secrets import get_secret
    assert get_secret("MISSING_SECRET") is None


def test_require_secret_raises_when_missing(monkeypatch):
    from app.core import secrets
    monkeypatch.setenv("SECRETS_BACKEND", "env")
    monkeypatch.delenv("DEFINITELY_NOT_SET", raising=False)
    with pytest.raises(RuntimeError, match="DEFINITELY_NOT_SET"):
        secrets.require_secret("DEFINITELY_NOT_SET")


def test_populate_environ_noop_for_env_backend(monkeypatch):
    monkeypatch.setenv("SECRETS_BACKEND", "env")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DEFINITELY_NOT_POPULATED", "x")
    from app.core.secrets import populate_environ
    # env backend is a no-op for populate_environ
    assert populate_environ() == 0
    # existing values untouched
    assert os.environ["DEFINITELY_NOT_POPULATED"] == "x"


def test_populate_environ_injects_from_file(monkeypatch, tmp_path: Path):
    (tmp_path / "SECRET_KEY").write_text("from-file\n")
    (tmp_path / "STRIPE_SECRET_KEY").write_text("sk_test_file\n")
    (tmp_path / "DATABASE_URL").write_text("postgresql://file/db\n")
    monkeypatch.setenv("SECRETS_BACKEND", "file")
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from app.core.secrets import populate_environ
    n = populate_environ()
    assert n == 3
    assert os.environ["SECRET_KEY"] == "from-file"
    assert os.environ["STRIPE_SECRET_KEY"] == "sk_test_file"
    assert os.environ["DATABASE_URL"] == "postgresql://file/db"


def test_populate_environ_does_not_overwrite(monkeypatch, tmp_path: Path):
    """If an env var is already set, populate_environ leaves it alone."""
    (tmp_path / "SECRET_KEY").write_text("from-file\n")
    monkeypatch.setenv("SECRETS_BACKEND", "file")
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))
    monkeypatch.setenv("SECRET_KEY", "explicit-override")

    from app.core.secrets import populate_environ, clear_cache
    clear_cache()
    n = populate_environ()
    assert n == 0  # SECRET_KEY was already in environ, no injection
    assert os.environ["SECRET_KEY"] == "explicit-override"


def test_aws_backend_handles_missing_boto_gracefully(monkeypatch):
    """If boto3 isn't installed, AWS backend returns None without crashing."""
    import sys
    monkeypatch.setenv("SECRETS_BACKEND", "aws")
    # Simulate boto3 missing by replacing it with a placeholder that raises
    # ImportError if imported. We do this by hiding boto3 and botocore.
    monkeypatch.setitem(sys.modules, "boto3", None)
    monkeypatch.setitem(sys.modules, "botocore.exceptions", None)
    from app.core.secrets import get_secret
    assert get_secret("ANYTHING") is None
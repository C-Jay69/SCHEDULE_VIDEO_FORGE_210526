"""Regression tests for the portable-settings_json refactor.

The model previously used postgresql.JSONB which crashed SQLAlchemy when
running against the in-memory SQLite test DB. After this change, the full
schema should create cleanly on any backend.
"""

import uuid


def test_full_schema_creates_on_sqlite():
    """Creating every project's table on SQLite must not raise.

    This is the regression guard for the JSONB portability fix — before,
    Base.metadata.create_all() on sqlite would fail with
        Compiler <SQLiteTypeCompiler> can't render element of type JSONB
    on `settings_json`. The column is now generic JSON, so the DDL
    succeeds and the test passes.
    """
    from sqlalchemy import create_engine

    from app.models.base import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)  # must not raise
    assert engine is not None


def test_project_settings_json_round_trips():
    """Insert a project with arbitrary JSON settings and read it back."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models.base import Base
    from app.models.project import Project, ProjectStatus
    from app.models.user import User, UserRole

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    u = User(
        id=uuid.uuid4(),
        email="pj@example.com",
        password_hash="x",
        name="PJ",
        role=UserRole.user,
        is_active=True,
    )
    session.add(u)
    session.commit()

    payload = {"tone": "energetic", "duration_seconds": 60, "tags": ["fun", "shorts"]}
    p = Project(
        user_id=u.id,
        topic="Test topic",
        status=ProjectStatus.draft,
        settings_json=payload,
    )
    session.add(p)
    session.commit()
    session.refresh(p)

    assert p.settings_json == payload
    assert p.settings_json["duration_seconds"] == 60
    assert "shorts" in p.settings_json["tags"]
    session.close()
    engine.dispose()

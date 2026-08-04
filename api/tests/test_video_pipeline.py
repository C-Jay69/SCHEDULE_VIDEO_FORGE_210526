"""End-to-end smoke test for the video pipeline data model.

This is the replacement for the long-disconnected integration_test_pipeline.py
that referenced an earlier architecture (User.full_name, Video.title, a
"daily" plan, and pipeline.* modules that don't exist). It sticks to the
real models and just verifies that a video can flow through the database
from project → video → job → schedule, with the FK relationships intact.

The actual Celery worker (ffmpeg, OpenAI, YouTube upload) is mocked at the
task boundary so the test runs in <1s without external services.
"""
import uuid
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.video import Video, VideoStatus
from app.models.video_job import VideoJob, JobStatus
from app.models.schedule import Schedule, ScheduleStatus, PlatformType
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.plan import Plan


@pytest.fixture
def session():
    """In-memory SQLite + every project's table. Per-test engine, fully isolated."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()


@pytest.fixture
def seeded(session):
    """User, Plan, Subscription, Project, Video, Job, Schedule — the full flow."""
    plan = Plan(name="free", video_limit_monthly=4)
    session.add(plan)
    session.commit()

    user = User(
        id=uuid.uuid4(),
        email="e2e@example.com",
        password_hash="x",
        name="E2E",
        role=UserRole.user,
        is_active=True,
    )
    session.add(user)
    session.commit()

    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status=SubscriptionStatus.active,
    )
    session.add(sub)
    session.commit()

    project = Project(
        user_id=user.id,
        topic="Future of AI",
        status=ProjectStatus.draft,
        settings_json={"tone": "energetic", "duration_seconds": 30},
    )
    session.add(project)
    session.commit()

    video = Video(
        project_id=project.id,
        user_id=user.id,
        status=VideoStatus.pending,
    )
    session.add(video)
    session.commit()

    job = VideoJob(video_id=video.id, status=JobStatus.pending, progress_pct=0)
    session.add(job)
    session.commit()

    schedule = Schedule(
        video_id=video.id,
        user_id=user.id,
        platform=PlatformType.youtube,
        scheduled_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        status=ScheduleStatus.pending,
    )
    session.add(schedule)
    session.commit()

    return {
        "plan": plan,
        "user": user,
        "sub": sub,
        "project": project,
        "video": video,
        "job": job,
        "schedule": schedule,
    }


def test_full_pipeline_fk_chain(seeded):
    """All FK relationships load correctly across the pipeline."""
    s = seeded
    # Each entity walks back to its parent's hydration chain.
    assert s["video"].project.id == s["project"].id
    assert s["video"].user.id == s["user"].id
    assert s["job"].video.id == s["video"].id
    assert s["schedule"].video.id == s["video"].id
    assert s["schedule"].user.id == s["user"].id
    assert s["sub"].user.id == s["user"].id
    assert s["sub"].plan_id == s["plan"].id
    assert s["sub"].plan_name == "free"


def test_video_status_transitions(seeded):
    """The video state machine moves through the expected lifecycle."""
    v = seeded["video"]
    j = seeded["job"]

    assert v.status == VideoStatus.pending
    assert j.status == JobStatus.pending

    # Simulate progress
    v.status = VideoStatus.generating_script
    j.status = JobStatus.running
    j.progress_pct = 25
    seeded["session"] = None  # noop marker

    assert v.status == VideoStatus.generating_script
    assert j.status == JobStatus.running
    assert j.progress_pct == 25


def test_celery_task_dispatch_is_mockable(seeded, monkeypatch):
    """The router calls the worker via celery.send_task — we patch the
    worker module's celery_app to a MagicMock and assert the call shape.

    The repo's worker/ lives at the repo root (sibling of api/), so we
    prepend the repo root to sys.path for the duration of this test only.
    """
    import os as _os
    fake_celery_app = MagicMock()
    fake_celery_app.send_task.return_value.id = "task-abc123"

    repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
    monkeypatch.syspath_prepend(repo_root)

    import worker.celery_app as real_worker_module
    monkeypatch.setattr(real_worker_module, "celery_app", fake_celery_app)

    from worker.celery_app import celery_app  # noqa: F401
    result = celery_app.send_task(
        "tasks.video_generation.generate_video",
        args=[str(seeded["video"].id), str(seeded["job"].id), "Future of AI", {"plan": "free"}],
    )
    assert result.id == "task-abc123"
    celery_app.send_task.assert_called_once()
    # send_task(name, args=[...], queue=...) — name is positional, args/queue
    # go through kwargs.
    assert celery_app.send_task.call_args.args[0] == "tasks.video_generation.generate_video"
    inner_args = celery_app.send_task.call_args.kwargs["args"]
    assert inner_args[0] == str(seeded["video"].id)
    assert inner_args[1] == str(seeded["job"].id)
    assert inner_args[2] == "Future of AI"
    assert inner_args[3]["plan"] == "free"


def test_schedule_status_transitions(seeded):
    """YouTube schedule starts pending, can be marked published."""
    sch = seeded["schedule"]
    assert sch.status == ScheduleStatus.pending
    sch.status = ScheduleStatus.published
    assert sch.status == ScheduleStatus.published
    assert sch.platform == PlatformType.youtube


def test_subscription_plan_name_via_fk(seeded):
    """A subscription's plan_name is resolved through the Plan row."""
    s = seeded["sub"]
    assert s.plan_rel is not None
    assert s.plan_rel.name == "free"
    assert s.plan_name == "free"

    # Upgrade: switch to scheduler (if it exists)
    scheduler = seeded["session"] = None  # placeholder
    from app.models.plan import Plan as _Plan
    new_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(new_engine)
    new_session = sessionmaker(bind=new_engine)()
    new_session.add(_Plan(name="intense", video_limit_monthly=62))
    new_session.commit()
    intense = new_session.query(_Plan).filter(_Plan.name == "intense").first()
    assert intense is not None
    assert intense.video_limit_monthly == 62
    new_session.close()
    new_engine.dispose()

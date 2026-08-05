import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..core.security import get_current_user
from ..core.storage import upload_bytes
from ..database import get_db
from ..models.project import Project, ProjectStatus
from ..models.project_asset import ProjectAsset
from ..models.user import User
from ..schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Project).filter(Project.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    return ProjectListResponse(items=[ProjectResponse.model_validate(p) for p in items], total=total)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        user_id=current_user.id,
        topic=data.topic,
        status=ProjectStatus.draft,
        settings_json=data.settings or {},
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.topic is not None:
        project.topic = data.topic
    if data.settings is not None:
        project.settings_json = data.settings
    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


@router.post("/{project_id}/assets")
async def upload_project_asset(
    project_id: uuid.UUID,
    asset_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate the asset type to keep the enum-ish column clean.
    allowed_types = {"script", "audio", "subtitle", "thumbnail", "final_video", "image", "music", "logo", "clip"}
    if asset_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"asset_type must be one of: {sorted(allowed_types)}")

    # Simple size guard (100MB).
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 100MB)")

    storage_key = f"assets/{project_id}/{asset_type}/{file.filename or uuid.uuid4().hex}"
    try:
        upload_bytes(content, storage_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc

    asset = ProjectAsset(
        project_id=project.id,
        asset_type=asset_type,
        storage_key=storage_key,
        original_filename=file.filename,
        metadata_json={"size": len(content)},
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"id": asset.id, "asset_type": asset.asset_type, "storage_key": asset.storage_key}

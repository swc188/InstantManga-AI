from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...core.errors import ApiError
from ...core.response import ApiResponse
from ...core.storage import ensure_project_media
from ...database import get_db
from ...models import Character, Project, Scene, Script, Storyboard, ShotAsset, AudioAsset, Export
from ...schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_out(p: Project) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        title=p.title,
        genre=p.genre,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=ApiResponse)
def list_projects(db: Session = Depends(get_db)) -> ApiResponse:
    projects = db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
    return ApiResponse(data=[_to_out(p) for p in projects])


@router.post("", response_model=ApiResponse)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ApiResponse:
    project = Project(title=payload.title, genre=payload.genre)
    db.add(project)
    db.commit()
    db.refresh(project)
    ensure_project_media(project.id)
    return ApiResponse(data=_to_out(project))


@router.get("/{project_id}", response_model=ApiResponse)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    project = db.get(Project, project_id)
    if project is None:
        raise ApiError(status_code=404, code=404, message="项目不存在")
    return ApiResponse(data=_to_out(project))


@router.put("/{project_id}", response_model=ApiResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse:
    project = db.get(Project, project_id)
    if project is None:
        raise ApiError(status_code=404, code=404, message="项目不存在")
    for field in ("title", "genre", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return ApiResponse(data=_to_out(project))


@router.delete("/{project_id}", response_model=ApiResponse)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    project = db.get(Project, project_id)
    if project is None:
        raise ApiError(status_code=404, code=404, message="项目不存在")
    # 先删除关联的 storyboard（会级联删除 shot_assets）
    db.execute(delete(Storyboard).where(Storyboard.project_id == project_id))
    # 删除其他直接关联的项目数据
    db.execute(delete(Character).where(Character.project_id == project_id))
    db.execute(delete(Scene).where(Scene.project_id == project_id))
    db.execute(delete(Script).where(Script.project_id == project_id))
    db.execute(delete(AudioAsset).where(AudioAsset.project_id == project_id))
    db.execute(delete(Export).where(Export.project_id == project_id))
    # 删除项目本身
    db.delete(project)
    db.commit()
    return ApiResponse(message="项目已删除")

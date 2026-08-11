from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...core.errors import ApiError
from ...core.response import ApiResponse
from ...database import get_db
from ...models import Character, Scene
from ...schemas.character import CharacterCreate, CharacterOut, CharacterUpdate, SceneCreate, SceneOut, SceneUpdate
from ...services import character as character_service

router = APIRouter(prefix="/projects/{project_id}/cast", tags=["cast"])


def _get_project(db: Session, project_id: int) -> None:
    from ...models import Project
    if db.get(Project, project_id) is None:
        raise ApiError(status_code=404, code=404, message="项目不存在")


@router.get("/characters", response_model=ApiResponse)
def list_characters(project_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    characters = db.scalars(
        select(Character).where(Character.project_id == project_id).order_by(Character.created_at)
    ).all()
    return ApiResponse(data=[CharacterOut.model_validate(c).model_dump() for c in characters])


@router.post("/characters", response_model=ApiResponse)
def create_character(project_id: int, payload: CharacterCreate, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    character = Character(project_id=project_id, name=payload.name, keywords=payload.keywords)
    db.add(character)
    db.commit()
    db.refresh(character)
    return ApiResponse(data=CharacterOut.model_validate(character).model_dump())


@router.put("/characters/{character_id}", response_model=ApiResponse)
def update_character(project_id: int, character_id: int, payload: CharacterUpdate, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    character = db.get(Character, character_id)
    if character is None or character.project_id != project_id:
        raise ApiError(status_code=404, code=404, message="角色不存在")
    
    if payload.name is not None:
        character.name = payload.name
    if payload.keywords is not None:
        character.keywords = payload.keywords
    if payload.portrait_path is not None:
        character.portrait_path = payload.portrait_path
    
    db.commit()
    db.refresh(character)
    return ApiResponse(data=CharacterOut.model_validate(character).model_dump())


@router.post("/characters/{character_id}/generate-portrait", response_model=ApiResponse)
def generate_portrait(project_id: int, character_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    """生成角色定妆照"""
    _get_project(db, project_id)
    character = db.get(Character, character_id)
    if character is None or character.project_id != project_id:
        raise ApiError(status_code=404, code=404, message="角色不存在")
    
    portrait_path = character_service.generate_character_portrait(
        project_id=project_id,
        character_name=character.name,
        keywords=character.keywords,
        style=character.portrait_style or "manga",
    )
    
    character.portrait_path = portrait_path
    db.commit()
    db.refresh(character)
    
    return ApiResponse(data=CharacterOut.model_validate(character).model_dump(), message="定妆照生成成功")


@router.get("/scenes", response_model=ApiResponse)
def list_scenes(project_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    scenes = db.scalars(
        select(Scene).where(Scene.project_id == project_id).order_by(Scene.created_at)
    ).all()
    return ApiResponse(data=[SceneOut.model_validate(s).model_dump() for s in scenes])


@router.post("/scenes", response_model=ApiResponse)
def create_scene(project_id: int, payload: SceneCreate, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    scene = Scene(project_id=project_id, name=payload.name, desc_words=payload.desc_words)
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return ApiResponse(data=SceneOut.model_validate(scene).model_dump())


@router.put("/scenes/{scene_id}", response_model=ApiResponse)
def update_scene(project_id: int, scene_id: int, payload: SceneUpdate, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    scene = db.get(Scene, scene_id)
    if scene is None or scene.project_id != project_id:
        raise ApiError(status_code=404, code=404, message="场景不存在")
    
    if payload.name is not None:
        scene.name = payload.name
    if payload.desc_words is not None:
        scene.desc_words = payload.desc_words
    
    db.commit()
    db.refresh(scene)
    return ApiResponse(data=SceneOut.model_validate(scene).model_dump())


@router.delete("/scenes/{scene_id}", response_model=ApiResponse)
def delete_scene(project_id: int, scene_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    scene = db.get(Scene, scene_id)
    if scene is None or scene.project_id != project_id:
        raise ApiError(status_code=404, code=404, message="场景不存在")
    
    db.delete(scene)
    db.commit()
    return ApiResponse(message="已删除")

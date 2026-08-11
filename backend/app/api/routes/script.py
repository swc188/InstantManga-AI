from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.errors import ApiError
from ...core.response import ApiResponse
from ...database import get_db
from ...models import Character, Project, Scene, Script
from ...providers.base import ProviderError
from ...schemas.script import (
    EntityOut,
    ScriptGenerateRequest,
    ScriptOut,
    ScriptRewriteRequest,
    ScriptSaveRequest,
)
from ...services.script import (
    SYSTEM_PROMPT,
    build_generate_prompt,
    detect_awkward_sentences,
    extract_entities,
    parse_structure,
    segment_beats,
)
from ...services.providers import get_text_provider

router = APIRouter(tags=["script"])


def _get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise ApiError(status_code=404, code=404, message="项目不存在")
    return project


def _get_script(db: Session, project_id: int) -> Script | None:
    return db.scalar(
        select(Script).where(Script.project_id == project_id).order_by(Script.id.desc())
    )


def _to_out(script: Script, awkward: list[dict] | None = None) -> ScriptOut:
    return ScriptOut(
        id=script.id,
        project_id=script.project_id,
        content=script.content,
        beats=script.beats or [],
        structure=script.structure or {},
        awkward=awkward or [],
        created_at=script.created_at,
    )


@router.get("/projects/{project_id}/script", response_model=ApiResponse)
def get_script(project_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    script = _get_script(db, project_id)
    if script is None:
        raise ApiError(status_code=404, code=404, message="剧本尚未生成")
    return ApiResponse(data=_to_out(script, detect_awkward_sentences(script.content)))


@router.post("/projects/{project_id}/script/generate", response_model=ApiResponse)
def generate_script(
    project_id: int,
    payload: ScriptGenerateRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    project = _get_project(db, project_id)
    provider = get_text_provider(db)
    try:
        raw = provider.generate(
            build_generate_prompt(payload.genre, payload.theme),
            system=SYSTEM_PROMPT,
        )
    except ProviderError as exc:
        raise ApiError(status_code=502, code=502, message=str(exc)) from exc

    content, structure = parse_structure(raw)
    if len(content) < 50:
        raise ApiError(status_code=502, code=502, message="生成的剧本过短，请重试")

    beats = segment_beats(content)
    script = _get_script(db, project_id)
    if script is None:
        script = Script(project_id=project_id)
        db.add(script)
    script.content = content
    script.structure = structure
    script.beats = beats
    if project.genre is None and payload.genre:
        project.genre = payload.genre
    db.commit()
    db.refresh(script)
    return ApiResponse(data=_to_out(script, detect_awkward_sentences(content)))


@router.put("/projects/{project_id}/script", response_model=ApiResponse)
def save_script(
    project_id: int,
    payload: ScriptSaveRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    _get_project(db, project_id)
    if len(payload.content) < 50:
        raise ApiError(status_code=422, code=422, message="剧本内容过短")
    script = _get_script(db, project_id)
    if script is None:
        script = Script(project_id=project_id)
        db.add(script)
    script.content = payload.content
    script.structure = payload.structure or {}
    script.beats = payload.beats or segment_beats(payload.content)
    db.commit()
    db.refresh(script)
    return ApiResponse(data=_to_out(script))


@router.post("/projects/{project_id}/script/rewrite", response_model=ApiResponse)
def rewrite_script(
    project_id: int,
    payload: ScriptRewriteRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    script = _get_script(db, project_id)
    if script is None:
        raise ApiError(status_code=404, code=404, message="剧本尚未生成")
    provider = get_text_provider(db)
    try:
        raw = provider.rewrite(script.content, payload.instruction)
    except ProviderError as exc:
        raise ApiError(status_code=502, code=502, message=str(exc)) from exc

    content, structure = parse_structure(raw)
    script.content = content
    script.structure = structure
    script.beats = segment_beats(content)
    db.commit()
    db.refresh(script)
    return ApiResponse(data=_to_out(script, detect_awkward_sentences(content)))


@router.post("/projects/{project_id}/script/extract", response_model=ApiResponse)
def extract_entities_route(
    project_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    _get_project(db, project_id)
    script = _get_script(db, project_id)
    if script is None:
        raise ApiError(status_code=404, code=404, message="剧本尚未生成")
    provider = get_text_provider(db)
    try:
        entities = extract_entities(provider, script.content)
    except ProviderError as exc:
        raise ApiError(status_code=502, code=502, message=str(exc)) from exc

    existing_names = set(
        db.scalars(
            select(Character.name).where(Character.project_id == project_id)
        ).all()
    )
    for ch in entities["characters"]:
        name = (ch.get("name") or "").strip()
        if not name or name in existing_names:
            continue
        db.add(
            Character(
                project_id=project_id,
                name=name,
                keywords=ch.get("description") or "",
            )
        )
        existing_names.add(name)

    scene_names = set(
        db.scalars(select(Scene.name).where(Scene.project_id == project_id)).all()
    )
    for sc in entities["scenes"]:
        name = (sc.get("name") or "").strip()
        if not name or name in scene_names:
            continue
        db.add(Scene(project_id=project_id, name=name, desc_words=""))
        scene_names.add(name)

    db.commit()
    return ApiResponse(
        data=EntityOut(
            characters=entities["characters"],
            scenes=entities["scenes"],
        )
    )

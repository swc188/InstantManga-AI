from fastapi import APIRouter, Depends
from sqlalchemy import asc, delete, select
from sqlalchemy.orm import Session

from ...core.errors import ApiError
from ...core.response import ApiResponse
from ...database import get_db
from ...models import Project, Storyboard
from ...schemas.storyboard import (
    StoryboardGenerateRequest,
    StoryboardOut,
    StoryboardUpdate,
)
from ...providers.base import ProviderError
from ...services.providers import get_text_provider
from ...services.storyboard import (
    build_generate_prompt,
    check_transition_smoothness,
    rotate_camera_angle,
    rotate_shot_type,
    validate_dialogue_coverage,
)

router = APIRouter(tags=["storyboard"])


def _get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise ApiError(status_code=404, code=404, message="项目不存在")
    return project


def _get_storyboards(db: Session, project_id: int) -> list[Storyboard]:
    from sqlalchemy import asc
    return db.scalars(
        select(Storyboard).where(
            Storyboard.project_id == project_id
        ).order_by(asc(Storyboard.shot_no))
    ).all()


def _to_out(sb: Storyboard) -> StoryboardOut:
    return StoryboardOut(
        id=sb.id,
        project_id=sb.project_id,
        shot_no=sb.shot_no,
        scene_desc=sb.scene_desc,
        shot_type=sb.shot_type,
        camera_angle=sb.camera_angle,
        dialogue=sb.dialogue,
        emotion=sb.emotion,
        duration=sb.duration,
        created_at=sb.created_at,
    )


@router.get("/projects/{project_id}/storyboard", response_model=ApiResponse)
def get_storyboard(project_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    _get_project(db, project_id)
    storyboards = _get_storyboards(db, project_id)
    if not storyboards:
        return ApiResponse(data=[])
    return ApiResponse(data=[_to_out(sb) for sb in storyboards])


@router.post("/projects/{project_id}/storyboard/generate", response_model=ApiResponse)
def generate_storyboard(
    project_id: int,
    payload: StoryboardGenerateRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    project = _get_project(db, project_id)
    provider = get_text_provider(db)
    
    try:
        raw = provider.generate(
            build_generate_prompt(payload.content),
            system="你是短视频漫剧分镜师，将剧本拆解为20-30个镜头的分镜表。要求：1.每个镜头必须包含完整的画面描述、景别（特写/近景/中景/远景/全景）、拍摄角度（平视/俯拍/侧拍/仰拍/主观）、台词（必须提取剧本中的原台词，不能为空）、情绪标签（平静/紧张/愤怒/惊讶/悲伤/喜悦/恐惧/期待）、时长（1.0-3.0秒）2.每3-5个镜头切换景别或拍摄角度 3.动作场景拆分为多个连续镜头 4.相邻镜头画面要有连贯性 5.总镜头数20-30个，对应1-2分钟时长 6.剧本中的台词必须分配到对应镜头\n\n输出JSON格式：{\"storyboards\":[{\"shot_no\":1,\"scene_desc\":\"画面描述\",\"shot_type\":\"特写\",\"camera_angle\":\"平视\",\"dialogue\":\"原台词内容\",\"emotion\":\"紧张\",\"duration\":1.8}]}。只输出JSON，不要其他文字。",
        )
    except ProviderError as exc:
        raise ApiError(status_code=502, code=502, message=str(exc)) from exc

    # 解析 JSON - 尝试多种方式
    import json as _json
    import re as _re
    
    # 方法1: 直接解析
    try:
        data = _json.loads(raw)
    except _json.JSONDecodeError:
        # 方法2: 提取 JSON 对象
        match = _re.search(r'\{.*\}', raw, _re.DOTALL)
        if not match:
            raise ApiError(status_code=502, code=502, message="AI 返回内容无法解析，请重试")
        json_str = match.group(0)
        
            # 方法3: 修复常见的 JSON 错误
            try:
                # 移除尾随逗号
                json_str = _re.sub(r',\s*([}\]])', r'\1', json_str)
                # 修复未引号的键
                json_str = _re.sub(r'(\w+)\s*:', r'"\1":', json_str)
                # 修复缺少逗号的字段（如 `"value" "key"` 应为 `"value", "key"`）
                json_str = _re.sub(r'"([^"]+)"\s+"', r'"\1", "', json_str)
                # 修复缺少引号的字符串值
                json_str = _re.sub(r':\s*([^"{}\[\],\s][^,}\]]*)', r': "\1"', json_str)
                # 移除控制字符（换行、制表符等）
                json_str = _re.sub(r'[\x00-\x1f]', '', json_str)
                data = _json.loads(json_str)
            except _json.JSONDecodeError:
                pass
        
        # 方法4: 逐字符修复
        if 'data' not in locals():
            try:
                fixed = []
                in_string = False
                escape = False
                brace_count = 0
                bracket_count = 0
                
                for i, c in enumerate(json_str):
                    if escape:
                        fixed.append(c)
                        escape = False
                        continue
                    if c == '\\':
                        escape = True
                        fixed.append(c)
                        continue
                    if c == '"':
                        in_string = not in_string
                        fixed.append(c)
                        continue
                    if in_string:
                        fixed.append(c)
                        continue
                    
                    # 不在字符串内
                    if c == '{':
                        brace_count += 1
                        fixed.append(c)
                    elif c == '}':
                        brace_count -= 1
                        if fixed and fixed[-1] not in '[,{':
                            fixed.append(',')
                        fixed.append(c)
                    elif c == '[':
                        bracket_count += 1
                        fixed.append(c)
                    elif c == ']':
                        bracket_count -= 1
                        if fixed and fixed[-1] not in '[,{':
                            fixed.append(',')
                        fixed.append(c)
                    elif c == ',':
                        fixed.append(c)
                    elif c == ':':
                        fixed.append(c)
                    elif c.isspace():
                        continue
                    else:
                        # 未引用的值
                        fixed.append(f'"{c}"')
                
                json_str = ''.join(fixed)
                
                # 如果括号不匹配，尝试补全
                while brace_count > 0:
                    json_str += '}'
                    brace_count -= 1
                while bracket_count > 0:
                    json_str += ']'
                    bracket_count -= 1
                
                # 再次尝试修复尾随逗号
                json_str = _re.sub(r',\s*([}\]])', r'\1', json_str)
                data = _json.loads(json_str)
            except _json.JSONDecodeError as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to parse storyboard JSON: {e}")
                logging.getLogger(__name__).error(f"JSON string: {json_str[:1000]}...")
                raise ApiError(status_code=502, code=502, message=f"分镜解析失败: {e}")
    
    raw_shots = data.get("storyboards", [])
    if len(raw_shots) < 10:
        raise ApiError(status_code=502, code=502, message="生成的分镜过少，请重试")
    
    # 清理旧分镜
    db.execute(delete(Storyboard).where(Storyboard.project_id == project_id))
    
    # 按规则调整景别和角度
    storyboards = []
    for i, shot in enumerate(raw_shots):
        shot_no = i + 1
        # 轮换景别和角度
        shot_type = shot.get("shot_type", rotate_shot_type(i, len(raw_shots)))
        camera_angle = shot.get("camera_angle", rotate_camera_angle(i, len(raw_shots)))
        
        sb = Storyboard(
            project_id=project_id,
            shot_no=shot_no,
            scene_desc=shot.get("scene_desc", ""),
            shot_type=shot_type,
            camera_angle=camera_angle,
            dialogue=shot.get("dialogue"),
            emotion=shot.get("emotion"),
            duration=shot.get("duration", 1.8),
        )
        db.add(sb)
        storyboards.append(sb)
    
    db.commit()
    for sb in storyboards:
        db.refresh(sb)
    
    # 校验台词覆盖
    uncovered = validate_dialogue_coverage(payload.content, [_to_out(sb).model_dump() for sb in storyboards])
    
    # 检查过渡连贯性
    transitions = check_transition_smoothness([_to_out(sb).model_dump() for sb in storyboards])
    
    return ApiResponse(data={
        "storyboards": [_to_out(sb) for sb in storyboards],
        "validation": {
            "uncovered_dialogues": uncovered,
            "transition_issues": transitions,
        }
    })


@router.put("/projects/{project_id}/storyboard", response_model=ApiResponse)
def update_storyboard(
    project_id: int,
    payload: StoryboardUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse:
    _get_project(db, project_id)
    sb = db.get(Storyboard, payload.id)
    if sb is None:
        raise ApiError(status_code=404, code=404, message="分镜不存在")
    
    if payload.scene_desc is not None:
        sb.scene_desc = payload.scene_desc
    if payload.shot_type is not None:
        sb.shot_type = payload.shot_type
    if payload.camera_angle is not None:
        sb.camera_angle = payload.camera_angle
    if payload.dialogue is not None:
        sb.dialogue = payload.dialogue
    if payload.emotion is not None:
        sb.emotion = payload.emotion
    if payload.duration is not None:
        sb.duration = payload.duration
    
    db.commit()
    db.refresh(sb)
    return ApiResponse(data=_to_out(sb))


@router.post("/projects/{project_id}/storyboard/reorder", response_model=ApiResponse)
def reorder_storyboard(
    project_id: int,
    payload: dict,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """重新排序分镜并自动重排镜头号。"""
    _get_project(db, project_id)
    shot_ids = payload.get("shot_ids", [])
    
    for i, shot_id in enumerate(shot_ids):
        sb = db.get(Storyboard, shot_id)
        if sb:
            sb.shot_no = i + 1
    
    db.commit()
    storyboards = _get_storyboards(db, project_id)
    return ApiResponse(data=[_to_out(sb) for sb in storyboards])

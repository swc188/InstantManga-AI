import json
import re
from typing import Literal

ShotType = Literal["特写", "近景", "中景", "远景", "全景"]
CameraAngle = Literal["平视", "俯拍", "仰拍", "侧拍", "主观"]
Emotion = Literal["平静", "紧张", "愤怒", "惊讶", "悲伤", "喜悦", "恐惧", "期待"]

SYSTEM_PROMPT = """你是短视频漫剧分镜师，将剧本拆解为 20-30 个镜头的分镜表。

要求：
1. 每个镜头必须包含完整的：画面描述、景别、拍摄角度、台词（如有）、情绪标签、时长
2. 景别必须从以下选项中选择：特写、近景、中景、远景、全景
3. 拍摄角度必须从以下选项中选择：平视、俯拍、侧拍、仰拍、主观
4. 情绪标签必须从以下选项中选择：平静、紧张、愤怒、惊讶、悲伤、喜悦、恐惧、期待
5. 时长在 1.0-3.0 秒之间
6. 每 3-5 个镜头切换一次景别或拍摄角度，避免单调
7. 动作场景拆分为多个连续镜头（如"摔杯子"拆为"抓起杯子→砸向地面→碎片飞溅"）
8. 相邻镜头画面要有连贯性，跳跃时添加过渡镜头
9. 总镜头数控制在 20-30 个，对应 1-2 分钟时长

输出 JSON 格式：
{"storyboards":[{"shot_no":1,"scene_desc":"画面描述","shot_type":"特写","camera_angle":"平视","dialogue":"台词内容","emotion":"紧张","duration":1.8}]}"""


def build_generate_prompt(content: str) -> str:
    return f"请将以下剧本拆解为分镜表：\n\n{content}"


def detect_action_sequences(text: str) -> list[dict]:
    """识别动作序列，准备拆分多阶段镜头。"""
    actions = []
    patterns = [
        r"([一二三四五六七八九十]+个)?[^(]+?(?:摔|砸|打|踢|推|拉|抓|扔|撞|摔)",
        r"(?:猛然|突然|迅速|立刻)(?:冲|跑|逃|追|扑|闪)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].strip()
            if context:
                actions.append({"match": match.group(0), "context": context})
    return actions


def split_shot_type(shot_type: str) -> str:
    """标准化景别。"""
    mapping = {
        "特写": "特写",
        "近景": "近景",
        "中景": "中景",
        "远景": "远景",
        "全景": "全景",
    }
    for key, val in mapping.items():
        if key in shot_type:
            return val
    return "中景"


def split_camera_angle(angle: str) -> str:
    """标准化拍摄角度。"""
    mapping = {
        "平视": "平视",
        "俯视": "俯拍",
        "仰视": "仰拍",
        "侧视": "侧拍",
        "主观": "主观",
    }
    for key, val in mapping.items():
        if key in angle:
            return val
    return "平视"


def rotate_shot_type(index: int, total: int) -> ShotType:
    """轮换景别：每 3-5 个镜头切换。"""
    types: list[ShotType] = ["特写", "近景", "中景", "远景", "全景"]
    cycle = 4
    return types[(index // cycle) % len(types)]


def rotate_camera_angle(index: int, total: int) -> CameraAngle:
    """轮换拍摄角度：每 3-5 个镜头切换。"""
    angles: list[CameraAngle] = ["平视", "俯拍", "仰拍", "侧拍", "主观"]
    cycle = 5
    return angles[(index // cycle) % len(angles)]


def validate_dialogue_coverage(
    script_content: str, storyboards: list[dict]
) -> list[str]:
    """校验剧本台词是否都被分配到分镜。"""
    # 匹配多种台词格式：
    # 1. 角色名："台词" 或 角色名：台词
    # 2. 纯台词 "台词" 或 （台词）
    # 3. 带引号的台词
    dialogues = []

    # 格式1: 角色名："台词" 或 角色名：台词
    for match in re.finditer(r'[\u4e00-\u9fa5]+(?:先生|女士|少爷|小姐)?["\s]*[：:]\s*[""]?([^"""]+)[""]?', script_content):
        dialogue = match.group(1).strip().strip('"“”')
        if dialogue and len(dialogue) > 2:
            dialogues.append(dialogue)

    # 格式2: 独立台词 "台词"
    for match in re.finditer(r'[""]([^"""]{3,})[""]', script_content):
        dialogue = match.group(1).strip()
        # 避免重复添加（已在格式1中添加的）
        if dialogue not in dialogues:
            dialogues.append(dialogue)

    covered = set()
    for sb in storyboards:
        if sb.get("dialogue"):
            covered.add(sb["dialogue"].strip())

    uncovered = [d for d in dialogues if d not in covered]
    return uncovered[:5]  # 最多返回 5 条


def check_transition_smoothness(
    storyboards: list[dict], threshold: int = 3
) -> list[dict]:
    """检查相邻镜头的画面连贯性，提示需要过渡镜头的位置。"""
    issues = []
    for i in range(len(storyboards) - 1):
        current = storyboards[i]
        next_sb = storyboards[i + 1]
        
        current_desc = current.get("scene_desc", "")
        next_desc = next_sb.get("scene_desc", "")
        
        # 如果两个镜头的景别差异过大且没有过渡
        if current.get("shot_type") != next_sb.get("shot_type"):
            if abs(storyboards.index(current) - storyboards.index(next_sb)) > threshold:
                issues.append({
                    "from_shot": i + 1,
                    "to_shot": i + 2,
                    "reason": "景别变化较大，建议添加过渡镜头",
                })
    
    return issues

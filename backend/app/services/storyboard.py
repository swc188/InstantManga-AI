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
10. 剧本中的台词必须分配到对应的镜头中，台词字段不能为空

输出 JSON 格式：
{"storyboards":[{"shot_no":1,"scene_desc":"画面描述","shot_type":"特写","camera_angle":"平视","dialogue":"台词内容","emotion":"紧张","duration":1.8}]}"""


def build_generate_prompt(content: str) -> str:
    # 提取剧本中的台词
    dialogues = []

    # 方法1: 匹配英文引号内的内容
    for match in re.finditer(r'"(.+?)"', content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 1 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 方法2: 匹配中文引号内的内容
    for match in re.finditer(r'「(.+?)」', content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 1 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 方法3: 匹配引号后跟对话的形式（如：said："dialogue"）
    for match in re.finditer(r'[：:]\s*["\""](.+?)["\""]', content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 1 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 【】标注的关键台词
    for match in re.finditer(r'【([^】]+)】', content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 2 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 限制台词数量
    dialogues = dialogues[:20]

    prompt = f"请将以下剧本拆解为 20-30 个镜头的分镜表。\n\n剧本内容：\n{content}\n\n需要提取的台词（必须分配到对应镜头）：\n"
    for i, d in enumerate(dialogues, 1):
        prompt += f"{i}. {d}\n"

    return prompt


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
    # 提取剧本中的台词
    dialogues = []

    # 方法1: 匹配英文引号内的内容
    for match in re.finditer(r'"(.+?)"', script_content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 1 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 方法2: 匹配中文引号内的内容
    for match in re.finditer(r'「(.+?)」', script_content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 1 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 方法3: 匹配引号后跟对话的形式（如：said："dialogue"）
    for match in re.finditer(r'[：:]\s*["\""](.+?)["\""]', script_content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 1 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 【】标注的关键台词
    for match in re.finditer(r'【([^】]+)】', script_content):
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 2 and dialogue not in dialogues:
            dialogues.append(dialogue)

    # 限制台词数量
    dialogues = dialogues[:20]

    # 从分镜中提取台词（去掉所有前缀和格式符号）
    covered = set()
    for sb in storyboards:
        dialogue = sb.get("dialogue", "") or ""
        # 去掉角色名前缀（如"林晚："、"沈舟（低声）："）
        dialogue = re.sub(r'^[\u4e00-\u9fa5]+(?:（[^）]+）)?[：:]\s*', '', dialogue)
        # 去掉「」引号
        dialogue = dialogue.strip('「」')
        # 去掉（OS）标记
        dialogue = re.sub(r'\（OS\）', '', dialogue)
        # 去掉（内心）标记
        dialogue = re.sub(r'（内心）', '', dialogue)
        # 去掉（低语）标记
        dialogue = re.sub(r'（低语）', '', dialogue)
        # 只去掉首尾引号和空格，保留标点
        dialogue = dialogue.strip().strip('"“”\'\'')
        if dialogue:
            covered.add(dialogue)

    uncovered = []
    for d in dialogues:
        # 检查是否完全匹配或部分匹配
        found = False
        for c in covered:
            if d == c or d in c or c in d:
                found = True
                break
        if not found:
            uncovered.append(d)

    return uncovered[:10]


def check_transition_smoothness(
    storyboards: list[dict], threshold: int = 3
) -> list[dict]:
    """检查相邻镜头的画面连贯性，提示需要过渡镜头的位置。"""
    issues = []
    
    # 景别跳跃检查
    shot_type_order = {"远景": 0, "全景": 1, "中景": 2, "近景": 3, "特写": 4}
    
    for i in range(len(storyboards) - 1):
        current = storyboards[i]
        next_sb = storyboards[i + 1]
        
        current_type = current.get("shot_type", "")
        next_type = next_sb.get("shot_type", "")
        
        # 检查景别跳跃（只检测特写↔远景的直接跳跃）
        if current_type and next_type:
            current_level = shot_type_order.get(current_type, 2)
            next_level = shot_type_order.get(next_type, 2)
            jump = abs(current_level - next_level)
            
            # 只有跨越3个及以上级别才警告
            if jump >= 3:
                issues.append({
                    "from_shot": i + 1,
                    "to_shot": i + 2,
                    "reason": f"景别跳跃过大（{current_type}→{next_type}），建议添加过渡镜头",
                    "type": "shot_type_jump"
                })
        
        # 检查场景切换（只检测有明显场景变化的）
        current_desc = current.get("scene_desc", "")
        next_desc = next_sb.get("scene_desc", "")
        
        # 如果场景描述差异很大（关键词不重叠）
        if current_desc and next_desc:
            current_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', current_desc))
            next_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', next_desc))
            overlap = current_keywords & next_keywords
            
            # 如果关键词完全不重叠且有台词变化
            if len(overlap) == 0 and current.get("dialogue") and next_sb.get("dialogue"):
                issues.append({
                    "from_shot": i + 1,
                    "to_shot": i + 2,
                    "reason": "场景切换突兀，建议添加过渡镜头",
                    "type": "scene_jump"
                })
        
        # 检查情绪断层（只检测极端对立）
        current_emotion = current.get("emotion", "")
        next_emotion = next_sb.get("emotion", "")
        
        if current_emotion and next_emotion:
            # 对立情绪检查
            opposite_pairs = [
                ("平静", "愤怒"), ("平静", "恐惧"), ("喜悦", "悲伤"),
                ("紧张", "放松")
            ]
            for p1, p2 in opposite_pairs:
                if (current_emotion == p1 and next_emotion == p2) or \
                   (current_emotion == p2 and next_emotion == p1):
                    issues.append({
                        "from_shot": i + 1,
                        "to_shot": i + 2,
                        "reason": f"情绪突变（{current_emotion}→{next_emotion}），建议添加过渡镜头",
                        "type": "emotion_jump"
                    })
                    break
    
    return issues

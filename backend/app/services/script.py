import json
import re

SYSTEM_PROMPT = """你是短视频漫剧编剧，创作 1-2 分钟 AI 漫剧脚本。要求：
1. 开头 3 秒抓人，中间有冲突与反转，结尾有爽点或悬念
2. 每 15-20 秒有一个剧情或情绪转折，避免全程只有对话
3. 总字数控制在 200-300 字
4. 用【开头】【冲突】【结尾】三个标记分段输出，只输出剧本正文，不要额外说明"""

EXTRACT_SYSTEM = "你是剧本分析助手，只输出 JSON，不要多余文字。"


def build_generate_prompt(genre: str, theme: str) -> str:
    parts = [f"题材：{genre}"]
    if theme:
        parts.append(f"主题：{theme}")
    return "\n".join(parts) + "\n请写一个 1 分钟 AI 漫剧脚本。"


def parse_structure(raw: str) -> tuple[str, dict]:
    segments: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in raw.splitlines():
        m = re.match(r"^【(开头|冲突|结尾)】(.*)$", line.strip(), re.S)
        if m:
            if current is not None:
                segments[current] = "\n".join(buffer).strip()
            current = m.group(1)
            buffer = []
            rest = m.group(2).strip()
            if rest:
                buffer.append(rest)
        elif current is not None:
            buffer.append(line)
    if current is not None:
        segments[current] = "\n".join(buffer).strip()

    content = re.sub(r"【(开头|冲突|结尾)】", "", raw).strip()
    structure = {
        "opening": segments.get("开头", ""),
        "conflict": segments.get("冲突", ""),
        "ending": segments.get("结尾", ""),
    }
    return content, structure


def segment_beats(
    text: str,
    words_per_sec: float = 4.5,
    beat_seconds: int = 18,
) -> list[dict]:
    """按累计字数量化 15-20 秒节奏分段，返回时间窗与段落要点。"""
    sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])", text) if s.strip()]
    beats: list[dict] = []
    bucket: list[str] = []
    bucket_len = 0
    elapsed = 0
    for s in sentences:
        bucket.append(s)
        bucket_len += len(s)
        if bucket_len >= words_per_sec * beat_seconds:
            beats.append(
                {
                    "time": f"{elapsed}-{elapsed + beat_seconds}s",
                    "point": bucket[0][:24],
                }
            )
            elapsed += beat_seconds
            bucket = []
            bucket_len = 0
    if bucket:
        beats.append(
            {"time": f"{elapsed}-{elapsed + beat_seconds}s", "point": bucket[0][:24]}
        )
    return beats


def detect_awkward_sentences(text: str, max_len: int = 30) -> list[dict]:
    """启发式检测拗口句：超长句与词语重复。"""
    sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])", text) if s.strip()]
    results: list[dict] = []
    for s in sentences:
        issues: list[str] = []
        if len(s) > max_len:
            issues.append("句子过长（超过 30 字）")
        repeat = re.search(r"([\u4e00-\u9fa5]{2,3})\1\1", s)
        if repeat:
            issues.append(f"“{repeat.group(1)}”连续重复出现")
        if issues:
            results.append({"sentence": s, "issues": issues})
    return results


def extract_entities(provider, content: str) -> dict:
    prompt = (
        "从以下剧本中抽取所有角色（含一句形象描述）与场景，输出 JSON：\n"
        '{"characters":[{"name":"","description":""}],"scenes":[{"name":""}]}\n\n'
        f"剧本：\n{content}"
    )
    raw = provider.generate(prompt, system=EXTRACT_SYSTEM)
    match = re.search(r"\{.*\}", raw, re.S)
    try:
        data = json.loads(match.group(0)) if match else json.loads(raw)
    except json.JSONDecodeError:
        return {"characters": [], "scenes": []}
    return {
        "characters": data.get("characters", []),
        "scenes": data.get("scenes", []),
    }

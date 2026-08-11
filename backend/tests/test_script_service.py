from app.services.script import (
    build_generate_prompt,
    detect_awkward_sentences,
    extract_entities,
    parse_structure,
    segment_beats,
)


def test_build_generate_prompt_includes_genre_and_theme():
    prompt = build_generate_prompt("霸总", "逆袭")
    assert "霸总" in prompt
    assert "逆袭" in prompt


def test_parse_structure_extracts_three_segments():
    raw = "【开头】她带着秘密归来。\n【冲突】他却已订婚。\n【结尾】她笑着转身离开。"
    content, structure = parse_structure(raw)
    assert structure["opening"] == "她带着秘密归来。"
    assert structure["conflict"] == "他却已订婚。"
    assert structure["ending"] == "她笑着转身离开。"
    assert "【" not in content
    assert content == "她带着秘密归来。\n他却已订婚。\n她笑着转身离开。"


def test_parse_structure_without_marks_falls_back_empty():
    content, structure = parse_structure("只有一段话。")
    assert structure["opening"] == ""
    assert content == "只有一段话。"


def test_segment_beats_creates_time_windows():
    text = "".join(f"这是第{i}句台词，讲述故事的发展与转折。" for i in range(10))
    beats = segment_beats(text, words_per_sec=4.5, beat_seconds=18)
    assert len(beats) >= 2
    assert beats[0]["time"] == "0-18s"
    assert "time" in beats[1]
    assert beats[0]["point"]


def test_segment_beats_empty_text():
    assert segment_beats("") == []


def test_detect_awkward_flags_long_sentence():
    sentence = "他是一个非常非常非常热爱唱歌并且每天都要坚持练习发声技巧的年轻男孩。"
    results = detect_awkward_sentences(sentence, max_len=30)
    assert len(results) == 1
    assert any("句子过长" in issue for issue in results[0]["issues"])


def test_detect_awkward_flags_repeated_word():
    sentence = "他反复反复反复地确认了这个消息。"
    results = detect_awkward_sentences(sentence, max_len=30)
    assert len(results) == 1
    assert any("重复" in issue for issue in results[0]["issues"])


def test_extract_entities_parses_provider_json():
    class FakeProvider:
        def generate(self, prompt, system=None, **kw):
            return (
                '{"characters":[{"name":"男主","description":"黑发白衬衫"}],'
                '"scenes":[{"name":"总裁办公室"}]}'
            )

    entities = extract_entities(FakeProvider(), "剧本")
    assert entities["characters"][0]["name"] == "男主"
    assert entities["scenes"][0]["name"] == "总裁办公室"


def test_extract_entities_tolerates_invalid_json():
    class FakeProvider:
        def generate(self, prompt, system=None, **kw):
            return "抱歉，我无法抽取"

    entities = extract_entities(FakeProvider(), "剧本")
    assert entities["characters"] == []
    assert entities["scenes"] == []

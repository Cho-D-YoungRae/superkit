from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample-captions.vtt"


def test_parse_vtt_extracts_cues(yt_transcript):
    cues = yt_transcript.parse_vtt(FIXTURE.read_text(encoding="utf-8"))
    assert [c.start for c in cues] == [0.0, 2.0, 4.0, 12.0]
    assert cues[2].text == "위키 패턴을 다룹니다 핵심은 압축입니다"  # 태그 제거·라인 병합


def test_dedupe_rolling_captions(yt_transcript):
    cues = yt_transcript.dedupe_cues(yt_transcript.parse_vtt(FIXTURE.read_text(encoding="utf-8")))
    assert [c.text for c in cues] == [
        "안녕하세요 오늘은",
        "위키 패턴을 다룹니다",
        "핵심은 압축입니다",
        "다음 주제로 넘어갑니다",
    ]


def test_paragraphs_split_on_gap(yt_transcript):
    cues = yt_transcript.dedupe_cues(yt_transcript.parse_vtt(FIXTURE.read_text(encoding="utf-8")))
    paras = yt_transcript.to_paragraphs(cues, gap=4.0, max_chars=600)
    assert len(paras) == 2
    assert paras[0][0] == 0.0
    assert paras[1] == (12.0, "다음 주제로 넘어갑니다")


def test_paragraphs_split_on_length(yt_transcript):
    Cue = yt_transcript.Cue
    cues = [Cue(start=float(i), text="가" * 250) for i in range(4)]
    paras = yt_transcript.to_paragraphs(cues, gap=100.0, max_chars=600)
    assert len(paras) > 1


def test_format_timestamp(yt_transcript):
    assert yt_transcript.format_timestamp(0) == "00:00"
    assert yt_transcript.format_timestamp(75) == "01:15"
    assert yt_transcript.format_timestamp(3671) == "1:01:11"


def test_render_markdown_frontmatter_and_markers(yt_transcript):
    meta = {
        "title": 'He said "hi"',
        "channel": "ch",
        "url": "https://youtu.be/x",
        "upload_date": "2026-07-01",
        "duration": "10:00",
        "lang": "ko",
        "kind": "auto",
        "retrieved": "2026-07-27",
    }
    out = yt_transcript.render_markdown(meta, [(0.0, "본문 첫 문단"), (75.0, "둘째 문단")])
    assert out.startswith("---\n")
    assert 'title: "He said \\"hi\\""' in out
    assert "[00:00] 본문 첫 문단" in out
    assert "[01:15] 둘째 문단" in out

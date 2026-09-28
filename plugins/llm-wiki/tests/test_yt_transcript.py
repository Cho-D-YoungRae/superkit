from pathlib import Path

import pytest
import yaml

FIXTURE = Path(__file__).parent / "fixtures" / "sample-captions.vtt"

# yt-dlp info 모사용 자막 URL — 기계 번역 트랙은 원본 URL에 tlang=이 붙는다
ORIG_EN = "https://www.youtube.com/api/timedtext?v=x&lang=en&kind=asr"
TRANS_KO = ORIG_EN + "&tlang=ko"


def _fmts(url: str, exts: tuple[str, ...] = ("json3", "vtt")) -> list[dict]:
    """yt-dlp 자막 형식 목록 모사 — vtt 외 형식을 섞어 형식 필터도 함께 검증한다."""
    return [{"ext": ext, "url": f"{url}&fmt={ext}"} for ext in exts]


def _frontmatter(out: str) -> dict:
    return yaml.safe_load(out.split("---\n")[1])


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


def test_render_markdown_frontmatter_is_typed_yaml(yt_transcript):
    # YAML 1.1(PyYAML)은 따옴표 없는 10:00을 60진수 정수 600으로, no(노르웨이어)를 False로 읽는다
    meta = {
        "title": 'He said "hi"',
        "channel": "ch",
        "url": "https://youtu.be/x",
        "upload_date": "2026-07-01",
        "duration": "10:00",
        "lang": "no",
        "kind": "auto-translated",
        "retrieved": "2026-07-27",
    }
    fm = _frontmatter(yt_transcript.render_markdown(meta, [(0.0, "본문")]))
    assert fm["duration"] == "10:00"
    assert fm["lang"] == "no"
    assert fm["kind"] == "auto-translated"
    assert fm["title"] == 'He said "hi"'
    long = _frontmatter(yt_transcript.render_markdown({**meta, "duration": "1:01:11"}, []))
    assert long["duration"] == "1:01:11"


def test_parse_vtt_unescapes_html_entities(yt_transcript):
    # 엔티티 복원은 태그 제거 뒤에 — &lt;b&gt;가 만든 <b>는 태그가 아니라 본문이다
    vtt = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:02.000\n&gt;&gt; Q&amp;A &lt;시작&gt;\n\n"
        "00:00:02.000 --> 00:00:04.000\n<c>&lt;b&gt;</c>태그는&nbsp;지운다\n"
    )
    assert [c.text for c in yt_transcript.parse_vtt(vtt)] == [">> Q&A <시작>", "<b>태그는 지운다"]


def test_pick_track_manual_beats_auto(yt_transcript):
    info = {
        "subtitles": {"en-US": _fmts("https://yt.test/manual-en")},
        "automatic_captions": {"en-orig": _fmts(ORIG_EN), "en": _fmts(ORIG_EN), "ko": _fmts(TRANS_KO)},
    }
    assert yt_transcript.pick_track(info, ["ko", "en"]) == (
        "en-US", "https://yt.test/manual-en&fmt=vtt", "manual")
    info["subtitles"]["ko"] = _fmts("https://yt.test/manual-ko")
    assert yt_transcript.pick_track(info, ["ko", "en"]) == (
        "ko", "https://yt.test/manual-ko&fmt=vtt", "manual")


def test_pick_track_prefers_original_over_machine_translation(yt_transcript):
    # yt-dlp: 원본 ASR은 `<lang>-orig`(+호환용 `<lang>`), 나머지 언어 키는 tlang= 기계 번역
    info = {
        "subtitles": {},
        "automatic_captions": {
            "af": _fmts(ORIG_EN + "&tlang=af"),
            "en-orig": _fmts(ORIG_EN),
            "en": _fmts(ORIG_EN),
            "ko": _fmts(TRANS_KO),
        },
    }
    assert yt_transcript.pick_track(info, ["ko", "en"]) == ("en", ORIG_EN + "&fmt=vtt", "auto")


def test_pick_track_original_outside_langs(yt_transcript):
    orig_ja = "https://yt.test/timedtext?lang=ja&kind=asr"
    info = {  # subtitles 키 자체가 없는 info도 허용
        "automatic_captions": {
            "en": _fmts(orig_ja + "&tlang=en"),
            "ja-orig": _fmts(orig_ja),
            "ja": _fmts(orig_ja),
            "ko": _fmts(orig_ja + "&tlang=ko"),
        },
    }
    assert yt_transcript.pick_track(info, ["ko", "en"]) == ("ja", orig_ja + "&fmt=vtt", "auto")


def test_pick_track_original_url_comes_from_orig_key(yt_transcript):
    # 원본 ASR이 둘(다중 오디오)이면 호환용 `en` 키 앞쪽에 es→en 번역 트랙이 섞인다
    orig_es = "https://yt.test/timedtext?lang=es&kind=asr"
    orig_en = "https://yt.test/timedtext?lang=en&kind=asr"
    info = {
        "automatic_captions": {
            "en": _fmts(orig_es + "&tlang=en") + _fmts(orig_en),
            "es-orig": _fmts(orig_es),
            "es": _fmts(orig_es) + _fmts(orig_en + "&tlang=es"),
            "ko": _fmts(orig_es + "&tlang=ko") + _fmts(orig_en + "&tlang=ko"),
            "en-orig": _fmts(orig_en),
        },
    }
    assert yt_transcript.pick_track(info, ["ko", "en"]) == ("en", orig_en + "&fmt=vtt", "auto")
    assert yt_transcript.pick_track(info, ["ko"]) == ("es", orig_es + "&fmt=vtt", "auto")


def test_pick_track_without_orig_keys_treats_auto_as_original(yt_transcript):
    # 번역 언어 목록을 주지 않는 클라이언트: 자동 자막은 원본 언어뿐이고 `-orig` 키가 없다
    info = {"automatic_captions": {"fr": _fmts("https://yt.test/fr"), "en": _fmts("https://yt.test/en")}}
    assert yt_transcript.pick_track(info, ["ko", "en"]) == ("en", "https://yt.test/en&fmt=vtt", "auto")
    only_fr = {"automatic_captions": {"fr": _fmts("https://yt.test/fr")}}
    assert yt_transcript.pick_track(only_fr, ["ko", "en"]) == ("fr", "https://yt.test/fr&fmt=vtt", "auto")


def test_pick_track_machine_translation_is_last_resort(yt_transcript):
    # 원본(`-orig`·호환 키 모두)에 vtt가 없을 때만 번역 트랙 — kind로 번역임을 드러낸다
    no_vtt = ("json3", "srv3")
    info = {
        "automatic_captions": {
            "en-orig": _fmts(ORIG_EN, no_vtt),
            "en": _fmts(ORIG_EN, no_vtt),
            "ja": _fmts(ORIG_EN + "&tlang=ja"),
            "ko": _fmts(TRANS_KO),
        },
    }
    assert yt_transcript.pick_track(info, ["ko", "en"]) == ("ko", TRANS_KO + "&fmt=vtt", "auto-translated")
    assert yt_transcript.pick_track(info, ["en"]) is None  # 번역 트랙은 langs 일치만 — 임의 언어 금지


def test_pick_track_requires_vtt_with_url(yt_transcript):
    manual_unusable = {"ko": [{"ext": "srv3", "url": "https://yt.test/srv3"}, {"ext": "vtt"}]}
    info = {"subtitles": manual_unusable, "automatic_captions": {"ko": _fmts("https://yt.test/ko")}}
    assert yt_transcript.pick_track(info, ["ko", "en"]) == ("ko", "https://yt.test/ko&fmt=vtt", "auto")
    info["automatic_captions"] = {"ko": _fmts("https://yt.test/ko", ("json3",))}
    assert yt_transcript.pick_track(info, ["ko", "en"]) is None


def test_pick_track_none_without_tracks(yt_transcript):
    assert yt_transcript.pick_track({}, ["ko", "en"]) is None
    assert yt_transcript.pick_track({"subtitles": None, "automatic_captions": None}, ["ko", "en"]) is None


def test_ydl_opts_single_video_with_timeout(yt_transcript):
    opts = yt_transcript.YDL_OPTS
    assert opts["noplaylist"] is True  # watch?v=ID&list=PL… 가 재생목록 전체로 풀리지 않게
    assert isinstance(opts.get("socket_timeout"), (int, float)) and opts["socket_timeout"] > 0
    assert opts["skip_download"] is True  # 영상 다운로드 금지 계약


@pytest.mark.parametrize("argv", [["https://youtu.be/x", "--bogus"], []])
def test_usage_error_exits_1_not_2(yt_transcript, argv):
    # exit 2는 "자막 없음" 전용 — argparse 기본 사용법 오류 코드(2)와 겹치면 안 된다
    with pytest.raises(SystemExit) as exc:
        yt_transcript.main(argv)
    assert exc.value.code == 1


def test_pick_track_prefers_manual_in_original_language(yt_transcript):
    # 원어 수동 자막은 langs 밖이어도 원어 ASR보다 낫다(사람이 만든 원문 그대로)
    orig_ja = "https://yt.test/timedtext?lang=ja&kind=asr"
    info = {
        "subtitles": {"ja": _fmts("https://yt.test/manual-ja")},
        "automatic_captions": {"ja-orig": _fmts(orig_ja), "ja": _fmts(orig_ja), "ko": _fmts(orig_ja + "&tlang=ko")},
    }
    assert yt_transcript.pick_track(info, ["ko", "en"]) == ("ja", "https://yt.test/manual-ja&fmt=vtt", "manual")
    # 자동 자막이 아예 없어도 info.language로 원어를 안다
    only_manual = {"language": "ja", "subtitles": {"ja": _fmts("https://yt.test/manual-ja")}}
    assert yt_transcript.pick_track(only_manual, ["ko", "en"]) == ("ja", "https://yt.test/manual-ja&fmt=vtt", "manual")


def test_fetch_rejects_pure_playlist_url(yt_transcript, monkeypatch, capsys):
    import sys
    import types

    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=False):
            assert self.opts.get("extract_flat") == "in_playlist"  # 목록 항목을 하나하나 조회하지 않는다
            return {"_type": "playlist", "entries": [{"id": "a"}, {"id": "b"}]}

    fake = types.ModuleType("yt_dlp")
    fake.YoutubeDL = FakeYDL
    monkeypatch.setitem(sys.modules, "yt_dlp", fake)
    code = yt_transcript.main(["https://www.youtube.com/playlist?list=PLx"])
    assert code == 1  # 자막 없음(exit 2)으로 오안내하지 않는다
    assert "재생목록" in capsys.readouterr().err

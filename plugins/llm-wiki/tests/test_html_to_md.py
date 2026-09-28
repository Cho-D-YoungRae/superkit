import contextlib
import datetime
import io

import pytest
import yaml

BASE = "https://example.com/blog/post"


def body_of(html_to_md, html, base=BASE):
    return html_to_md.convert(html, base)[1]


def run(html_to_md, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = html_to_md.main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


def test_headings_paragraphs_and_inline_formatting(html_to_md):
    md = body_of(html_to_md, "<h1>제목</h1><p>본문 <strong>강조</strong>와 <em>기울임</em>, <code>x = 1</code>.</p><h3>소제목</h3>")
    assert md.splitlines() == ["# 제목", "", "본문 **강조**와 *기울임*, `x = 1`.", "", "### 소제목"]


def test_drops_non_content_elements(html_to_md):
    html = """<body>
      <nav>메뉴</nav><header role="banner">사이트 헤더</header>
      <p>남는 본문</p>
      <script>track()</script><style>p{}</style><noscript>JS 켜세요</noscript>
      <aside>관련 글</aside><form>구독<input></form><footer>저작권</footer>
      <div hidden>숨김</div><div aria-hidden="true">스크린리더 숨김</div>
      <div style="display: none">안 보임</div><div role="navigation">빵부스러기</div>
    </body>"""
    md = body_of(html_to_md, html)
    assert md == "남는 본문"


def test_prefers_main_over_page_chrome(html_to_md):
    html = "<body><div>로그인 | 가입</div><main><h2>진짜 글</h2><p>" + "내용 " * 60 + "</p></main><div>추천 링크</div></body>"
    md = body_of(html_to_md, html)
    assert md.startswith("## 진짜 글") and "로그인" not in md and "추천 링크" not in md


def test_picks_largest_article_when_no_main(html_to_md):
    html = "<body><article><p>짧은 카드</p></article><article><h1>본문 글</h1><p>" + "긴 내용 " * 80 + "</p></article></body>"
    md = body_of(html_to_md, html)
    assert md.startswith("# 본문 글") and "짧은 카드" not in md


def test_links_and_images_become_absolute(html_to_md):
    html = (
        '<p><a href="../other">다른 글</a> · <a href="#sec">목차</a> · <a href="javascript:void(0)">클릭</a> · '
        '<a href="mailto:a@b.c">메일</a></p>'
        '<p><img src="/img/a.png" alt="그림 A"> <img data-src="lazy.png" src="data:image/gif;base64,R0l" alt="지연"></p>'
    )
    md = body_of(html_to_md, html)
    assert "[다른 글](https://example.com/other)" in md
    assert "목차" in md and "(#sec)" not in md
    assert "클릭" in md and "javascript:" not in md
    assert "[메일](mailto:a@b.c)" in md
    assert "![그림 A](https://example.com/img/a.png)" in md
    assert "![지연](https://example.com/blog/lazy.png)" in md and "base64" not in md


def test_nested_and_ordered_lists(html_to_md):
    md = body_of(html_to_md, "<ul><li>하나<ul><li>하나-가</li></ul></li><li>둘</li></ul><ol start='3'><li>셋</li><li>넷</li></ol>")
    assert md.splitlines() == ["- 하나", "  - 하나-가", "- 둘", "", "3. 셋", "4. 넷"]


def test_unclosed_list_items_do_not_nest(html_to_md):
    md = body_of(html_to_md, "<ul><li>가<li>나</ul><p>끝</p>")
    assert md.splitlines() == ["- 가", "- 나", "", "끝"]


def test_code_block_keeps_whitespace_language_and_entities(html_to_md):
    html = '<pre><code class="language-python">def f(x):\n    return x &lt; 1\n</code></pre>'
    md = body_of(html_to_md, html)
    assert md == "```python\ndef f(x):\n    return x < 1\n```"


def test_code_block_containing_backticks_uses_longer_fence(html_to_md):
    md = body_of(html_to_md, "<pre>```\nnested\n```</pre>")
    assert md.startswith("````\n") and md.endswith("\n````")


def test_table_to_pipe_table(html_to_md):
    html = "<table><thead><tr><th>이름</th><th>값</th></tr></thead><tbody><tr><td>a|b</td><td>1</td></tr><tr><td>c</td></tr></tbody></table>"
    md = body_of(html_to_md, html)
    assert md.splitlines() == ["| 이름 | 값 |", "| --- | --- |", "| a\\|b | 1 |", "| c |  |"]


def test_blockquote_and_rule(html_to_md):
    md = body_of(html_to_md, "<blockquote><p>인용 1</p><p>인용 2</p></blockquote><hr><p>다음</p>")
    assert md.splitlines() == ["> 인용 1", ">", "> 인용 2", "", "---", "", "다음"]


def test_whitespace_entities_and_line_breaks(html_to_md):
    md = body_of(html_to_md, "<p>  Q&amp;A&nbsp;세션\n\n   시작 <br>둘째   줄 </p>\n\n\n<p>셋</p>")
    assert md == "Q&A 세션 시작\n둘째 줄\n\n셋"


def test_metadata_prefers_og_and_resolves_canonical(html_to_md):
    html = """<html><head><title>글 제목 | 사이트</title>
      <meta property="og:title" content="글 제목"><meta property="og:site_name" content="사이트">
      <meta name="author" content="홍길동"><meta property="article:published_time" content="2026-07-01T09:00:00+09:00">
      <link rel="canonical" href="/blog/post-canonical"></head><body><p>본문</p></body></html>"""
    meta, _ = html_to_md.convert(html, BASE)
    assert meta["title"] == "글 제목"
    assert meta["site_name"] == "사이트"
    assert meta["author"] == "홍길동"
    assert meta["published"] == "2026-07-01T09:00:00+09:00"
    assert meta["canonical"] == "https://example.com/blog/post-canonical"


@pytest.mark.parametrize("value", ["262588213843476", "https://facebook.com/someone"])
def test_author_ignores_profile_ids_and_urls(html_to_md, value):
    # GitHub 등은 article:author에 페이스북 숫자 ID·프로필 URL을 넣는다 — 저자명이 아니다
    meta, _ = html_to_md.convert(f'<meta property="article:author" content="{value}"><p>본문</p>', BASE)
    assert meta["author"] == ""


def test_decode_uses_meta_charset(html_to_md):
    data = "<meta charset='euc-kr'><p>안녕하세요</p>".encode("euc-kr")
    assert "안녕하세요" in html_to_md.decode_html(data, None)
    assert "안녕하세요" in html_to_md.decode_html("<p>안녕하세요</p>".encode("utf-8"), "utf-8")


@pytest.mark.parametrize(
    ("content_type", "kind"),
    [
        ("text/html; charset=utf-8", "html"),
        ("application/xhtml+xml", "html"),
        ("text/plain; charset=utf-8", "text"),
        ("text/markdown", "text"),
        ("application/pdf", None),
        ("application/json", None),
        (None, "html"),
    ],
)
def test_classify_content_type(html_to_md, content_type, kind):
    assert html_to_md.classify_content_type(content_type) == kind


def test_render_frontmatter_omits_empty_and_duplicate_fields(html_to_md):
    meta = {"title": 'He said "hi"', "site_name": "", "author": "홍길동", "published": "", "canonical": BASE}
    out = html_to_md.render(BASE, meta, "본문", extraction="html", retrieved="2026-09-28")
    fm = yaml.safe_load(out.split("---")[1])
    assert fm == {
        "url": BASE,
        "title": 'He said "hi"',
        "author": "홍길동",
        "retrieved": datetime.date(2026, 9, 28),  # 다른 스크립트처럼 날짜는 비인용 YAML date
        "extraction": "html",
    }
    assert out.endswith("---\n\n본문\n")


def test_file_mode_converts_local_html(html_to_md, tmp_path):
    page = tmp_path / "saved.html"
    page.write_text("<title>저장한 글</title><main><p>" + "로컬 본문 " * 60 + '</p><a href="next">다음</a></main>', encoding="utf-8")
    code, out, _ = run(html_to_md, ["--file", str(page), "--base-url", "https://ex.com/a/"])
    assert code == 0
    assert out.startswith("---\n") and 'title: "저장한 글"' in out and "extraction: html" in out
    assert "[다음](https://ex.com/a/next)" in out


def test_thin_body_exits_two_but_still_prints(html_to_md, tmp_path):
    page = tmp_path / "spa.html"
    page.write_text('<body><div id="root"></div><p>Loading…</p></body>', encoding="utf-8")
    code, out, err = run(html_to_md, ["--file", str(page)])
    assert code == 2
    assert "Loading…" in out
    assert "본문" in err


def test_usage_errors_exit_one(html_to_md):
    assert run(html_to_md, [])[0] == 1
    assert run(html_to_md, ["https://example.com", "--bogus"])[0] == 1
    assert run(html_to_md, ["https://example.com", "--file", "x.html"])[0] == 1

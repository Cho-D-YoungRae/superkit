#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""HTML → 마크다운 기계 변환 — llm-wiki 플러그인(web-extract 스킬의 전처리 헬퍼).

usage: uv run html_to_md.py URL [--timeout 30]
       uv run html_to_md.py --file PATH [--base-url URL]

판단 없이 기계적으로만 변환한다. script·style·nav·footer·aside·form 같은 비본문 요소와
숨김 요소(hidden·aria-hidden·display:none·탐색용 ARIA role)를 버리고, <main>(없으면 가장 큰
<article>)이 본문 글자의 상당 부분을 담으면 그 범위만 변환한다. 제목·문단·목록·인용·코드·표·
링크·이미지를 마크다운으로 옮기고 링크·이미지는 절대 URL로 바꾼다. 무엇이 본문인지의 최종
판단(남은 군더더기 제거·누락 확인)은 호출한 에이전트가 한다.

text/plain·text/markdown 응답(예: raw.githubusercontent.com)은 변환 없이 통과시킨다.
stdout: frontmatter(url, title, site_name, author, published, canonical, retrieved, extraction) + 본문.
wiki/ 파일 직접 쓰기 금지. 서드파티 의존 없음(표준 라이브러리만).

exit: 0 성공 / 1 일반 오류 / 2 특수 상황 — 접근 차단(401·403·429·451), HTML이 아닌 응답(PDF 등),
      본문 과소(JS 렌더링·차단 화면 의심 — 이때는 결과를 stdout에 그대로 내보낸다)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from typing import NoReturn
from urllib.parse import urljoin

MIN_BODY_CHARS = 200        # 공백 제외 본문 글자 수가 이보다 적으면 exit 2
MAX_BYTES = 10 * 1024 * 1024
MAIN_MIN_SHARE = 0.25       # <main>/<article>이 body 글자의 이 비율 이상을 담을 때만 범위를 좁힌다
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 llm-wiki"
)
BLOCKED_STATUS = {401, 403, 429, 451}

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
DROP_TAGS = {
    "head", "title", "script", "style", "noscript", "template", "svg", "canvas", "iframe", "object", "embed",
    "video", "audio", "form", "button", "input", "select", "textarea", "nav", "footer", "aside", "dialog",
}
DROP_ROLES = {"navigation", "banner", "contentinfo", "complementary", "search", "dialog"}
BLOCK_TAGS = {
    "html", "body", "main", "article", "section", "div", "header", "figure", "figcaption", "address", "center",
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "dl", "dt", "dd", "blockquote", "pre",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "hr", "details", "summary",
}
# 열린 <p> 안에서 이 태그가 시작되면 <p>를 닫는다(HTML 암묵적 종료 규칙의 단순화)
P_CLOSERS = {
    "p", "div", "ul", "ol", "dl", "pre", "blockquote", "table", "section", "article", "header", "footer",
    "nav", "aside", "main", "figure", "hr", "form", "details", "address", "h1", "h2", "h3", "h4", "h5", "h6",
}
# 코드 블록 언어를 담는 class 토큰 — highlight-source-x(GitHub)를 highlight-x(Sphinx)보다 먼저 맞춘다
CODE_LANG_CLASS_RE = re.compile(r"^(?:language|lang|highlight-source|highlight)-([\w+#.-]+)$")
NON_LANGUAGES = {"default", "none"}  # Sphinx 기본 하이라이터 표기 등 — 언어가 아니다
# 태그 → (닫을 열린 태그들, 탐색을 멈출 경계 태그들): 닫는 태그를 생략한 li·td 등이 중첩되지 않게
IMPLIED_END = {
    "li": ({"li"}, {"ul", "ol"}),
    "dt": ({"dt", "dd"}, {"dl"}),
    "dd": ({"dt", "dd"}, {"dl"}),
    "tr": ({"tr"}, {"table", "thead", "tbody", "tfoot"}),
    "td": ({"td", "th"}, {"tr", "table"}),
    "th": ({"td", "th"}, {"tr", "table"}),
}


class BlockedError(Exception):
    pass


class UnsupportedContentError(Exception):
    pass


class _Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag: str, attrs: dict[str, str], parent: _Node | None = None):
        self.tag = tag
        self.attrs = attrs
        self.children: list[_Node | str] = []
        self.parent = parent


class _TreeBuilder(HTMLParser):
    """관대한 DOM 트리 빌더 — 짝 없는 닫는 태그는 무시하고, 생략된 닫는 태그는 추정해 닫는다."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._implied_close(tag)
        node = _Node(tag, {k: (v or "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._implied_close(tag)
        self.stack[-1].children.append(_Node(tag, {k: (v or "") for k, v in attrs}, self.stack[-1]))

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)

    def _implied_close(self, tag: str) -> None:
        if tag in P_CLOSERS and self.stack[-1].tag == "p":
            self.stack.pop()
        rule = IMPLIED_END.get(tag)
        if not rule:
            return
        closes, boundary = rule
        for i in range(len(self.stack) - 1, 0, -1):
            t = self.stack[i].tag
            if t in closes:
                del self.stack[i:]
                return
            if t in boundary:
                return


# ── 트리 유틸 ────────────────────────────────────────────────────────────────

def _is_dropped(node: _Node) -> bool:
    if node.tag in DROP_TAGS:
        return True
    a = node.attrs
    if "hidden" in a or a.get("aria-hidden", "").lower() == "true":
        return True
    if a.get("role", "").lower() in DROP_ROLES:
        return True
    style = a.get("style", "").replace(" ", "").lower()
    return "display:none" in style or "visibility:hidden" in style


def _iter(node: _Node, visible_only: bool = False) -> Iterator[_Node]:
    for c in node.children:
        if isinstance(c, _Node):
            if visible_only and _is_dropped(c):
                continue
            yield c
            yield from _iter(c, visible_only)


def _text_len(node: _Node) -> int:
    total = 0
    for c in node.children:
        if isinstance(c, str):
            total += len(c.strip())
        elif not _is_dropped(c):
            total += _text_len(c)
    return total


def _raw_text(node: _Node) -> str:
    parts: list[str] = []
    for c in node.children:
        if isinstance(c, str):
            parts.append(c)
        elif c.tag == "br":
            parts.append("\n")
        elif not _is_dropped(c):
            parts.append(_raw_text(c))
    return "".join(parts)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _content_root(root: _Node) -> _Node:
    body = next((n for n in _iter(root) if n.tag == "body"), root)
    total = _text_len(body) or 1
    predicates = (
        lambda n: n.tag == "main" or n.attrs.get("role", "").lower() == "main",
        lambda n: n.tag == "article",
    )
    for pred in predicates:
        candidates = [n for n in _iter(body, visible_only=True) if pred(n)]
        if candidates:
            best = max(candidates, key=_text_len)
            if _text_len(best) >= total * MAIN_MIN_SHARE:
                return best
    return body


def _metadata(root: _Node, base_url: str) -> dict[str, str]:
    metas: dict[str, str] = {}
    title = canonical = ""
    for n in _iter(root):
        if n.tag == "meta":
            key = (n.attrs.get("property") or n.attrs.get("name") or n.attrs.get("itemprop") or "").lower()
            content = _collapse(n.attrs.get("content", ""))
            if key and content:
                metas.setdefault(key, content)
        elif n.tag == "title" and not title:
            title = _collapse(_raw_text(n))
        elif n.tag == "link" and "canonical" in n.attrs.get("rel", "").lower().split() and not canonical:
            href = n.attrs.get("href", "").strip()
            if href:
                canonical = urljoin(base_url, href)
    author = metas.get("author") or metas.get("article:author") or metas.get("parsely-author") or ""
    if author.startswith(("http://", "https://")) or author.isdigit():
        author = ""  # article:author가 프로필 URL·숫자 ID(GitHub 등)인 경우는 저자명이 아니다
    published = (
        metas.get("article:published_time") or metas.get("datepublished")
        or metas.get("date") or metas.get("pubdate") or ""
    )
    return {
        "title": metas.get("og:title") or metas.get("twitter:title") or title,
        "site_name": metas.get("og:site_name", ""),
        "author": author,
        "published": published,
        "canonical": canonical,
    }


# ── 마크다운 렌더링 ──────────────────────────────────────────────────────────

def _wrap(text: str, mark: str) -> str:
    core = text.strip()
    if not core:
        return text
    lead = text[: len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    return f"{lead}{mark}{core}{mark}{trail}"


def _code_span(text: str) -> str:
    if not text:
        return ""
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def _link(el: _Node, inner: str, base: str) -> str:
    href = el.attrs.get("href", "").strip()
    text = inner.strip()
    if not text or not href or href.startswith("#") or href.lower().startswith("javascript:"):
        return inner
    url = urljoin(base, href)
    if re.search(r"[\s()]", url):
        url = f"<{url}>"
    lead = inner[: len(inner) - len(inner.lstrip())]
    trail = inner[len(inner.rstrip()):]
    return f"{lead}[{text}]({url}){trail}"


def _image(el: _Node, base: str) -> str:
    src = ""
    for attr in ("data-src", "data-original", "data-lazy-src", "src"):
        v = el.attrs.get(attr, "").strip()
        if v and not v.startswith("data:"):
            src = v
            break
    if not src:
        srcset = el.attrs.get("srcset") or el.attrs.get("data-srcset") or ""
        first = srcset.split(",")[0].strip().split(" ")[0] if srcset else ""
        src = first if first and not first.startswith("data:") else ""
    if not src:
        return ""
    return f"![{_collapse(el.attrs.get('alt', ''))}]({urljoin(base, src)})"


def _inline(node: _Node, base: str) -> str:
    out: list[str] = []
    for c in node.children:
        if isinstance(c, str):
            out.append(re.sub(r"\s+", " ", c))
        elif not _is_dropped(c):
            out.append(_inline_el(c, base))
    return "".join(out)


def _inline_el(el: _Node, base: str) -> str:
    tag = el.tag
    if tag == "br":
        return "\n"
    if tag == "img":
        return _image(el, base)
    if tag in ("code", "kbd", "samp", "tt"):
        return _code_span(_collapse(_raw_text(el)))
    inner = _inline(el, base)
    if tag == "a":
        return _link(el, inner, base)
    if tag in ("strong", "b"):
        return _wrap(inner, "**")
    if tag in ("em", "i"):
        return _wrap(inner, "*")
    if tag in ("del", "s", "strike"):
        return _wrap(inner, "~~")
    if tag in BLOCK_TAGS:  # 인라인 문맥 속 블록 요소(카드형 링크 등)는 공백으로 구분
        return f" {inner} "
    return inner


def _clean_inline(text: str) -> str:
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def _blocks(node: _Node, base: str) -> list[str]:
    blocks: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        text = _clean_inline("".join(buf))
        if text:
            blocks.append(text)
        buf.clear()

    for c in node.children:
        if isinstance(c, str):
            buf.append(re.sub(r"\s+", " ", c))
        elif _is_dropped(c):
            continue
        elif c.tag in BLOCK_TAGS:
            flush()
            blocks.extend(_block(c, base))
        else:
            buf.append(_inline_el(c, base))
    flush()
    return blocks


def _list_item(marker: str, body: str) -> str:
    lines = body.split("\n")
    rest = [(" " * len(marker) + ln) if ln else "" for ln in lines[1:]]
    return "\n".join([marker + lines[0], *rest])


def _list(el: _Node, base: str) -> str:
    ordered = el.tag == "ol"
    try:
        n = int(el.attrs.get("start", "1"))
    except ValueError:
        n = 1
    items: list[str] = []
    for c in el.children:
        if isinstance(c, str) or _is_dropped(c):
            continue
        if c.tag != "li":  # 목록 안의 비-li 래퍼 — 렌더 결과를 그대로 항목으로
            items.extend(_block(c, base) if c.tag in BLOCK_TAGS else [_clean_inline(_inline_el(c, base))])
            continue
        body = "\n".join(_blocks(c, base))
        if not body:
            continue
        items.append(_list_item(f"{n}. " if ordered else "- ", body))
        n += 1
    return "\n".join(i for i in items if i)


def _code_lang(pre: _Node) -> str:
    """코드 블록 언어 — <pre>, 그 안의 첫 <code>, 가까운 조상 3단계 순으로 찾는다.
    Prism·highlight.js는 pre/code에, Jekyll·Rouge는 바깥 div에(language-x), Sphinx는 조부모 div에(highlight-x),
    GitHub는 div에(highlight-source-x) 언어를 단다."""
    candidates = [pre, *[c for c in _iter(pre) if c.tag == "code"][:1]]
    node = pre.parent
    for _ in range(3):
        if node is None:
            break
        candidates.append(node)
        node = node.parent
    for n in candidates:
        for attr in ("data-lang", "data-language"):
            if n.attrs.get(attr):
                return n.attrs[attr].strip()
        for token in n.attrs.get("class", "").split():
            m = CODE_LANG_CLASS_RE.match(token)
            if m and m.group(1) not in NON_LANGUAGES:
                return m.group(1)
    return ""


def _code_block(el: _Node) -> str:
    text = _raw_text(el)
    if text.startswith("\n"):
        text = text[1:]
    text = text.rstrip("\n")
    if not text.strip():
        return ""
    lang = _code_lang(el)
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{lang}\n{text}\n{fence}"


def _table_rows(node: _Node) -> Iterator[_Node]:
    for c in node.children:
        if isinstance(c, _Node) and not _is_dropped(c):
            if c.tag == "tr":
                yield c
            elif c.tag in ("thead", "tbody", "tfoot"):
                yield from _table_rows(c)


def _table(el: _Node, base: str) -> str:
    rows: list[list[str]] = []
    for tr in _table_rows(el):
        cells = [
            _clean_inline(_inline(c, base)).replace("\n", " ").replace("|", "\\|")
            for c in tr.children
            if isinstance(c, _Node) and c.tag in ("td", "th") and not _is_dropped(c)
        ]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def _block(el: _Node, base: str) -> list[str]:
    tag = el.tag
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        text = _clean_inline(_inline(el, base)).replace("\n", " ")
        return [f"{'#' * int(tag[1])} {text}"] if text else []
    if tag in ("ul", "ol"):
        text = _list(el, base)
        return [text] if text else []
    if tag == "li":  # 목록 밖에 떨어진 li
        body = "\n".join(_blocks(el, base))
        return [_list_item("- ", body)] if body else []
    if tag == "pre":
        code = _code_block(el)
        return [code] if code else []
    if tag == "blockquote":
        inner = "\n\n".join(_blocks(el, base))
        return ["\n".join(f"> {ln}" if ln else ">" for ln in inner.split("\n"))] if inner else []
    if tag == "table":
        table = _table(el, base)
        return [table] if table else []
    if tag == "hr":
        return ["---"]
    if tag == "dt":
        text = _clean_inline(_inline(el, base))
        return [_wrap(text, "**")] if text else []
    return _blocks(el, base)  # p·div·section·figure·dd·details 등 컨테이너


def convert(html: str, base_url: str = "") -> tuple[dict[str, str], str]:
    """HTML 문자열 → (메타데이터, 마크다운 본문). 순수 함수."""
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))  # 깊게 중첩된 DOM 대비
    builder = _TreeBuilder()
    builder.feed(html)
    builder.close()
    meta = _metadata(builder.root, base_url)
    body = "\n\n".join(_blocks(_content_root(builder.root), base_url))
    return meta, re.sub(r"\n{3,}", "\n\n", body).strip()


def decode_html(data: bytes, header_charset: str | None) -> str:
    charset = header_charset
    if not charset:
        m = re.search(rb"""<meta[^>]+charset\s*=\s*["']?\s*([A-Za-z0-9_-]+)""", data[:8192], re.I)
        charset = m.group(1).decode("ascii") if m else "utf-8"
    try:
        text = data.decode(charset, errors="replace")
    except LookupError:
        text = data.decode("utf-8", errors="replace")
    return text.lstrip("﻿")


def classify_content_type(content_type: str | None) -> str | None:
    """Content-Type → "html" | "text" | None(지원 외). 헤더가 없으면 HTML로 간주."""
    if not content_type:
        return "html"
    mime = content_type.split(";")[0].strip().lower()
    if mime in ("text/html", "application/xhtml+xml"):
        return "html"
    if mime in ("text/plain", "text/markdown", "text/x-markdown"):
        return "text"
    return None


def _q(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(url: str, meta: dict[str, str], body: str, extraction: str, retrieved: str) -> str:
    fields = [("url", url), ("title", meta.get("title", ""))]
    fields += [(k, meta[k]) for k in ("site_name", "author", "published") if meta.get(k)]
    canonical = meta.get("canonical", "")
    if canonical and canonical != url:
        fields.append(("canonical", canonical))
    lines = ["---", *(f"{k}: {_q(str(v))}" for k, v in fields), f"retrieved: {retrieved}", f"extraction: {extraction}", "---", ""]
    return "\n".join(lines) + "\n" + body.strip() + "\n"


def fetch(url: str, timeout: float) -> tuple[str, str, str]:
    """(최종 URL, "html"|"text", 디코드된 본문). 네트워크."""
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            kind = classify_content_type(resp.headers.get("Content-Type"))
            if kind is None:
                raise UnsupportedContentError(
                    f"HTML이 아닌 응답({resp.headers.get_content_type()}) — PDF면 내려받아 로컬 PDF 레시피로 처리하세요."
                )
            data = resp.read(MAX_BYTES + 1)
            charset = resp.headers.get_content_charset()
            final_url = resp.geturl()
    except urllib.error.HTTPError as e:
        if e.code in BLOCKED_STATUS:
            raise BlockedError(
                f"접근 차단(HTTP {e.code}) — 옵시디언 Web Clipper나 브라우저 저장본(--file)으로 우회하세요."
            ) from e
        raise
    if len(data) > MAX_BYTES:
        raise ValueError("응답이 너무 큼(10MB 초과)")
    return final_url, kind, decode_html(data, charset)


class _Parser(argparse.ArgumentParser):
    """사용법 오류는 exit 1 — argparse 기본값(2)은 플러그인 스크립트의 exit 2(도메인 특수상황) 규약과 충돌한다."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: 오류: {message}\n")


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description="HTML → 마크다운 기계 변환(stdout)")
    parser.add_argument("url", nargs="?", help="가져올 웹 페이지 URL")
    parser.add_argument("--file", help="URL 대신 로컬 HTML 파일을 변환")
    parser.add_argument("--base-url", default="", help="--file의 상대 링크를 풀 기준 URL")
    parser.add_argument("--timeout", type=float, default=30.0, help="네트워크 타임아웃(초, 기본 30)")
    args = parser.parse_args(argv)
    if bool(args.url) == bool(args.file):
        parser.error("URL과 --file 중 정확히 하나를 지정하세요")

    try:
        if args.file:
            path = Path(args.file)
            if not path.is_file():
                raise FileNotFoundError(f"파일이 없습니다: {path}")
            url, kind, text = args.base_url, "html", decode_html(path.read_bytes(), None)
        else:
            url, kind, text = fetch(args.url, args.timeout)
    except (BlockedError, UnsupportedContentError) as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"오류: {e}", file=sys.stderr)
        return 1

    if kind == "text":
        meta, body = {"title": ""}, text.strip()
    else:
        meta, body = convert(text, url)
    sys.stdout.write(render(url, meta, body, extraction=kind, retrieved=_dt.date.today().isoformat()))
    if len(re.sub(r"\s+", "", body)) < MIN_BODY_CHARS:
        print(
            "본문이 매우 짧음 — JS 렌더링 페이지나 차단 화면일 수 있다. 결과를 확인하고 필요하면 폴백하세요.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

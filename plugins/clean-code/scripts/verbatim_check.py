"""레퍼런스 md가 원서 텍스트를 연속으로 옮겨 왔는지 검사한다.

사용법: python3 -I verbatim_check.py <레퍼런스.md> <원서.txt> [<원서.txt> ...] [--window N]

원서 텍스트는 저장소에 두지 않는다. 레퍼런스를 고치는 사람이 갖고 있는 PDF에서
`pdftotext -layout clean-code.pdf book.txt`로 뽑아 해당 챕터 쪽만 잘라 쓴다.

md의 영어 단어열에서 N개(기본 10) 연속 단어 창을 만들고, 정규화한 원서 텍스트에
같은 단어열이 있으면 겹치는 창을 합쳐 보고한다. 결과가 없으면 "OK"를 출력한다.
걸린 구절이 허용 인용(큰따옴표와 쪽 표시, 15단어 미만, 파일당 2개 이하)인지는 사람이 판단한다.
"""
import re
import sys
import unicodedata

LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


def normalize_source(text):
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"=====.*?=====", " ", text)  # 쪽 표시 제거
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # 줄바꿈 하이픈 결합
    return words(text)


def words(text):
    text = text.lower().replace("’", "'").replace("‘", "'")
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text)


def md_tokens(text):
    # 한글 등 비ASCII 토큰은 창을 끊도록 구분자로 남긴다.
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    text = text.lower().replace("’", "'").replace("‘", "'")
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?|[^\sa-z0-9\W]+|[가-힣]+", text)


def main(argv):
    window = 10
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == "--window":
            window = int(argv[i + 1])
            i += 2
            continue
        args.append(argv[i])
        i += 1
    md_path, sources = args[0], args[1:]
    src_words = []
    for s in sources:
        src_words += normalize_source(open(s, encoding="utf-8", errors="replace").read())
    src_join = " " + " ".join(src_words) + " "
    toks = md_tokens(open(md_path, encoding="utf-8").read())
    hits = []
    for start in range(0, len(toks) - window + 1):
        win = toks[start:start + window]
        if any(not re.fullmatch(r"[a-z0-9]+(?:'[a-z]+)?", w) for w in win):
            continue
        if " " + " ".join(win) + " " in src_join:
            hits.append((start, start + window))
    merged = []
    for a, b in hits:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    if not merged:
        print("OK")
        return 0
    for a, b in merged:
        print(f"[{b - a} words] " + " ".join(toks[a:b]))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

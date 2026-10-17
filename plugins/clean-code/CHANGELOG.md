# Changelog

이 플러그인의 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다. 1.0.0 전에는
마이너 버전이 호환되지 않는 변경을 담을 수 있다.

## 0.1.0 — 2026-10-17

처음 공개한다.

### Added

- `apply` 스킬: 코드를 쓰거나 리팩터링·리뷰할 때 작업에 맞는 챕터 레퍼런스만 골라 읽고 적용한다. 프로젝트 지침·린터·다른 컨벤션 스킬과 부딪치면 그쪽을 따른다.
- 레퍼런스 `skills/apply/references/`: 전체 목차와 한 줄 요약을 담은 `index.md`, 코드 작성에 쓰이는 챕터별 요약(1~14, 16, 17장, 13장은 부록 A 포함). 서문·15장·부록 B/C·에필로그는 `index.md`에만 둔다.
- `scripts/verbatim_check.py`: 레퍼런스가 원서 문장을 연속으로 옮겨 오지 않았는지 대조한다(원서 텍스트는 저장소에 두지 않는다).
- `tests/test_references.py`: 스킬 앞머리, index와 챕터 파일의 링크, 챕터 파일 형식을 검사한다.

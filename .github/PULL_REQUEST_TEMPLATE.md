## 변경 요약

<!-- 무엇을, 왜 변경했는지 간단히 설명하세요. -->

## 대상 플러그인

- [ ] superdomain
- [ ] superglossary
- [ ] infra
- [ ] superrelease
- [ ] llm-wiki
- [ ] 저장소 공통(마켓플레이스·CI·문서)

## 테스트

- [ ] `claude plugin validate .` 통과
- [ ] 바뀐 플러그인의 테스트 통과(명령은 [CONTRIBUTING.md](../CONTRIBUTING.md#개발검증))
- [ ] `claude --plugin-dir plugins/<이름>`으로 로컬 동작 확인

## 체크리스트

- [ ] 대상 브랜치가 `main`입니다.
- [ ] 커밋 메시지가 Conventional Commits를 따르고 범위에 플러그인 이름을 적었습니다.
- [ ] 버전을 바꿨다면 그 플러그인의 `CHANGELOG.md`를 갱신했습니다.

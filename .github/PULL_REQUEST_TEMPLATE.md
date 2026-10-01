## 변경 요약

<!-- 무엇을, 왜 변경했는지 간단히 설명하세요. -->

## 대상 플러그인

- [ ] superdomain
- [ ] superglossary
- [ ] infra
- [ ] 저장소 공통(마켓플레이스·CI·문서)

## 테스트

- [ ] `claude plugin validate .` 통과
- [ ] 바뀐 플러그인의 테스트 통과(superglossary: `python3 -m unittest discover -s plugins/superglossary/tests`, infra: `bash plugins/infra/tests/run_tests.sh`)
- [ ] `claude --plugin-dir plugins/<이름>`으로 로컬 동작 확인

## 체크리스트

- [ ] 대상 브랜치가 `main`입니다.
- [ ] 커밋 메시지가 Conventional Commits를 따르고 범위에 플러그인 이름을 적었습니다.
- [ ] 버전을 바꿨다면 그 플러그인의 `CHANGELOG.md`를 갱신했습니다.

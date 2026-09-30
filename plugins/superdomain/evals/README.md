# 스킬 평가

skill-creator(`/anthropic-skills:skill-creator`)로 스킬을 평가할 때 쓰는 정의와 입력이다. 실행 결과는 저장소 밖(스크래치 폴더 등)에 둔다.

## conventions

- `conventions/evals.json`: 프롬프트 3개와 채점 기준.
- `conventions/fixture/`: 평가용 Kotlin·Spring 예제 프로젝트(주문·결제·포인트). 기존 코드에 `@Transactional`이 없어서, 트랜잭션을 어디에 거는지는 스킬이 정하게 된다.

## 실행 절차

1. 실행마다 `fixture/`를 복사하고, 실행 에이전트에게 그 복사본 안에서만 작업하게 한다. 사용자에게 물을 수 없으니 가정을 정해 진행하고, 빌드·테스트는 돌리지 않는다고 알린다.
2. 스킬 있음(또는 새 스킬·옛 스킬) 쪽 지시에만 "먼저 SKILL.md를 읽고 따른다(`${CLAUDE_SKILL_DIR}` = 스킬 폴더)" 한 줄을 더한다. 나머지 지시는 같게 둔다.
3. 하위 에이전트는 보고서 파일(.md) 쓰기가 막힐 수 있다. 요약은 파일로 쓰게 하지 말고 마지막 응답으로 받는다.
4. 끝나면 `fixture/`와의 diff를 만든다. diff와 변경 후 프로젝트를 설정 이름을 가린 A/B 폴더로 옮겨 채점자에게 넘긴다. 채점자는 코드로 확인한 사실로만 판정하고, 결과 JSON을 응답으로 돌려준다.
5. 소요 시간과 토큰은 실행 완료 알림에서 기록하고, skill-creator의 `aggregate_benchmark`로 집계한다.

# 스킬 평가

skill-creator(`/anthropic-skills:skill-creator`)로 스킬을 평가할 때 쓰는 정의와 입력이다. 실행 결과는 저장소 밖(스크래치 폴더 등)에 둔다.

## conventions

- `conventions/evals.json`: 프롬프트 3개와 채점 기준.
- `conventions/fixture/`: 평가용 Kotlin·Spring 예제 프로젝트(주문·결제·포인트). 기존 코드에 `@Transactional`이 없어서, 트랜잭션을 어디에 거는지는 스킬이 정하게 된다.

실행마다 `fixture/`를 복사해 그 안에서 작업하게 한다. 스킬 있음과 없음(또는 새 스킬과 옛 스킬)을 같은 지시로 돌리고, `fixture/`와의 diff를 채점한다.

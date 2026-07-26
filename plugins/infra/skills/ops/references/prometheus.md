# prometheus / victoria-metrics 조작 지식 (ops용)

엔드포인트는 컴포넌트 엔티티의 `endpoint`, 토큰은 keys.md 참조 위치에서 환경변수로만 (원칙 1).

## read-only (PromQL API — 전부 read-only)
- 즉시 쿼리: `curl -sf -H "Authorization: Bearer ${VM_TOKEN}" "${ENDPOINT}/api/v1/query?query=up"`
- 범위 쿼리: `.../api/v1/query_range?query=...&start=...&end=...&step=...`
- 메타: `/api/v1/labels`, `/api/v1/label/<name>/values`, `/api/v1/targets`(prometheus),
  victoria-metrics 상태: `/metrics`, vmui: `${ENDPOINT}/vmui`

## mutating
v0.1 범위에서는 없음 — admin API(tsdb delete 등)는 ops로 실행하지 않고 runbook으로 안내한다.

## 주의
- 토큰 값을 명령에 직접 붙여넣지 않는다. `VM_TOKEN` 환경변수가 없으면 사용자에게
  `export VM_TOKEN=$(...)` 준비를 요청하되 그 실행은 사용자가 한다.
- 버전 확인: `curl -sf "${ENDPOINT}/api/v1/status/buildinfo"` (victoria-metrics도 호환 제공)

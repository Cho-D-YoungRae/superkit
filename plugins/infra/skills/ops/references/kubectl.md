# kubectl 조작 지식 (ops용)

모든 명령에 `--context <엔티티의 context>`를 명시한다. 현재 컨텍스트 의존 금지 (원칙 6).

## read-only (즉시 실행)
get, describe, logs, top, events, api-resources, `rollout status`, `rollout history`, `auth can-i`

## mutating (정책 승인 파이프라인)
apply, create, delete, patch, replace, scale, edit, label, annotate, cordon, uncordon, drain, taint,
`rollout restart|undo|pause|resume`, exec(대상 상태를 바꿀 수 있으므로 mutating 취급)

## 예시
- 조회: `kubectl --context prod-k8s -n monitoring get pods`
- 변경: `kubectl --context prod-k8s -n app rollout restart deploy/api`
- 검증: `kubectl --context prod-k8s -n app rollout status deploy/api --timeout=120s`

## 주의
- `--dry-run=client|server`는 read-only 취급이지만 결과 확인 용도로만.
- 컴포넌트의 namespace는 엔티티 frontmatter의 `namespace:`를 사용한다.

# argocd 조작 지식 (ops용)

서버 지정: 컴포넌트 엔티티의 `endpoint`를 `--server <endpoint>`로 명시 (원칙 6).
인증(원칙 1 — 값 노출 금지): `--auth-token ${ARGOCD_AUTH_TOKEN}` 환경변수 참조,
또는 토큰 없이 kubectl 자격 재사용: `--port-forward --port-forward-namespace argocd --kube-context <c>`
(port-forward 모드에서도 컨텍스트를 명시한다 — 원칙 6).

## read-only
app list, app get, app history, app diff, proj list, cluster list

## mutating
app sync, app delete, app set, app patch, app rollback

## 예시
- 조회: `argocd --server argocd.example.com --auth-token ${ARGOCD_AUTH_TOKEN} app list`
- 동기화: `argocd --server argocd.example.com --auth-token ${ARGOCD_AUTH_TOKEN} app sync my-app`
- 검증: `argocd ... app get my-app` (Health/Sync 상태 확인)

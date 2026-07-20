# helm 조작 지식 (ops용)

모든 명령에 `--kube-context <엔티티의 context>`를 명시한다 (원칙 6).

## read-only
list, status, get(values|manifest|notes), history, show, search, template(렌더만)

## mutating
install, upgrade, uninstall, rollback

## 예시
- 버전 확인: `helm --kube-context prod-k8s list -A` (installed_by와 대조)
- 업그레이드: `helm --kube-context prod-k8s -n monitoring upgrade vm vm/victoria-metrics-single --version 0.9.1`
- 검증: `helm --kube-context prod-k8s -n monitoring status vm` + 해당 파드 rollout status

## 주의
- upgrade 전 `helm ... get values`로 현재 값 확인, `--reuse-values` 여부를 사용자와 확인.
- 값 파일에 시크릿이 필요하면 `sops exec-env` 또는 `--set-file <경로>` 참조 실행만.

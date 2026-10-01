# 인프라 하네스

이 저장소는 인프라의 지식(인벤토리)·기록(변경/의사결정)·조작(진입점)을 담는 **중앙 하네스**다.
infra 플러그인 스킬(init/register/lookup/connect/ops/change/decide/sync/audit/secrets)이 이 저장소를 읽고 쓴다.
이 저장소는 IP·토폴로지·접근 정보가 담긴 민감 문서다 — **외부 비공개 필수**.

> **세션은 이 디렉터리(하네스 루트)에서 여세요.** `secrets/` 읽기 차단은
> `.claude/settings.json`에 있는데, 이 파일은 세션을 연 디렉터리의 `.claude/`에서만
> **부모 폴백 없이** 로드된다. 하위 디렉터리(`inventory/` 등)에서 세션을 열면 스킬은
> 상향 탐색으로 하네스를 찾아 정상 동작하지만 차단은 걸리지 않는다.
> 이 하네스가 git 저장소라면 `.claude/settings.local.json`이 저장소 루트에서 로드되어
> 그 경우를 덮는다 — **이 파일을 지우거나 `.gitignore`에 넣지 마세요.**

## 핵심 규약

- 시크릿 값은 어떤 파일에도 적지 않는다. 위치 참조만(access/keys.md). 사용은 참조 실행
  (`ssh -i <경로>`, `${VAR}`, `sops exec-env`, `op run`)만 (원칙 1).
- `secrets/`는 읽기 금지 구역이다(.claude/settings.json의 deny). 보관 정책은 harness.yaml의
  sharing·secrets_mode를 따른다 (원칙 2).
- 조작 명령은 항상 엔티티에 기록된 `--context`/`--profile`을 명시한다 (원칙 6).
- mutating 작업 후에는 changes/에 기록을 남긴다 — 롤백 방법 필수 (원칙 7·9).
- 상태의 SSOT는 실제 인프라·terraform state·config 레포다. 하네스는 색인·맥락·진입점만 담는다 (원칙 4).

## 스킬 사용

자연어로 요청하면 된다: "prod DB 어떻게 붙어?"(lookup) · "이 클러스터 파드 상태 봐줘"(ops) ·
"방금 작업 기록 남겨줘"(change) · "문서랑 실제 상태 맞아?"(sync) · "하네스 점검해줘"(audit) ·
"서버 등록해줘"(register) · "kubeconfig 다시 잡아줘"(connect).

## 하네스 변경 이력

- {{date}}: init으로 생성

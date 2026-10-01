---
name: ops
description: 하네스 엔티티(서버·k8s 클러스터·컴포넌트)를 대상으로 kubectl·helm·argocd·PromQL·클라우드 CLI 명령을 context/profile 명시로 실행한다. "이 클러스터 프로메테우스 버전 확인해줘", "파드 상태 봐줘", "디플로이 재시작해줘" 같은 실제 조회·조작 요청에 사용. read-only는 즉시, mutating은 env 정책에 따라 승인 후 실행하고 변경 기록 초안을 남긴다. 위치·접속법 질문만이면 lookup, 접근 자체가 안 되면 connect.
---

# ops — 인프라 직접 제어

하네스 엔티티(서버·k8s 클러스터·컴포넌트)를 대상으로 kubectl·helm·argocd·PromQL·클라우드
CLI 명령을 실제로 실행하는 스킬이다. "파드 상태 봐줘", "이 클러스터 프로메테우스 버전
확인해줘", "디플로이 재시작해줘"처럼 조회·조작을 직접 수행해야 할 때 쓴다. 위치·접속
방법만 궁금하면 lookup, 애초에 로컬 접근 자체가 구성돼 있지 않으면 connect로 먼저
재구성해야 한다 — ops는 항상 "이미 구성된 접근으로 실제 명령을 실행하는" 작업만 한다.

## 1. 적용 원칙

이 스킬이 반드시 지키는 원칙은 다음 여섯 가지다.

- **원칙 1 — 시크릿 값의 컨텍스트 유입 금지, 참조 실행만**: 명령에 시크릿이 필요하면
  값을 읽거나 echo·cat으로 노출하지 않고 항상 참조 실행 형태(`ssh -i <경로>`, `${VAR}`,
  `sops exec-env <파일> '<명령>'`, `op run -- <명령>`)로만 구성한다.
- **원칙 4 — 하네스는 색인이지 엔진이 아니다**: 명령 실행 결과(실제 상태)가 SSOT이고
  하네스 문서는 그 명령을 조립하는 데 필요한 좌표(context/profile/endpoint)만 제공한다.
  실행 결과를 하네스 문서에 맞춰 해석하지 말고 있는 그대로 보고한다.
- **원칙 6 — 암묵 컨텍스트 금지**: 모든 명령에 `--context`/`--kube-context`/`--profile`을
  명시한다. 현재 kubectl 컨텍스트나 기본 aws profile에 의존하는 명령은 절대 생성하지
  않는다.
- **원칙 7 — 읽기/변경 분리**: read-only 명령은 자유롭게 즉시 실행한다. mutating 명령은
  반드시 §4~§7의 파이프라인(정책 적용 → 실행 → 검증 → 기록)을 거친다.
- **원칙 8 — 정책은 데이터**: mutating 승인 여부는 스킬 본문이 아니라 `harness.yaml`의
  `policies.mutating.<env>` 값으로 결정한다. 정책이 바뀌어도(예: dev를 confirm으로 강화)
  `harness.yaml`만 고치면 되고 이 스킬을 수정할 필요가 없다.
- **원칙 9 — 기록은 작업의 부산물**: mutating 작업이 끝나면 그 사실 자체가 change 스킬
  호출의 트리거가 된다. 기록 여부를 사용자에게 다시 물어보지 않고 절차의 일부로 자동
  수행한다.

## 2. 대상 해석

1. 사용자 요청에서 대상 엔티티 id를 식별한다. 이름이 모호해 후보가 여럿이면(예: "prod
   디비" → `prod-db-01`, `prod-db-02`) lookup과 같은 방식으로 후보를 표로 제시해 사용자가
   하나를 고르게 한다.
2. 엔티티 type에 따라 명령 조립에 필요한 좌표를 해석한다.
   - **server**: 엔티티가 참조하는 `provider`의 `cli_profile`과 엔티티 자신의 `access`
     필드(ssh 접속 정보)를 사용한다.
   - **k8s-cluster**: 엔티티 자신의 `context` 필드를 사용한다.
   - **component**: frontmatter에 env가 없다 — `runs_on`이 가리키는 server/k8s-cluster
     엔티티를 따라가 그 엔티티의 env와 context(k8s-cluster) 또는 cli_profile(server)를
     해석한다(스펙 D5). 여기에 component 자신의 `endpoint`/`access`/`namespace`를 더해
     최종 명령을 구성한다. 예: `victoria-metrics`(component, `runs_on: prod-k8s`,
     `namespace: monitoring`) → `runs_on` 추적으로 `prod-k8s`의 `context: prod-k8s`를
     얻어 `kubectl --context prod-k8s -n monitoring ...`을 조립한다.

## 3. read/mutating 분류

명령이 read-only인지 mutating인지는 도구별로 `references/`의 분류표를 기준으로
판정한다 — 임의로 판단하지 않는다. **분류가 애매한 명령(표에 없는 서브커맨드, 새로운
플래그 조합 등)은 항상 mutating으로 취급**해 안전한 쪽으로 넘어간다.

## 4. 정책 적용

mutating으로 분류된 명령은 실행 전에 `harness.yaml`의 `policies.mutating.<대상 env>`를
확인한다.

- `allow` → 그대로 진행(§5).
- `confirm` → `AskUserQuestion`으로 **대상 id, env, 실행할 전체 명령**(옵션까지 그대로)을
  보여주고 승인을 받은 뒤에만 진행한다. 승인 UX에 `AskUserQuestion`을 쓸 수 없는 환경이면
  텍스트 질문으로 폴백한다.
- **정책에 해당 env 키가 아예 없으면 `confirm`으로 취급한다**(스펙 D4) — 정의되지 않은
  환경을 `allow`처럼 조용히 진행하지 않는다.

## 5. 실행

모든 명령에 `--context`/`--kube-context`/`--profile`을 명시한다(원칙 6, references의
"context/profile 명시 형태" 참고). 시크릿이 필요하면 참조 실행만 구성한다 —
`ssh -i <경로>`, 환경변수 `${VAR}`, `sops exec-env <파일> '<명령>'`, `op run --
<명령>`처럼 값이 명령 실행 경로로만 흐르는 형태만 쓴다. 값을 변수에 담아 echo나 cat으로
화면에 출력하는 형태는 어떤 이유로도 만들지 않는다.

## 6. 검증

mutating 명령 실행 직후에는 항상 대응하는 read-only 명령으로 결과를 검증한다 —
`kubectl ... rollout status`, `helm ... status` + 파드 rollout status, `argocd ... app
get`(Health/Sync 확인), 헬스체크 endpoint 호출 등. 검증 결과가 실패·비정상이면 그 사실을
숨기지 않고 그대로 보고한 뒤 §7의 기록에도 실패로 남긴다.

## 7. 기록

mutating 명령이 끝나면 **성공이든 실패든** change 스킬의 절차를 그 자리에서 자동으로
호출해 `changes/`에 초안을 남긴다. "기록할까요?"라고 다시 묻지 않는다 — 실행한 명령
(context/profile 포함 그대로), 결과, §6의 검증 내용을 change에 그대로 전달한다. 롤백
방법이 그 자리에서 확정되지 않으면 change 절차가 사용자에게 직접 묻는다.

## 8. references 로드

명령을 조립하기 전에 해당 도구의 조작 지식을 먼저 읽는다 — kubectl 작업은
`references/kubectl.md`, helm 작업은 `references/helm.md`, argocd 작업은
`references/argocd.md`, PromQL/victoria-metrics 조회는 `references/prometheus.md`.
각 reference는 그 도구의 read-only/mutating 분류표, context/profile 명시 형태, 참조
실행 예시, 검증 명령을 담고 있으므로 §3~§6의 판단·조립 근거로 그대로 쓴다.

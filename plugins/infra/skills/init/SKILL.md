---
name: init
description: 인프라 하네스 저장소(서버·k8s·컴포넌트 인벤토리 + 변경기록 + 정책)를 새로 스캐폴딩하거나 기존 하네스를 점검·확장한다. "인프라 하네스 만들어줘", "인프라 관리 시작하고 싶어", "하네스 초기화" 같은 요청에 사용. 로컬 CLI를 스캔해 확인 인터뷰 후 골격만 생성한다. 개별 서버·컴포넌트 등록은 register, 정합성 검증만 원하면 audit.
---

# init — 인프라 하네스 스캐폴딩

인프라 하네스(서버·k8s 클러스터·컴포넌트 인벤토리 + 변경기록 + 정책을 담는 중앙 저장소 1개)를
처음 만들거나, 이미 있는 하네스를 점검·보완한다. **골격까지만 책임진다** — 서버·컴포넌트
전수 등록을 강요하지 않는다(콜드 스타트 마찰 방지). 개별 등록은 register, 등록 없이 정합성만
확인하고 싶다면 audit을 안내한다.

## 1. 적용 원칙

이 스킬이 반드시 지키는 원칙(전 스킬 공통 원칙 중 init에 해당하는 항목)은 다음 네 가지다.

- **원칙 1 — 시크릿 값의 컨텍스트 유입 금지**: 자동 발견 단계를 포함해 어떤 순간에도
  `~/.aws/credentials`, kubeconfig 같은 시크릿이 담긴 raw 파일을 읽지 않는다.
  `aws configure list-profiles`, `kubectl config get-contexts`, `ssh-keygen -lf` 처럼
  값이 아니라 **메타데이터만 출력하는 명령**만 사용한다.
- **원칙 2 — 시크릿 저장 정책은 공유 모드에 종속**: `sharing`이 `local`이 아니면(`git`,
  `shared-drive`) `secrets_mode: plaintext`는 애초에 선택지에 올리지 않는다 — `none` 또는
  `encrypted`만 유효하다. 이 필터링은 확인 인터뷰(§4)에서 기계적으로 적용한다.
- **원칙 3 — 묻기 전에 스캔**: profile·context·설치된 CLI처럼 로컬에서 확인 가능한 정보는
  먼저 스캔(§3)하고, 그 결과를 근거로 확인 질문(§4)을 한다. 사용자의 기억이나 처음부터의
  타이핑에 의존하지 않는다.
- **원칙 8 — 정책은 데이터**: `sharing`·`secrets_mode`·`environments`·`policies`·`hooks`는
  전부 `harness.yaml`에 데이터로 기록한다. 이후 정책이 바뀌어도 스킬 본문이 아니라
  `harness.yaml` 값만 바뀌면 된다.

## 2. 기존 하네스 감지

가장 먼저, cwd에서 상위 디렉터리 방향으로 `harness.yaml`을 탐색한다(다른 모든 스킬과 공유하는
하네스 발견 규약과 동일한 방식). 결과에 따라 분기한다.

- **발견됨** → 새 하네스를 만들지 않는다. 대신:
  1. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py --root <발견된 경로>` 를 실행한다.
  2. 실패·경고를 그대로 보고한다.
  3. 표준 구조(디렉토리 `providers/ inventory/ inventory/components/ access/ changes/
     decisions/ runbooks/`, `.claude/settings.json`, `.gitignore`, `CLAUDE.md`)와 실제
     디렉토리를 비교해 누락된 디렉토리·템플릿이 있으면 "감사/확장 모드"로 보완 생성을
     제안한다. **기존 파일·데이터는 절대 덮어쓰지 않는다.**
- **미발견** → §3~§6의 "신규 생성" 절차로 진행한다.

## 3. 자동 발견 (메타데이터만)

아래 명령만 사용한다. CLI마다 먼저 `command -v <cli>`로 설치 여부를 확인하고, 설치된 것만
다음 명령을 실행한다(미설치 시 처리는 §7 참고).

- `command -v aws` → `aws configure list-profiles`
- `command -v gcloud` → `gcloud config configurations list`
- `command -v kubectl` → `kubectl config get-contexts -o name`
- `~/.ssh/*.pub` 각 파일마다 `ssh-keygen -lf <파일>` (fingerprint만 추출 — 개인키 파일은
  절대 열지 않는다)
- `command -v terraform` / `ansible` / `docker` / `helm` / `argocd` → **설치 여부만** 기록
  (이 다섯은 profile 개념이 없어 추가 발견 명령이 없다 — 이후 register/ops/connect가
  참고하는 사실 정보일 뿐)

**금지 명령 (절대 실행하지 않는다)**: `cat ~/.aws/credentials`, `cat ~/.kube/config` 등
자격 증명·kubeconfig **raw 파일을 여는 모든 명령**. 값이 궁금해지는 어떤 상황에서도 이
파일들을 직접 읽지 않는다(원칙 1).

## 4. 확인 인터뷰

자동 발견 결과를 근거로 `AskUserQuestion`으로 한 턴에 2~3개씩 묻는다. 다뤄야 할 결정은
아래 6가지다.

1. 발견된 profile/context 중 하네스에서 관리할 대상 선택
2. 자동 발견되지 않은 provider(온프렘 등)를 수동으로 추가할지
3. `sharing`(local / git / shared-drive) + `secrets_mode` — **원칙 2의 유효 조합만
   선택지로 제시**한다: `sharing: local`이면 none/plaintext/encrypted 모두 제시하고,
   `git`·`shared-drive`면 `plaintext`를 선택지에서 빼고 none/encrypted만 제시한다.
   `secrets_mode: encrypted`를 선택하면 이어서 팀원의 age **공개키**와 **recovery
   수신자**(조직 복구용, 필수 — D11)를 물어 `secrets_recipients`를 채운다. age 공개키는
   비밀이 아니므로 그대로 물어도 안전하다(개인키와 혼동하지 않는다)
4. `environments` 목록 확정(기본 제안: `prod`, `stage`, `dev` — 필요에 맞게 가감)
5. IaC 레포 등록 여부(terraform 레포 URL 등, 없으면 생략 가능)
6. `hooks.change_reminder` 활성화 여부(기본값 `true` 권장)

## 5. 스캐폴딩

`${CLAUDE_PLUGIN_ROOT}/templates/`의 파일을 복사하고 `{{변수}}` 자리를 인터뷰에서 확정된
값과 오늘 날짜로 채운다(치환 스크립트는 없다 — 이 단계에서 직접 채워 넣는다).

- 디렉토리: `providers/`, `inventory/`, `inventory/components/`, `access/`, `changes/`,
  `decisions/`, `runbooks/` — 전부 빈 채로 만든다(서버·컴포넌트·키 항목 등록은 register 몫).
- 선택·추가된 provider마다 `providers/<id>.md` (`provider.md` 템플릿 — 온프렘처럼 해당
  없는 필드는 템플릿 주석 지시대로 그 줄을 삭제).
- `harness.yaml` (`harness.yaml` 템플릿 — `sharing`/`secrets_mode`/`environments`/
  `iac.repos`/`policies.mutating`/`hooks.change_reminder` 채움. `policies.mutating`에
  없는 env는 자동으로 `confirm` 취급되므로 전 환경을 다 채울 필요는 없다).
  `secrets_mode: encrypted`면 주석 처리된 `secrets_format`/`secrets_recipients` 블록의
  주석을 해제하고 §4에서 확인한 팀원 age 공개키 + recovery 수신자로 채운다(D11) —
  값(개인키·시크릿)은 여기서 만들지 않고 공개키만 기록한다.
- `CLAUDE.md` (`harness-CLAUDE.md` 템플릿).
- `.claude/settings.json` (`settings.json` 템플릿을 **그대로** 복사 — `Read(/secrets/**)`
  와 `Read(./secrets/**)` deny 규칙을 병기해 앵커 문법 차이에 대비).
- `.claude/settings.local.json` (`settings.local.json` 템플릿을 **그대로** 복사 — 같은 deny
  규칙을 한 벌 더 둔다). 사본이 아니라 **다른 구멍을 메우는 것**이다: `settings.json`은
  cwd의 `.claude/`에서만 **부모 폴백 없이** 로드되는데, 하네스 발견은 상향 탐색이므로(D1)
  하네스 하위 디렉터리(`inventory/` 등)에서 세션을 열면 스킬은 동작하는데 차단은 사라진다.
  `settings.local.json`은 **git 저장소 루트에서** 로드되므로 그 경우를 덮는다.
  - `sharing: git`이면 이 파일을 **커밋 대상에 포함**한다고 사용자에게 알린다 — 이름은
    `local`이지만 여기서는 팀 전체가 같은 보호를 받게 하려는 의도적 선택이다.
    `.gitignore`에 `.claude/settings.local.json`을 넣지 않는다.
  - 하네스가 git 저장소가 **아니면** 이 파일은 로드되지 않는다. 이때는 "세션을 하네스
    루트에서 열어야 `secrets/` 차단이 걸린다"고 마무리 안내(§7)에서 명시한다.
- `.gitignore` (`gitignore` 템플릿 — `secrets_mode: encrypted`면 `!secrets/*.age` /
  `!secrets/*.sops.yaml` 재포함 줄의 주석을 해제).
- `secrets_mode ≠ none`이면 `secrets/` 디렉토리를 빈 채로 생성한다. register도 원칙 1에
  따라 시크릿 값 자체는 쓰지 않는다 — register가 하는 일은 `access/keys.md`와 엔티티의
  `access` 필드에 종류·fingerprint·위치 참조 같은 메타데이터만 기록하는 것이며, 실제
  시크릿 파일은 사용자가 이 디렉토리에 직접 둔다.
- `decisions/ADR-0001-harness-init.md` (`adr.md` 템플릿 — 이번 인터뷰의 결정과 근거를
  기록: `sharing`/`secrets_mode` 선택 이유, `environments`, IaC 레포 등록 여부,
  `change_reminder` 여부).

`configs/`는 만들지 않는다(원칙 5 — `managed_by: manual`인 엔티티가 실제로 생겨 설정
보관이 필요해지는 시점에 그 스킬이 만든다).

## 6. 마무리

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py --root <새로 만든 하네스 경로>` 를 1회
실행해 결과를 그대로 보고한다(정상 스캐폴딩이면 등록된 엔티티가 없으므로 보통 실패 0건).
이어서 "서버·컴포넌트는 register로 등록하세요"라고 안내한다. **지금 전부 등록하라고
강요하지 않는다** — 골격만 마련하는 것이 이 스킬의 설계 의도다.

`secrets_mode: encrypted`로 스캐폴딩했다면 `secrets_recipients`를 채운 것만으로는 아직
암호화가 동작하지 않는다 — `secrets` 스킬 **§6(신규 시크릿 생성·최초 암호화)**로 넘어가
`.sops.yaml` 생성과 최초 암호화를 진행하라고 안내한다(이 스킬은 골격(harness.yaml의
수신자 매니페스트)만 준비하며, 실제 `.sops.yaml`·암호화 파일 생성이나 시크릿 값 생성은
하지 않는다).

## 7. 에러 처리

자동 발견(§3) 단계에서 특정 CLI(`aws`/`gcloud`/`kubectl`/`terraform`/`ansible`/`docker`/
`helm`/`argocd`)가 없으면 해당 provider·도구의 자동 발견만 건너뛰고 나머지는 계속
진행한다. 건너뛴 대상은 확인 인터뷰(§4)에서 "자동 발견되지 않음 — 수동으로
추가하시겠습니까?"로 안내해, CLI가 없는 온프렘 등의 환경도 등록 경로를 잃지 않게 한다.

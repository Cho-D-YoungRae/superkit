# infra

인프라의 **지식(인벤토리) · 기록(변경/의사결정) · 조작(직접 제어)**을 담당하는 "인프라 하네스"를
구성·운영하는 Claude Code 플러그인. 스킬 9종(init/register/lookup/connect/ops/change/decide/
sync/audit), 엔티티 템플릿, 검증 스크립트, hook으로 구성된다.

## 목차

1. [개요](#1-개요)
2. [설치](#2-설치)
3. [시작하기](#3-시작하기)
4. [불변 원칙과 하네스 발견 규약](#4-불변-원칙과-하네스-발견-규약)
5. [스킬](#5-스킬)
6. [테스트](#6-테스트)
7. [수동 검증 체크리스트](#7-수동-검증-체크리스트)

## 1. 개요

**플러그인**과 **하네스 인스턴스**는 서로 다른 것이다.

- **플러그인(이 저장소, `infra`)** = 재사용 도구. `.claude-plugin/plugin.json`, `skills/`,
  `templates/`, `scripts/`, `hooks/`, `tests/`로 구성되며, 코드·문서 그 자체는 어떤 인프라
  정보도 담지 않는다.
- **하네스 인스턴스** = 실제 데이터가 담기는 전용 저장소 1개(`harness.yaml` + `CLAUDE.md` +
  인벤토리·변경기록·의사결정 등). 이 플러그인의 `init` 스킬이 그 저장소를 스캐폴딩한다.
  저장소 이름은 자유(예: `infra-workspace`)이며 플러그인 이름과 무관하다.

인프라는 특정 프로젝트에 종속되지 않고 여러 프로젝트를 가로지르는 대상이므로, 하네스는
프로젝트별로 여러 개 두지 않고 **중앙 1개**만 운영한다. 저장·공유 방식(로컬 전용 / git /
공유 드라이브)은 자유이지만, 하네스에는 IP·토폴로지·접근 정보 같은 민감 정보가 담기므로
**외부 비공개는 필수**다.

대상 환경은 온프렘 · AWS · GCP 혼합이며, 앱/DB/모니터링 서버, k8s 클러스터, argocd·
prometheus·victoria-metrics 같은 설치 컴포넌트를 다룬다.

## 2. 설치

### 개발 모드

```bash
claude --plugin-dir /path/to/infra
```

`/path/to/infra`는 `.claude-plugin/plugin.json`이 있는 이 저장소의 절대 경로다. 같은 이름의
설치된 플러그인이 있어도 `--plugin-dir`로 띄운 로컬 버전이 우선한다.

### marketplace로 배포하는 경우

이 플러그인을 사내/개인 marketplace에 등록해 배포한다면, 사용자는 저장소를 직접 내려받지
않고 세션 안에서 `/plugin` 명령으로 marketplace 추가와 `infra` 플러그인 설치를 진행한다.
(marketplace 자체를 구성하는 작업은 이 저장소의 범위 밖이다.)

### 개발 루프

스킬·스크립트·hooks 파일을 수정한 뒤에는 세션을 새로 시작하지 않고 세션 안에서
`/reload-plugins`를 실행해 변경 사항을 반영한다.

### 요구 사항

`scripts/`와 `hooks/scripts/`는 python3 표준 라이브러리만 사용한다(PyYAML 등 외부 패키지
설치 불필요). PATH에 `python3`만 있으면 된다.

## 3. 시작하기

1. 하네스로 쓸 **빈 디렉토리**를 만들고 그 안에서 세션을 연다(기존 프로젝트 디렉토리가
   아니라 별도 디렉토리를 쓴다 — 하네스는 중앙 1개다).

   ```bash
   mkdir ~/infra-workspace && cd ~/infra-workspace
   claude --plugin-dir /path/to/infra
   ```

2. 대화창에 "인프라 하네스 만들어줘"라고 요청한다. `init` 스킬이 로컬에 설치된 CLI를
   자동으로 스캔한 뒤 확인 인터뷰를 거쳐 `harness.yaml`·`CLAUDE.md`·`providers/` 등 하네스
   골격을 만든다.
3. 서버·클러스터·컴포넌트는 `register`로 등록한다: "이 서버 등록해줘", "클러스터 추가해줘"
   또는 목록·스프레드시트 텍스트를 붙여넣어 일괄 등록도 가능하다.
4. 이후로는 스킬 이름을 몰라도 자연어로 요청하면 클로드가 description을 보고 알맞은 스킬을
   스스로 고른다. 대표 예시:

   | 발화 예시 | 자동 선택되는 스킬 |
   |---|---|
   | "인프라 하네스 만들어줘" | init |
   | "이 서버 등록해줘" | register |
   | "prod DB 어떻게 붙어?" | lookup |
   | "이 클러스터 kubeconfig 잡아줘" | connect |
   | "이 클러스터 프로메테우스 버전 확인해줘" | ops |
   | "방금 작업 기록 남겨줘" | change |
   | "이 결정 ADR로 남겨줘" | decide |
   | "문서랑 실제 상태 맞는지 확인해줘" | sync |
   | "하네스 점검해줘" | audit |

   각 스킬은 `/infra:<이름>`(예: `/infra:init`)으로 직접 호출할 수도 있지만, 이는 보조
   경로다 — 기본 사용 형태는 자연어 대화다.

## 4. 불변 원칙과 하네스 발견 규약

infra의 모든 스킬은 아래 10개 원칙을 위반할 수 없다(각 SKILL.md에 해당 원칙 번호가
명시돼 있다). 이 중 원칙 1·2는 이 플러그인이 존재하는 이유에 해당한다.

**원칙 1 — 시크릿 값의 컨텍스트 유입 금지, 참조 실행만.** 클로드는 키·토큰·인증서의 값을
어떤 경우에도 읽거나 출력하지 않는다. 사용은 항상 `ssh -i <경로>`, 환경변수 `${VAR}`,
`sops exec-env`, `op run -- <명령>`처럼 값이 명령 실행 경로로만 흐르는 참조 실행 형태로
한다. 자동 발견 단계에서도 `~/.aws/credentials`·kubeconfig 원본 파일은 읽지 않고,
`aws configure list-profiles`, `kubectl config get-contexts`, `ssh-keygen -lf` 같은
메타데이터만 출력하는 명령만 쓴다.

**원칙 2 — 시크릿 저장 정책은 공유 모드에 종속.** 값을 하네스 안에 둘 수 있는지는
`harness.yaml`의 `sharing`에 따라 결정된다: `local`(비공유)이면 `secrets/`에 평문 보관을
허용하고, 공유(`git`/`shared-drive`)면 암호화 저장(age/SOPS)만 허용하며, 공유+평문 조합은
금지한다. init이 하네스의 `.claude/settings.json`에 `secrets/` 읽기 차단(`permissions.deny`)을
설정해 이를 기계적으로 강제한다 — 참조 실행은 되고 Read(읽기)만 막힌다.

나머지 8개 원칙 요약:

| 원칙 | 요약 |
|---|---|
| 3 | 묻기 전에 스캔 — 로컬에서 확인 가능한 정보(CLI 설치·profile·context·키 fingerprint)는 스캔 후 확인 질문 |
| 4 | 하네스는 지도 + 조종석이지 엔진이 아니다 — 상태의 SSOT는 실제 인프라·terraform state |
| 5 | `managed_by`는 엔티티 속성 — 하네스 전역 IaC 모드가 아니라 엔티티마다 terraform/manual 표기 |
| 6 | 암묵 컨텍스트 금지 — 모든 조작 명령에 `--context`/`--profile`을 명시, 현재 컨텍스트·기본 profile 의존 금지 |
| 7 | 읽기/변경 분리 — read-only는 즉시 실행, mutating은 대상 확인→실행→검증→기록 파이프라인 |
| 8 | 정책은 데이터 — 환경별 mutating 정책·공유 모드·hook 동작은 `harness.yaml`에 두고 스킬이 읽어 적용 |
| 9 | 기록은 작업의 부산물 — `changes/`가 변경 이력의 SSOT (`decisions/`는 ADR 보관소) |
| 10 | 스킬은 description으로 자동 선택 가능해야 한다 — 슬래시 직접 호출은 보조 경로 |

### 하네스 발견 규약 (스펙 D1)

모든 스킬과 hook은 **하네스 안에서만** 동작한다: cwd에서 상위 디렉터리 방향으로
`harness.yaml`을 상향 탐색해 `HARNESS_ROOT`를 정한다.

- **발견됨** → 해당 스킬의 절차를 그대로 진행한다.
- **미발견** → `init`만 "새 하네스 생성 모드"로 진입한다. 그 외 스킬(register/lookup/
  connect/ops/change/decide/sync/audit)은 "하네스 디렉터리에서 세션을 열거나 init으로
  하네스를 먼저 생성하세요"라고 안내한 뒤 중단한다. hook(`change_reminder`)은 하네스를
  찾지 못하면 조용히 통과(exit 0)한다 — 하네스 밖 프로젝트 작업에는 어떤 형태로도
  개입하지 않는다.
- 전역 포인터 파일이나 사용자 설정은 건드리지 않는다 — 오직 cwd 기준 상향 탐색만 쓴다.

## 5. 스킬

| 이름 | 역할 | 대표 발화 |
|---|---|---|
| init | 하네스 저장소를 새로 스캐폴딩하거나 기존 하네스를 점검·확장한다 | "인프라 하네스 만들어줘" |
| register | 서버·k8s 클러스터·컴포넌트·provider·키 메타데이터를 등록해 엔티티 파일을 만든다 | "이 서버 등록해줘" |
| lookup | 인벤토리에서 접속 방법·위치·구성 정보를 조회해 답한다(키는 값이 아니라 위치 참조로) | "prod DB 어떻게 붙어?" |
| connect | 하네스에 기록된 `access_recipe`를 실행해 로컬 접근(kubeconfig·ssh)을 재구성한다 | "이 클러스터 kubeconfig 잡아줘" |
| ops | kubectl·helm·argocd·PromQL·클라우드 CLI 명령을 context/profile 명시로 실제 실행한다 | "이 클러스터 프로메테우스 버전 확인해줘" |
| change | 변경 내역을 `changes/`에 날짜 기반으로 기록한다(롤백 방법 필수 확인) | "방금 작업 기록 남겨줘" |
| decide | 기술 의사결정을 ADR 형식으로 `decisions/`에 기록한다 | "이 결정 ADR로 남겨줘" |
| sync | 인벤토리 문서와 실제 상태(클라우드 인스턴스·k8s 노드·helm 릴리스)를 read-only로 대조해 drift를 보고한다 | "문서랑 실제 상태 맞는지 확인해줘" |
| audit | 하네스 문서 자체의 정합성(스키마·참조·시크릿·정책·만료)을 검증한다 | "하네스 점검해줘" |

`ops`는 도구별 조작 지식을 `skills/ops/references/{kubectl,argocd,prometheus,helm}.md`로
분리해 명령을 조립하기 전에 필요한 것만 불러온다.

## 6. 테스트

```bash
bash tests/run_tests.sh
```

`tests/fixtures/harness-ok`(정상 하네스)·`tests/fixtures/harness-bad`(오염 하네스)·
`tests/fixtures/harness-off`(hook 비활성화 검증용) 세 fixture를 대상으로 다음을 자동
검증한다.

- `scripts/audit.py`의 기대 결과(스키마/참조/시크릿 패턴/정책 조합/만료 경고 각 항목의
  통과·실패)
- `hooks/scripts/change_reminder.py`의 케이스(mutating 매치 / read-only 제외 / `--dry-run`
  제외 / `hooks.change_reminder: false` / 하네스 밖에서 실행)
- `scripts/sync_snapshot.py`의 문서 스냅샷 파서·diff 로직(모의 수집 데이터 주입)

## 7. 수동 검증 체크리스트

`tests/run_tests.sh`는 파서·스크립트 로직만 자동 검증한다. 대화형 UX와 실제 인프라 대상
동작은 아래를 사람이 직접 확인한다(스펙 §12 시나리오 9 — audit의 AKIA 검출·무효 정책
조합·만료 임박·깨진 참조 검증 — 는 위 자동 테스트의 fixture로 이미 전부 커버되므로 이
체크리스트에서는 제외한다).

- [ ] 1. 빈 디렉토리에서 세션을 열고 "인프라 하네스 만들어줘"라고 요청하면 `init`이 로컬
      CLI·profile·context·ssh fingerprint를 자동 발견한 뒤 확인 인터뷰를 거쳐 하네스
      골격을 스캐폴딩한다.
- [ ] 2. `init` 인터뷰가 `sharing`/`secrets_mode`를 질문해 `harness.yaml`과
      `ADR-0001-harness-init.md`에 결정을 기록하고, 선택한 모드에 맞는 구성(예:
      `secrets_mode: encrypted`면 `.gitignore`의 암호문 재포함 규칙 해제, `none`이면
      `secrets/` 디렉토리 미생성)이 실제로 반영된다.
- [ ] 3. init부터 register·ops까지 전 과정에서 `~/.aws/credentials`·kubeconfig 등 raw
      자격증명 파일을 읽지 않고, 시크릿 값이 대화 컨텍스트에 그대로 노출되지 않는다.
- [ ] 4. 하네스 안에서 `secrets/` 아래 파일을 Read 도구로 열면 `.claude/settings.json`의
      deny 규칙에 의해 차단되고, 반대로 `ssh -i <경로>`·환경변수 `${VAR}` 참조 실행은
      정상 동작한다.
- [ ] 5. `register`로 대화형 등록(server/k8s-cluster/component 등 3종 이상)과 텍스트
      붙여넣기 일괄 등록이 모두 정상 동작한다.
- [ ] 6. `lookup`에 "prod DB 접속 방법"을 물으면 값이 아니라 위치 참조와 실행 가능한 명령
      형태로 정확히 응답한다.
- [ ] 7. `ops`에서 read-only 명령은 즉시 실행되고, prod 등 mutating 명령은 정책에 따라
      승인을 받은 뒤 실행되며, 종료 후 `change` 초안이 자동 생성되고, 모든 명령에
      `--context`/`--profile`이 명시된다.
- [ ] 8. `sync`를 실제 인프라 대상으로 실행해 문서 누락 / 유령 / 버전 불일치 / 확인 불가
      4구획 diff가 올바르게 보고된다.
- [ ] 10. `harness.yaml`의 `hooks.change_reminder`를 true/false로 바꿔가며 mutating 명령
      실행 후 리마인드가 각각 뜨고/뜨지 않는지 스모크 테스트한다.
- [ ] 11. "prod DB 어떻게 접속해?" → `lookup`, "이 클러스터 프로메테우스 버전
      확인해줘" → `ops`, "방금 작업 기록 남겨줘" → `change`처럼 스킬 이름을 언급하지 않은
      자연어만으로 올바른 스킬이 자동 선택된다.

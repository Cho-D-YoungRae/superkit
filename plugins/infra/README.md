# infra

인프라의 **지식(인벤토리) · 기록(변경/의사결정) · 조작(직접 제어)**을 담당하는 "인프라 하네스"를
구성·운영하는 Claude Code 플러그인. 스킬 10종(init/register/lookup/connect/ops/change/decide/
sync/audit/secrets), 엔티티 템플릿, 검증 스크립트, hook으로 구성된다.

## 빠른 시작

```bash
git clone <저장소 URL> ~/infra-plugin
mkdir -p ~/infra-workspace && cd ~/infra-workspace
claude --plugin-dir ~/infra-plugin
# 대화창: "인프라 하네스 만들어줘" → 이후 자연어로 등록·조회·조작
```

설치 상세와 요구 사항은 [3. 설치](#3-설치)를 참고한다.

## 목차

1. [개요](#1-개요)
2. [하네스 구조와 엔티티 모델](#2-하네스-구조와-엔티티-모델)
3. [설치](#3-설치)
4. [시작하기](#4-시작하기)
5. [유즈케이스](#5-유즈케이스)
6. [불변 원칙과 하네스 발견 규약](#6-불변-원칙과-하네스-발견-규약)
7. [스킬](#7-스킬)
8. [테스트](#8-테스트)
9. [수동 검증 체크리스트](#9-수동-검증-체크리스트)
10. [안전성 FAQ](#10-안전성-faq)
11. [마이그레이션](#11-마이그레이션)
12. [트러블슈팅](#12-트러블슈팅)
13. [기여·설계 문서](#13-기여설계-문서)
14. [라이선스](#14-라이선스)

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

## 2. 하네스 구조와 엔티티 모델

`init`이 스캐폴딩하는 하네스 저장소의 골격은 다음과 같다(엔티티 파일은 `register`로 채운다).

```
<하네스 저장소>/                # 이름 자유, 외부 비공개 필수
├── harness.yaml               # 정책 데이터 — sharing/secrets_mode/environments/policies/hooks(+secrets_recipients, D11)
├── CLAUDE.md                  # 하네스 소개·규약(플러그인의 CLAUDE.md와 다름)
├── .claude/settings.json      # secrets/ 읽기 차단(permissions.deny)
├── .claude/settings.local.json # 같은 차단 — git 루트에서 로드되어 하위 디렉터리 세션도 보호(D15)
├── .gitignore                 # secrets/ 제외(git 전환 대비 선등록)
├── providers/                 # provider 엔티티 — 예: aws-main.md, onprem-idc.md
├── inventory/
│   ├── <server>.md            # server 엔티티
│   ├── <cluster>.md           # k8s-cluster 엔티티
│   └── components/            # component 엔티티 — 예: argocd.md, victoria-metrics.md
├── access/keys.md             # 키·인증서 목록 — 위치 참조만, 값은 절대 안 적음
├── changes/YYYY/              # 변경 기록(날짜 기반, append-only)
├── decisions/                 # ADR — 예: ADR-0001-harness-init.md
├── runbooks/                  # 운영 절차 문서
└── secrets/                   # (secrets_mode≠none일 때) 시크릿 값 — Read 도구 차단됨
```

엔티티는 **YAML frontmatter + 마크다운 본문**이며 `id`는 파일명과 일치한다. 다섯 종류를 다룬다.

| 엔티티 | 위치 | 핵심 필드 |
|---|---|---|
| provider | `providers/<id>.md` | `kind`(aws/gcp/onprem), `cli_profile`, `regions`, `console` |
| server | `inventory/<id>.md` | `env`, `provider`, `runtime`, `access`, `managed_by`(terraform/manual) |
| k8s-cluster | `inventory/<id>.md` | `env`, `provider`, `context`, `access_recipe`, `managed_by` |
| component | `inventory/components/<id>.md` | `category`, `runs_on`, `namespace`, `endpoint`, `installed_by` |
| key/인증서 | `access/keys.md`의 표 행 | 이름, `kind`(ssh-key/tls-cert/api-token/cloud/account/password), `principal`, fingerprint, **위치 참조**, `usage`(참조 실행 레시피), 소유자, 생성일, 만료·로테이션 |

server의 사양·사설/공인 IP·아키텍처·서버별 특이 정보는 frontmatter 필드가 아니라 **엔티티 본문**에
자유 서술한다(스펙 D10 — `## 네트워크`/`## 사양`/`## 특이사항` 관례 섹션 권장, 강제 아님). 스킬이
파싱해 명령을 만드는 운영 메타데이터만 frontmatter에 둔다.

k8s는 **클러스터·컴포넌트 수준까지만** 인벤토리화한다. 내부 리소스(deployment/service)는
manifest·GitOps 레포 참조로 넘긴다(원칙 4 — 하네스는 상태를 복제하지 않는다).

## 3. 설치

### 설치

```bash
git clone <저장소 URL> ~/infra-plugin
mkdir -p ~/infra-workspace && cd ~/infra-workspace   # 하네스로 쓸 디렉터리
claude --plugin-dir ~/infra-plugin
```

`--plugin-dir`에는 `.claude-plugin/plugin.json`이 있는 저장소 루트의 절대 경로를 준다.
같은 이름의 설치된 플러그인이 있어도 `--plugin-dir`로 띄운 쪽이 우선한다.

위 경로가 현재의 정식 설치 방법이다.

> **언어**: 스킬 본문과 산출 문서는 한국어다. 영어권 사용자 대응(i18n)은 별도 작업으로
> 예정돼 있으며, 그 전까지는 한국어를 읽을 수 있는 환경을 전제한다.

### 사내·개인 marketplace에 등록해 배포하려면

이 저장소는 marketplace를 운영하지 않지만, 사용자가 **자신의** 사내·개인 marketplace에
이 플러그인을 등록해 팀에 배포할 수는 있다. 그 경우 팀원은 저장소를 직접 내려받지 않고
세션 안에서 `/plugin` 명령으로 marketplace 추가와 `infra` 플러그인 설치를 진행한다.
(marketplace 자체를 구성하는 작업은 이 저장소의 범위 밖이다.)

### 개발 루프

스킬·스크립트·hooks 파일을 수정한 뒤에는 세션을 새로 시작하지 않고 세션 안에서
`/reload-plugins`를 실행해 변경 사항을 반영한다.

### 요구 사항

- **플러그인 자체**는 `python3`만 있으면 된다. `scripts/`·`hooks/scripts/`는 python3 표준
  라이브러리만 쓴다(PyYAML 등 외부 패키지 설치 불필요).
- **하네스 운영 시** `ops`/`sync`/`connect`/`register`가 로컬에 설치된 CLI를 조종한다:
  `aws`, `gcloud`, `kubectl`, `helm`, `argocd`, `terraform`, `ssh`(+ `ansible`·`docker`
  스캔). `init`이 설치된 것만 자동 발견하며, 없는 도구는 해당 작업 시점에 설치를 안내한다.
  이 플러그인은 이 CLI들을 대신 설치하지 않는다.

## 4. 시작하기

1. 하네스로 쓸 **빈 디렉토리**를 만들고 그 안에서 세션을 연다(기존 프로젝트 디렉토리가
   아니라 별도 디렉토리를 쓴다 — 하네스는 중앙 1개다).

   ```bash
   mkdir ~/infra-workspace && cd ~/infra-workspace
   claude --plugin-dir /path/to/infra
   ```

2. 대화창에 "인프라 하네스 만들어줘"라고 요청한다. `init` 스킬이 로컬에 설치된 CLI를
   자동으로 스캔한 뒤 확인 인터뷰를 거쳐 `harness.yaml`·`CLAUDE.md`·`providers/` 등 하네스
   골격을 만든다.

   > **인터뷰에서 먼저 정하는 것 — 공유·시크릿 모드.** `init`은 하네스를 어떻게 보관·공유할지
   > (`sharing`)와 시크릿 값을 하네스 안에 둘지(`secrets_mode`)를 묻는다. 이 선택이 `secrets/`
   > 생성 여부와 `.gitignore`·deny 규칙 구성을 결정한다. 유효 조합은 §10과 아래 표를 참고:
   >
   > | `sharing` | 허용 `secrets_mode` | 시크릿 저장 |
   > |---|---|---|
   > | `local`(비공유) | `none`, `plaintext` | `secrets/`에 평문 허용(≈ `~/.ssh`와 동급) |
   > | `git` / `shared-drive`(공유) | `none`, `encrypted` | age/SOPS 암호문만(복호 키는 각 머신 로컬) |
   > | 공유 + `plaintext` | — | **금지**(audit가 실패 처리) |
   >
   > ssh 키처럼 도구가 위치·권한(600)을 요구하는 키는 원위치(`~/.ssh`) 유지 + 참조가 기본이다
   > (공유 드라이브는 POSIX 권한을 보존하지 않아 ssh가 거부한다).

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
   | "새 팀원 온보딩해줘" | secrets |

   각 스킬은 `/infra:<이름>`(예: `/infra:init`)으로 직접 호출할 수도 있지만, 이는 보조
   경로다 — 기본 사용 형태는 자연어 대화다.

## 5. 유즈케이스

스킬은 하나씩 쓰기보다 흐름으로 엮일 때 가치가 크다. 대표 시나리오:

### 새 서버를 인프라에 추가했을 때 — register

"방금 띄운 prod-app-02 등록해줘". `register`가 대화형으로 필수 필드를 묻고, ssh 접근이
있으면(동의 후) systemd 유닛·`docker ps`를 스캔해 이 서버에서 도는 컴포넌트 후보까지
제안한다. 기존 서버 목록을 텍스트로 붙여넣으면 초안 표로 확인 후 일괄 등록한다.

### 온콜 중 접속법이 기억나지 않을 때 — lookup → connect

"prod DB 어떻게 붙어?" → `lookup`이 provider profile·access 정보와 **실행 가능한 명령
형태**로 답한다(토큰은 값이 아니라 `secrets/…` 위치 참조와 `${VAR}` 사용법으로). 자격이
만료돼 접속이 안 되면 "kubeconfig 다시 잡아줘" → `connect`가 엔티티의 `access_recipe`를
실행해 로컬 접근을 재구성한다.

### 컴포넌트를 업그레이드할 때 — ops → change

"victoria-metrics 0.9.1로 올려줘". `ops`가 대상 엔티티의 env를 표시하고, `harness.yaml`의
`policies.mutating` 정책에 따라 prod면 승인을 받은 뒤 `--kube-context` 명시로 실행한다.
완료 후 rollout status로 검증하고 `changes/`에 롤백 방법까지 채운 변경 기록 초안을 자동
생성한다(PostToolUse hook도 리마인드를 띄운다).

### 정기 인프라 점검 — sync + audit

"문서랑 실제 맞는지 봐줘" → `sync`가 read-only 수집으로 실제 인스턴스·노드·helm 릴리스를
모아 문서 누락 / 유령 / 버전 불일치 / 확인 불가 4구획으로 보고한다(자동 수정 없음).
"하네스 점검해줘" → `audit`가 문서 자체의 스키마·참조 무결성·시크릿 유출·정책 조합·키
만료 임박을 검증한다.

### 새 노트북을 세팅할 때 — connect

"이 클러스터들 접속 다시 잡아줘". `connect`가 클러스터마다 `access_recipe`를 보여주고
실행해 kubeconfig·프로파일을 재구성한다(온프렘처럼 파일 복사가 필요한 경우 위치·방법만
안내하고 kubeconfig 내용은 하네스로 가져오지 않는다).

### 하네스를 팀과 공유할 때 — 모드 전환

로컬로 쓰던 하네스를 git으로 공유하려면 `sharing: git` + `secrets_mode: encrypted`로 바꾸고
`secrets/`를 SOPS+age 암호문으로 전환한다 — 초기 `secrets_recipients`(팀원 공개키 +
recovery) 구성과 `.sops.yaml` 생성·재암호화는 `secrets` 스킬이 담당한다(D11). `audit`가
"공유 + 평문" 위반을 잡아 준다.

### 비밀번호·서버 계정 관리 — register → lookup

"이 DB 계정 비밀번호 등록해줘" → `register`가 `access/keys.md`에 `kind: password`(또는
`account`) 행을 추가한다. `principal`(계정명)만 인터뷰로 받고 **값은 표에 절대 적지 않는다**
— 값은 `secrets/pg-app.age`(하네스 내부, `secrets_mode: encrypted`) 같은 위치 참조로 두고,
`usage` 컬럼에는 `sops exec-env secrets/pg-app.age 'psql ...'`처럼 참조 실행 레시피만 적는다
(argv에 비밀번호를 직접 넣는 형태는 어디서도 제시하지 않는다). 이후 "pg-app 계정으로
접속해줘" → `lookup`이 값이 아니라 이 위치 참조와 `usage`의 실행 레시피를 그대로 안내한다.
SSH 비밀번호 로그인은 키 인증 전환을 권장하고 `sshpass` 도입은 하지 않는다(D12).

### 외부 시크릿 매니저(Vault·1Password) 사용 — register/lookup

이미 HashiCorp Vault나 1Password로 비밀번호를 관리하고 있다면 하네스로 값을 옮기지 않는다.
`harness.yaml`을 `secrets_mode: none`(하네스는 참조만)으로 두고, `register`가
`access/keys.md`의 위치 참조 컬럼에 `vault://mount/path`나 `op://vault/item/field`를 그대로
적는다(참조는 불투명 — 등록 시점에 값을 조회·검증하지 않는다, D14). "vm 토큰 어디 있어?" →
`lookup`이 `op run -- <명령>`(1Password) 또는 `export TOKEN=$(vault kv get -field=<key>
-mount=<mount> <path>)`(HashiCorp Vault, `VAULT_ADDR`/`VAULT_NAMESPACE` 명시) 같은 그
백엔드의 참조 실행 명령을 안내한다 — 실행은 사용자 몫이고, `-field` 없이 실행하면 시크릿
전체가 stdout에 그대로 출력되므로 항상 특정 필드만 env로 뽑아 쓰며 값을 대신 조회·출력하지
않는다. 백엔드별 상세 관례는 `secrets` 스킬의 `references/backends.md`를 참고한다.

### 새 팀원 온보딩 — secrets

"새로 합류한 팀원 온보딩해줘, age 공개키는 이거야" → `secrets`가 `harness.yaml`의
`secrets_recipients`에 그 공개키를 추가하고 `.sops.yaml`을 재생성한 뒤 `sops updatekeys`로
기존 암호문 전체를 재키잉한다. age **공개**키는 비밀이 아니므로 harness.yaml에 그대로 남아도
안전하다(D11).

### 팀원 오프보딩 — secrets

"OO님 나갔어, 시크릿 접근 회수해줘" → `secrets`가 3단계로 처리한다: ① `secrets_recipients`
에서 제거하고 `.sops.yaml`을 갱신해 `sops updatekeys`로 전체 재키잉 ② 재키잉만으로는 그
사람이 이미 가진 구버전 암호문을 여전히 복호할 수 있으므로 **하위 자격증명(비밀번호·토큰
등)을 실제로 로테이션** ③ 로테이션 내역을 `changes/`에 기록. 조직 복구 수신자(`recovery`)는
항상 유지되므로 개인 이탈이 하네스 접근 단절로 이어지지 않는다(D11).

## 6. 불변 원칙과 하네스 발견 규약

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

## 7. 스킬

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
| secrets | 팀 시크릿(SOPS+age)의 수신자 관리·재키잉 생명주기(온보딩·오프보딩·자격증명 로테이션)를 담당한다 | "새 팀원 온보딩해줘" |

`ops`는 도구별 조작 지식을 `skills/ops/references/{kubectl,argocd,prometheus,helm}.md`로
분리해 명령을 조립하기 전에 필요한 것만 불러온다.

`change_reminder` hook은 세션에서 `terraform apply`·`kubectl apply`·`helm upgrade`·
`argocd app sync` 같은 mutating 명령이 실행되면 "변경 기록을 남기세요" 리마인드를 띄운다
(`harness.yaml`의 `hooks.change_reminder: false`면 조용히 통과).

## 8. 테스트

```bash
bash tests/run_tests.sh
```

`tests/fixtures/harness-ok`(정상 하네스)·`tests/fixtures/harness-bad`(오염 하네스)·
`tests/fixtures/harness-off`(hook 비활성화 검증용)·`tests/fixtures/harness-onprem`(온프렘 전용)
네 fixture를 대상으로 다음을 자동 검증한다.

- `scripts/audit.py`의 기대 결과 — 스키마/참조/시크릿 패턴/정책 조합/만료 경고에 더해 D13
  하드닝(심링크 거부·`secrets/` 재귀 스캔·`secrets_mode: none` 강제·엄격 헤더 판별·중복
  id/conflict-copy 파일명 탐지·`--staged` 모드)과 D11 수신자(recovery 필수)·D12
  자격증명(kind 어휘·위치 참조 누락) 검증까지 각 항목의 통과·실패
- `hooks/scripts/change_reminder.py`의 케이스(mutating 매치 / read-only 제외 / `--dry-run`
  제외 / `hooks.change_reminder: false` / 하네스 밖에서 실행)
- `scripts/sync_snapshot.py`의 문서 스냅샷 파서·diff 로직(모의 수집 데이터 주입)

## 9. 수동 검증 체크리스트

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

## 10. 안전성 FAQ

**Q. 클로드가 내 시크릿 값(키·토큰·비밀번호)을 보게 되나?**
정상 사용 경로에서는 보지 않는다(원칙 1). 스킬·스크립트 어디에도 값을 읽거나 출력하는
경로가 없고, 사용은 항상 참조 실행(`${VAR}`, `ssh -i <경로>`, `sops exec-env`)뿐이다.
**1차 방어선은 "스킬이 스스로 값을 읽지 않는 것"이며**, `.claude/settings.json`의 deny
규칙은 그 위에 얹는 2차 가드레일이다.

**단, deny 규칙은 보안 경계가 아니다**(D13). 공식 문서도 Read 규칙 적용을 "best-effort"로
서술한다. 아래 세 경우에는 차단이 걸리지 않으므로 알고 쓰는 편이 낫다.

| 경우 | 동작 |
|---|---|
| **하네스 하위 디렉터리에서 세션을 연 경우** | `.claude/settings.json`은 cwd의 `.claude/`에서만, **부모 폴백 없이** 로드된다. `init`이 `settings.local.json`에도 같은 규칙을 쓰므로 **git 저장소인 하네스는 하위 디렉터리에서도 보호**되지만, git을 쓰지 않는 하네스는 **하네스 루트에서 세션을 열어야** 보호된다 |
| **임의 서브프로세스** | deny는 Read 도구와 `cat`·`head`·`tail`·`sed` 같이 인식된 파일 명령에 적용되고, **파이썬·노드 스크립트처럼 스스로 파일을 여는 프로세스에는 적용되지 않는다.** 이 플러그인의 `scripts/*.py`도 여기 해당한다 — `audit`이 `secrets/`를 재귀 스캔할 수 있는 이유이며, 그래서 스크립트는 값을 출력하지 않도록 작성하고 회귀 테스트로 강제한다(`tests/test_secret_containment.py`) |
| **하네스 밖에서 절대 경로로 지목한 경우** | deny는 cwd 기준이라 다른 디렉터리에서 연 세션이 하네스 `secrets/`를 절대 경로로 읽으면 걸리지 않는다 |

OS 수준에서 모든 프로세스를 막고 싶다면 Claude Code의 **샌드박스**를 켜는 것이 유일한
방법이다. 반대로 값을 아예 로컬에 두지 않는 선택(`secrets_mode: none` + Vault·1Password
같은 외부 매니저 참조, D14)도 이 위험을 근본적으로 줄인다.

**Q. 하네스를 팀과 git으로 공유해도 되나?**
된다. 단 `secrets_mode: encrypted`로 두고 SOPS+age 암호문만 커밋한다(복호 키는 각 머신
로컬) — 수신자(`secrets_recipients`) 관리·재키잉·오프보딩 시 자격증명 로테이션은 `secrets`
스킬이 전담한다(D11). "공유 + 평문" 조합은 `audit`가 실패로 잡고, 심링크는 읽지 않고
거부하며 `secrets/`를 재귀로 검사하고 `--staged`로 커밋 전 스냅샷도 점검할 수 있다(D13).
값 회수·감사가 더 필요하면 하네스에는 참조만 두고 실제 값은 외부 시크릿 매니저(Vault·
1Password 등, D14)나 패스워드 매니저 공유 볼트 같은 채널을 쓴다.

**Q. 비밀번호나 서버 계정도 이 하네스에 담을 수 있나?**
된다(D12). `access/keys.md`에 `kind: account`/`password` 행으로 관리하되, 값은 어떤
경우에도 표에 적지 않고 위치 참조(`secrets/…` 또는 `op://`·`vault://`·
`aws-secretsmanager://` 같은 외부 매니저 참조, D14)만 남긴다. 사용은 `usage` 컬럼의
레시피(`sops exec-env`, `op run -- <명령>` 등)로만 하고, **argv에 비밀번호를 직접 넣는
형태는 register·lookup 어디서도 제시하지 않는다**(ps·셸 히스토리 유출 방지). SSH
비밀번호 로그인은 키 인증 전환을 권장하고 `sshpass`는 도입하지 않는다.

**Q. 팀원이 나가면 하네스의 시크릿은 어떻게 되나?**
`secrets` 스킬이 오프보딩을 3단계로 처리한다: ① `harness.yaml`의 `secrets_recipients`에서
그 사람을 제거하고 `.sops.yaml`을 갱신해 `sops updatekeys`로 전체 재키잉 ② 재키잉만으로는
그 사람이 이미 로컬에 가진 구버전 암호문을 여전히 복호할 수 있으므로 **하위
자격증명(비밀번호·토큰 등)을 실제로 로테이션** ③ 로테이션 내역을 `changes/`에 기록. 조직
복구 수신자(`recovery`)는 항상 유지되어 개인 이탈이 하네스 접근 단절로 이어지지 않는다(D11).

**Q. 하네스와 무관한 다른 프로젝트에서 세션을 열면 이 플러그인이 방해하나?**
아니다(스펙 D1). 스킬은 `harness.yaml`을 상향 탐색해 못 찾으면 안내 후 중단하고, hook은
조용히 통과(exit 0)한다. 하네스 밖 작업에는 개입하지 않는다.

**Q. 실수로 prod를 건드리지 않게 막아 주나?**
`harness.yaml`의 `policies.mutating`으로 환경별 승인 게이트를 둔다(예: `prod: confirm`).
정책에 없는 env는 안전 기본값 `confirm`으로 취급한다. read-only 명령은 게이트 없이 즉시
실행되고, mutating만 이 파이프라인을 탄다(원칙 7).

## 11. 마이그레이션

### 기존 하네스에 보호 설정 보강 (D15)

`.claude/settings.local.json`이 없는 기존 git 하네스는 `audit`가 실패로 보고한다. 하네스
하위 디렉터리에서 연 세션이 `secrets/` 차단을 받지 못하기 때문이다(`settings.json`은 부모
폴백 없이 cwd에서만 로드된다).

하네스에서 **"하네스 점검해줘"**라고 말하면 `audit`가 누락을 짚고 `init`이 보완을 제안한다.
직접 처리하려면 `.claude/settings.json`과 같은 내용으로 `.claude/settings.local.json`을
만들면 된다. `sharing: git` 하네스라면 이 파일을 **커밋한다** — 이름은 `local`이지만 팀
전체가 같은 보호를 받게 하려는 의도적 선택이며, `.gitignore`에 넣지 않는다.

## 12. 트러블슈팅

자주 겪는 문제와 해결 방법.

**하네스를 못 찾음** — register/lookup 등 스킬이 "하네스 디렉터리에서 세션을 열거나
init으로 하네스를 먼저 생성하세요"라며 중단된다. cwd에서 상향 탐색해도 `harness.yaml`을
찾지 못한 것이다(D1). 하네스 저장소 디렉터리(또는 그 하위)에서 세션을 다시 열거나,
처음이라면 "인프라 하네스 만들어줘"로 `init`을 실행한다.

**"공유 + 평문" audit 실패** — `audit`가 `[정책]` 실패로 공유(`sharing: git`/
`shared-drive`) + `secrets_mode: plaintext` 조합을 잡는다(원칙 2 위반). `secrets_mode:
encrypted`로 전환하고 `secrets` 스킬로 `secrets_recipients`(팀원 공개키 + recovery)를
구성해 재암호화한다.

**`sops`가 복호 키를 못 찾음("no key could decrypt" 등)** — 내 age 개인키가
`secrets_recipients`(및 그로부터 생성된 `.sops.yaml`)에 아직 없다는 뜻이다 — 온보딩이
안 된 상태다. 팀원에게 내 age **공개**키를 전달해 온보딩(`secrets` 스킬 — 수신자 추가 +
`sops updatekeys` 재키잉)을 요청한다.

**`secrets/`를 Read 도구로 열 수 없음** — 정상 동작이다(버그 아님). `.claude/settings.json`의
`permissions.deny`가 `secrets/` 읽기를 차단하도록 설계돼 있다(원칙 2의 기계적 강제, D3).
값이 필요하면 읽지 말고 `keys.md`의 위치 참조 + `usage` 컬럼의 참조 실행
레시피(`sops exec-env`, `op run`, `ssh -i` 등)로 사용한다.

## 13. 기여·설계 문서

이 저장소를 **수정**하려는 경우:

- [`CLAUDE.md`](CLAUDE.md) — 저장소를 수정하는 세션용 지침(테스트 명령, python3 stdlib
  전용·hook exit 0·SKILL.md description 형식 같은 비자명 제약).
- [`docs/superpowers/specs/2026-07-19-infra-plugin-design.md`](docs/superpowers/specs/2026-07-19-infra-plugin-design.md)
  — 불변 원칙 10개, 데이터 스키마, 확정 결정 D1~D14.
- [`docs/superpowers/plans/2026-07-19-infra-plugin.md`](docs/superpowers/plans/2026-07-19-infra-plugin.md)
  — 태스크별 구현 계획(D1~D10, init~audit 스킬).
- [`docs/superpowers/plans/2026-07-22-team-secrets.md`](docs/superpowers/plans/2026-07-22-team-secrets.md)
  — 팀 시크릿·자격증명·audit 하드닝 구현 계획(D11~D14, secrets 스킬).

원칙·스키마·D 결정은 확정 사항이다. 이를 바꾸는 변경은 스펙을 먼저 갱신하고 진행한다.
변경 후에는 `bash tests/run_tests.sh`로 전체 테스트를 확인한다.

### 기여자 주의 — `skills/secrets/` 열람

`Read(secrets/**)` 계열 deny 규칙을 쓰는 환경에서 **플러그인 저장소가 세션 cwd 아래에
있으면** `skills/secrets/` 이하 문서가 차단된다. deny 규칙이 앵커 아래 임의 깊이의
`secrets` 디렉터리를 매치하기 때문이다(문서화된 동작).

이때는 git 경유로 읽는다: `git show HEAD:skills/secrets/SKILL.md`

실사용자에게는 발생하지 않는다 — 사용자의 cwd는 하네스이고 플러그인은
`~/.claude/plugins/…`나 clone 경로에 있어 앵커 밖이기 때문이다.

## 14. 라이선스

[MIT License](LICENSE) — Copyright (c) 2026 Youngrae Cho.

# infra 플러그인 설계 스펙

- 날짜: 2026-07-19
- 상태: 승인됨 (브레인스토밍 완료, 사용자 설계 승인)
- 다음 단계: superpowers:writing-plans로 구현 계획 작성

## 1. 목표와 배경

인프라의 **지식(인벤토리) · 기록(변경/의사결정) · 조작(직접 제어)**을 담당하는 "인프라 하네스"를 구성·운영하는 Claude Code 플러그인 `infra`를 구현한다.

- **플러그인** = 재사용 도구: 스킬 10종(init·register·lookup·connect·ops·change·decide·sync·audit·secrets), 템플릿, 스키마 정의, hooks, 검증 스크립트. 이 저장소(`Projects/infra`)의 루트가 곧 플러그인 루트다.
- **하네스 인스턴스** = 전용 중앙 저장소 1개: 데이터 + `harness.yaml` + `CLAUDE.md`. 저장·공유 방식은 자유(로컬 전용 / git / 공유 드라이브)이나 **외부 비공개는 필수**다 — 하네스는 IP·토폴로지·접근 정보가 담긴 민감 문서다. 저장소 이름은 자유(예: `infra-workspace`)이며 플러그인 이름과 무관하다.
- 인프라는 프로젝트 크로스커팅이므로 하네스는 프로젝트별이 아니라 **중앙 1개**다. init이 이 저장소를 스캐폴딩한다.
- 대상 환경: 온프렘 · AWS · GCP 혼합. 앱/DB/모니터링 서버, k8s 클러스터, argocd·prometheus·victoria-metrics 같은 설치 컴포넌트.
- 슬래시 직접 호출(`/infra:init` 등)은 보조 경로다. **대화 중 클로드가 description을 보고 스스로 적절한 스킬을 골라 쓰는 것이 기본 사용 형태**다(원칙 10).

## 2. 브레인스토밍 확정 결정

원 스펙이 열어둔 부분에 대해 아래를 확정했다 (D1은 사용자 선택, 나머지는 설계 제시 후 일괄 승인).

| ID | 결정 | 내용 |
|----|------|------|
| D1 | 하네스 발견: **하네스 안에서만** | 모든 스킬·hook은 cwd에서 루트 방향으로 `harness.yaml`을 상향 탐색해 `HARNESS_ROOT`를 정한다. 미발견 시 init만 "새 하네스 생성 모드"로 진입하고, 나머지 스킬은 하네스 디렉터리에서 세션을 열거나 init을 실행하라고 안내 후 중단한다. hook은 미발견 시 조용히 통과(exit 0). 전역 포인터 파일·사용자 설정 변경은 하지 않는다. |
| D2 | scripts는 python3 표준 라이브러리 전용 | PyYAML 등 외부 의존 없음. 엔티티 frontmatter가 플랫 구조이므로 자체 미니 파서(`key: value`, `[a, b]` 리스트, 따옴표 문자열)로 충분하다. 스펙의 "bash 우선, 복잡하면 python" 방침에서 frontmatter 파싱·참조 그래프 검증은 '복잡한 경우'에 해당한다. |
| D3 | deny 규칙 두 형태 병기 | permissions 경로 앵커 문법이 미묘하므로(`/path`=설정 파일 기준, `./path`=cwd 기준 — 부록 A) `Read(/secrets/**)`와 `Read(./secrets/**)`를 병기하고, 구현 시 실제 Read 시도로 차단을 검증한다(완료 기준 4). |
| D4 | 정책 미정의 env는 confirm 기본 | `policies.mutating`에 해당 env 키가 없으면 안전 기본값 `confirm`으로 동작한다. |
| D5 | component의 env·context는 runs_on 체인 해석 | component frontmatter에는 env가 없다. ops는 `runs_on`이 가리키는 server/k8s-cluster 엔티티에서 env와 context/profile을 해석한다. |
| D6 | hook 오탐 방지 | `kubectl rollout status|history`는 read-only이므로 매치하지 않고 `rollout restart|undo|pause|resume`만 매치. `--dry-run` 포함 명령은 제외. PostToolUse는 사후 실행이므로 어떤 경우에도 차단하지 않는다. |
| D7 | description은 인프라 도메인 어휘 우선 | 기존 설치된 `harness:harness` 메타 스킬과 "하네스" 용어가 겹치므로, description은 "인프라 하네스(서버·k8s·컴포넌트 인벤토리)"처럼 인프라 도메인 어휘를 앞세워 오선택을 방지한다. |
| D8 | tests/fixtures 자동 검증 | fixture 하네스로 audit·sync 파서·hook 스크립트를 자동 검증한다. 최소 구성은 정상 하네스 1개 + 오염 하네스 1개이며, 이후 검증 대상이 늘면서 hook 비활성화·온프렘 전용 fixture가 추가됐다(현재 목록은 §12). |
| D9 | 매니페스트·개발 루프 | 저장소 루트 = 플러그인 루트. `plugin.json`은 `name: "infra"`, `version: "0.1.0"`, `description`, `author`. 개발 테스트는 `claude --plugin-dir .` + `/reload-plugins`. |
| D10 | 서버 정보: 파싱 대상만 frontmatter, 이질적 정보는 본문 | 스킬이 **결정론적으로 소비하는 값**(① 명령 생성 — `--context`/`--profile`(원칙 6) ② 참조 무결성(audit) ③ 실제 상태 대조(sync))만 frontmatter에 둔다. 서버 사양·사설/공인 IP·아키텍처·서버별 특이 정보처럼 이질적이고 프로그램이 diff하지 않는 정보는 markdown 본문에 자유 서술하되, register가 채우고 사람이 읽기 좋게 `## 네트워크`·`## 사양`·`## 특이사항` 같은 가벼운 관례 섹션을 쓴다(강제 스키마 아님). 이로써 파서·`REQUIRED_FIELDS`·`schema_version` 변경 없이 후방호환을 유지하고, 사양을 sync가 대조하는 상태 복제(원칙 4 위반)를 피한다. IP drift 자동 감지처럼 스킬이 특정 값을 결정론적으로 소비해야 할 때에만 그 값을 frontmatter로 **승격**한다(그 시점에 `provider_resource_id` 등과 함께 별도 결정으로 다룬다). |
| D11 | 팀 시크릿 라이프사이클 (encrypted 운영 프로토콜) | 공유(`git`/`shared-drive`)+`encrypted`는 **SOPS+age**를 표준으로 한다(raw age보다 수신자 관리·재키잉이 우수). `harness.yaml`의 `secrets_recipients`(`name: age공개키` 중첩 맵)에 팀원 공개키 + **조직 복구 수신자(필수)**를 두고 이를 근거로 `.sops.yaml`을 생성한다. 온보딩=수신자 추가 후 `sops updatekeys` 재키잉. **오프보딩=수신자 제거 + 재키잉 + 하위 자격증명 로테이션**(구버전 암호문은 이전 키로 복호 가능하므로 재키잉만으론 불충분). 신규 `secrets` 스킬이 이 라이프사이클을 담당한다. 공유 드라이브는 동시 편집에 취약하므로 암호문을 단일 작성자/읽기 위주 아티팩트로 취급한다. audit은 복호하지 않고(헤더만) 수신자 drift·MAC은 `secrets` 스킬이 SOPS 도구로 처리하되 평문을 출력하지 않는다. |
| D12 | 자격증명 스키마 (keys.md 개정) | keys.md를 ssh 키 외 계정·비밀번호도 담게 개정. 컬럼: `이름 / kind / principal / fingerprint / 위치 참조 / usage / 소유자 / 생성일 / 만료·로테이션`(생성일과 만료를 분리해 audit의 만료 검사가 생성일을 오인하지 않게 한다). `kind` 어휘 = `ssh-key \| tls-cert \| api-token \| cloud \| account \| password`. `principal`=주체(계정·비밀번호에 필요), `fingerprint`=종류별 선택(비밀번호엔 무의미), `usage`=안전한 주입 방법. 비밀번호는 **argv 절대 금지**(ps/history 유출), `sops exec-env`·`op run`·stdin/FD·백엔드 네이티브 주입만. SSH 비밀번호 로그인은 키 인증을 권장하고 `sshpass`를 도입하지 않으며 불가피하면 명시적 지원 경로를 usage에 적는다. audit이 kind 어휘·위치 참조 존재를 검증한다. |
| D13 | audit 하드닝 + secrets_mode 강제 | audit이 ① 심볼릭 링크를 **읽기 전에 거부**(하네스 밖 링크 추종 방지) ② `secrets/`를 **재귀** 스캔(직속 자식만 아님) ③ `secrets_mode: none`이면 `secrets/`에 시크릿 페이로드 파일이 없어야 함을 강제 ④ encrypted 헤더를 **엄격 prefix**로 검사(느슨한 부분문자열 제거, 암호학적 유효성은 주장하지 않음) ⑤ 중복 id·conflict-copy 파일명(예: `*conflicted copy*`, `* (1).md`) 탐지. `audit.py --staged`로 git staged 스냅샷을 검사(pre-commit용, git 없으면 무시). 어떤 경우에도 복호하지 않고 매치 값을 출력하지 않는다. `.claude/settings.json` deny는 Read 도구만 막는 **가드레일이며 보안 경계가 아님**(Bash/Python은 여전히 읽음)을 문서에 명시한다. |
| D14 | 외부 시크릿 백엔드 참조 규약 | keys.md 위치 참조 스킴을 명시: `secrets/…`(로컬) · `op://`(1Password) · `vault://`(HashiCorp Vault) · `aws-secretsmanager://`. 참조는 **불투명** — lookup·audit은 이를 resolve(복호·조회)하지 않고 위치와 사용 명령만 다룬다. 각 백엔드의 참조 실행 관례(`op run`, `vault kv get`, `aws secretsmanager get-secret-value` + 명시적 profile/region/namespace)는 references로 둔다. 전역 `secrets_backend`는 만들지 않는다(혼합 백엔드가 정상 — 참조별 식별). 외부 매니저 사용은 `secrets_mode: none`(하네스는 참조만)에 해당한다. |
| D15 | deny 방어선의 실효 범위 명문화 + 하위 디렉터리 구멍 차단 | `.claude/settings.json`은 **cwd의 `.claude/`에서만 부모 폴백 없이** 로드되는데 하네스 발견은 상향 탐색이므로(D1), 하네스 하위 디렉터리에서 연 세션은 스킬만 동작하고 `secrets/` 차단은 사라진다. init이 `.claude/settings.local.json`(= git 저장소 루트에서 로드됨)에 같은 deny 규칙을 한 벌 더 심어 이 구멍을 메우고, `sharing: git`이면 이 파일을 커밋 대상에 포함한다(이름은 local이지만 팀 전체 보호가 목적 — `.gitignore`에 넣지 않는다). git 저장소가 아닌 하네스는 메울 수단이 없으므로 "세션을 하네스 루트에서 열라"고 안내한다. audit이 두 파일의 존재·규칙 드리프트를 검사한다(`secrets_mode: none`이면 지킬 로컬 값이 없으므로 경고). 또한 deny는 Read 도구와 인식된 파일 명령(`cat`·`head`·`tail`·`sed`)에만 걸리고 **임의 서브프로세스(파이썬·노드 스크립트)에는 걸리지 않으므로**, 이 플러그인 자신의 `scripts/*.py`도 차단 밖이다 — 이 사실을 README FAQ와 CLAUDE.md에 명시하고, 스크립트가 시크릿 값을 출력하지 않음을 카나리 회귀 테스트로 강제한다. OS 수준 경계는 샌드박스뿐임도 함께 안내한다. |
| D16 | 문서 수치의 정합성은 테스트로 강제 | 문서(`CLAUDE.md`·`README.md`)가 스킬 수·결정 범위·계획 문서 목록처럼 코드 구조를 수치나 목록으로 언급하면, 그 정합성을 `tests/test_docs_consistency.py`가 검사한다. 손으로 고치는 규율만으로는 재발하기 때문이다(P0 작업 중 실제로 재발). 구조를 바꾸는 변경은 문서와 테스트를 같은 커밋에서 함께 갱신한다. |

## 3. 불변 원칙 (전 스킬 공통, 위반 불가)

모든 스킬은 아래 원칙을 위반할 수 없다. 각 스킬 SKILL.md에 해당되는 원칙 번호를 명시한다.

1. **시크릿 값의 컨텍스트 유입 금지 — 참조 실행만.** 클로드는 키·토큰·인증서의 값을 어떤 경우에도 읽거나 출력하지 않는다. 사용은 항상 참조 실행으로 한다: `ssh -i <경로>`, `--token-file <경로>`, 환경변수 `${VAR}`, `sops exec-env`, `op run -- <명령>`처럼 값이 명령 실행 경로로만 흐르는 형태. 자동 발견 시에도 `~/.aws/credentials`·kubeconfig raw 파일을 읽지 않는다 — `aws configure list-profiles`, `kubectl config get-contexts`, `ssh-keygen -lf` 같은 메타데이터 출력만 사용한다. lookup 등 조회 스킬도 키를 물으면 값이 아니라 위치 참조와 사용 명령 형태로 답한다.
2. **시크릿 저장 정책은 공유 모드에 종속.** 원칙 1은 컨텍스트 유출만 막고 공유·동기화 경로의 유출은 못 막으므로, 값을 하네스 안에 둘 수 있는지는 harness.yaml의 `sharing`에 따라 결정된다:
   - `sharing: local`(비공유) → `secrets/`에 평문 보관 허용. 사실상 `~/.ssh`와 동급의 로컬 디렉터리다.
   - 공유(`git` / `shared-drive`) + 하네스 내 보관 → **암호화 저장만 허용**(age 또는 SOPS). 암호문만 동기화되고 복호 키는 각 머신 로컬에 둔다. 사용은 `sops exec-env secrets.yaml '<명령>'` 형태로 원칙 1과 결합.
   - 공유 + 평문 → **금지**. 팀 배포가 목적이면 회수·감사가 가능한 채널(패스워드 매니저 공유 볼트 등)을 쓰고 하네스에는 참조만 둔다.
   - 예외: ssh 키처럼 도구가 위치·권한(600)을 요구하는 키는 원위치(`~/.ssh`) 유지 + 참조가 기본이다. 공유 드라이브 동기화는 POSIX 권한을 보존하지 않아 ssh가 거부한다.
   - 기계적 강제: init이 하네스의 `.claude/settings.json`에 `permissions.deny`로 `secrets/` 읽기 차단을 설정한다(D3). 실행 참조는 되고 읽기만 막힌다.
3. **묻기 전에 스캔.** 로컬에서 발견 가능한 정보(CLI 설치 여부, profile, context, 키 fingerprint, 설치된 컴포넌트)는 스캔 → 확인 순서로 진행한다. 사용자 기억과 타이핑에 의존하지 않는다.
4. **하네스는 지도 + 조종석이지 엔진이 아니다.** 상태의 SSOT는 클러스터 실제 상태, terraform state, config 레포다. 하네스는 색인·맥락(왜)·조작 진입점만 담당하고 상태를 복제하지 않는다.
5. **managed_by는 엔티티 속성.** IaC 사용 여부는 하네스 전역 모드가 아니다(현실은 terraform 관리 + 수동 관리 혼합). 엔티티별 `managed_by` 필드로 표현하고, IaC 관리 대상은 참조만 둔다. `managed_by: manual`인 엔티티의 설정을 담을 필요가 생기면 그때 `configs/`를 만든다.
6. **암묵 컨텍스트 금지.** 모든 조작 명령은 엔티티에서 읽은 `--context` / `--profile`을 명시적으로 붙인다. 현재 kubectl 컨텍스트나 기본 aws profile에 의존하는 명령을 절대 생성하지 않는다.
7. **읽기/변경 분리.** read-only 조작(get, describe, logs, top, PromQL 쿼리, `argocd app list` 등)은 자유롭게 실행한다. mutating 조작(apply, delete, scale, rollout, helm upgrade, `argocd app sync` 등)은 반드시 파이프라인을 따른다: ① 대상 확인(엔티티 env 표시, 정책에 따라 승인) → ② 실행(context/profile 명시) → ③ 검증(rollout status, 헬스체크) → ④ `changes/` 초안 자동 생성.
8. **정책은 데이터.** 환경별 가드("prod mutating은 항상 승인"), 공유 모드, hook 동작은 harness.yaml에 데이터로 두고 스킬이 읽어 적용한다. 정책 변경에 스킬 수정이 필요하면 안 된다.
9. **기록은 작업의 부산물.** 변경 기록은 별도의 일이 아니라 ops 파이프라인과 hook에서 자동 생성·유도된다. `changes/`는 날짜 기반 append-only 구조라 git 없이도 성립한다 — 저장 방식과 무관하게 changes/가 변경 이력의 SSOT다.
10. **스킬은 description으로 자동 선택 가능해야 한다.** 모든 SKILL.md frontmatter의 `description`은 클로드가 대화 흐름에서 스스로 그 스킬을 골라 호출할 수 있게 작성한다: ① 무엇을 하는지 한 문장 ② 언제 사용하는지 — 구체적 트리거 상황과 사용자 발화 예시 ③ 인접 스킬과의 경계. 스킬 본문과 산출 문서는 한국어. SKILL.md는 얇게 유지하고 상세 절차·도구별 지식은 `references/`로 분리한다(progressive disclosure).

## 4. 하네스 데이터 스키마

init이 스캐폴딩하는 하네스 저장소 구조:

```
infra-workspace/                    # 하네스 저장소 (이름 자유, 외부 비공개 필수)
├── CLAUDE.md                       # 하네스 소개, 규약 포인터, 하네스 변경 이력
├── harness.yaml                    # 공유 모드, 환경 목록, IaC 레포, 정책 (init 인터뷰 결과)
├── .claude/
│   └── settings.json               # permissions.deny — secrets/ 읽기 차단 (init 생성)
├── .gitignore                      # secrets/ 선등록 (git 미사용이어도 생성 — 이후 전환 대비)
├── providers/
│   ├── aws-main.md
│   └── onprem-idc.md
├── inventory/
│   ├── prod-app-01.md              # type: server
│   ├── prod-db-01.md               # type: server
│   ├── prod-k8s.md                 # type: k8s-cluster
│   └── components/
│       ├── argocd.md               # type: component
│       └── victoria-metrics.md
├── access/
│   └── keys.md                     # 키·인증서 "목록" — 메타데이터와 위치 참조만
├── secrets/                        # 값 보관 구역 — sharing 모드에 따라 평문/암호문 (원칙 2)
├── changes/
│   └── 2026/07-15-pg16-upgrade.md
├── decisions/
│   └── ADR-0001-harness-init.md    # init 인터뷰 결정(공유 모드 포함)도 첫 ADR로 기록
├── runbooks/
│   └── db-failover.md
└── configs/                        # managed_by: manual 엔티티가 생길 때만 생성
```

공통 규칙: 엔티티는 **YAML frontmatter + markdown 본문**. `id`는 파일명(stem)과 일치. 엔티티 간 참조는 id로. frontmatter는 스킬이 파싱하는 운영 메타데이터만 담고, 이질적·비파싱 정보(사양·IP·특이사항 등)는 본문에 자유 서술한다(D10). 본문 관례 섹션은 아래 server 예시를 참고.

### 4.1 엔티티 frontmatter

**provider** (`providers/aws-main.md`):

```yaml
---
id: aws-main
type: provider
kind: aws            # aws | gcp | onprem | ...
cli_profile: main    # aws --profile / gcloud configuration 이름
regions: [ap-northeast-2]
console: https://...
---
```

**server** (`inventory/prod-db-01.md`):

```yaml
---
id: prod-db-01
type: server
env: prod
provider: aws-main
runtime: ec2                        # ec2 | vm | baremetal | ...
purpose: PostgreSQL 단독 DB 서버
access: "ssh, 키: keys.md#deploy-key"
managed_by: terraform://org/infra-tf//modules/db    # 또는 manual
depends_on: []
---
```

server frontmatter는 위 필드(스킬이 파싱하는 운영 메타데이터)만 담는다. IP·사양·아키텍처·서버별
특이 정보는 **본문**에 자유 서술한다(D10 — 파서·REQUIRED_FIELDS 변경 없음, audit은 본문 미검사).
register가 이 본문을 채우며, 사람이 읽기 좋게 아래 관례 섹션을 권장한다(강제 아님):

```markdown
# prod-db-01

## 네트워크
- 사설 IP: 10.0.12.34
- 공인 IP: 3.35.x.x (EIP 고정)

## 사양  <!-- register가 ssh로 수집, 2026-07-21 -->
- arch: x86_64 / vCPU 8 / 32GiB
- 디스크: gp3 500GB + 데이터 2TB NVMe RAID1

## 특이사항
- 매일 02:00 pg_dump 배치 — 이 시간대 IO 지연 주의
```

**k8s-cluster** (`inventory/prod-k8s.md`):

```yaml
---
id: prod-k8s
type: k8s-cluster
env: prod
provider: aws-main
context: prod-k8s                   # kubectl context 이름
access_recipe: aws eks update-kubeconfig --name prod --profile main --alias prod-k8s
managed_by: terraform://org/infra-tf//modules/eks
---
```

`access_recipe`는 로컬 접근을 재구성하는 명령이다. EKS/GKE는 클라우드 CLI가 자격증명을 생성하므로 레시피로 충분하다. 온프렘(k3s 등)처럼 kubeconfig 파일 복사가 필요한 경우 레시피에 위치와 방법만 기술하고("master 노드 /etc/rancher/k3s/k3s.yaml, scp") 파일 내용은 저장하지 않는다.

**component** (`inventory/components/victoria-metrics.md`):

```yaml
---
id: victoria-metrics
type: component
category: monitoring                # gitops | monitoring | db | ingress | ...
runs_on: prod-k8s                   # server 또는 k8s-cluster id
namespace: monitoring
endpoint: https://vm.internal.example.com
installed_by: helm://vm/victoria-metrics-single@0.x   # helm 차트 | manifest 경로 | apt | docker 등
access: "PromQL API, 토큰: keys.md#vm-token"
---
```

`installed_by`는 재설치·업그레이드 재현과 sync의 drift 대조에 쓰이는 핵심 필드다.

k8s는 **클러스터·컴포넌트 수준까지만** 인벤토리화한다. 내부 리소스(deployment, service)는 manifest/GitOps 레포 참조로 넘긴다.

### 4.2 access/keys.md

키·인증서·자격증명(계정·비밀번호 포함)을 표로 관리(D12). 컬럼: **이름 / kind / principal / fingerprint / 위치 참조 / usage / 소유자 / 생성일 / 만료·로테이션**.

- `kind`: `ssh-key | tls-cert | api-token | cloud | account | password`.
- `principal`: 주체(계정명·사용자명). 계정·비밀번호에 필요, 키·토큰엔 생략 가능.
- `fingerprint`: 종류별 선택 — ssh 키·tls 인증서엔 유용, 비밀번호엔 무의미(빈칸).
- `위치 참조`: 값이 있는 곳. 외부(`~/.ssh/deploy-key`, `op://vault/item`, `vault://…`, `aws-secretsmanager://…`) 또는 하네스 내부(`secrets/vm-token.age`). 내부 보관 가능 여부는 원칙 2. 참조 스킴은 D14. **값은 이 파일에 절대 적지 않는다.**
- `usage`: 안전한 사용(참조 실행) 방법. 비밀번호는 argv 금지, `sops exec-env`·`op run`·stdin만(D12).
- `생성일` / `만료·로테이션`: 두 컬럼으로 분리. 만료·로테이션 컬럼은 만료/로테이션 예정일만 담고(없으면 `-`) audit이 이 마지막 컬럼만 만료 검사에 쓴다. TLS 인증서 만료도 여기서 추적.

### 4.3 컴포넌트 접근용 MCP 구성

victoria-metrics MCP처럼 컴포넌트 접근에 MCP를 쓰는 경우, MCP 구성 파일(`.mcp.json` 등)은 하네스에 보관한다(컴포넌트 access 메타데이터의 연장). 단 토큰 등 값은 구성 파일에 `${VM_TOKEN}` 같은 환경변수 참조로만 쓰고, 값 자체는 secrets 정책(원칙 2)을 따른다.

### 4.4 harness.yaml

```yaml
sharing: local              # local | git | shared-drive (Cowork·구글 드라이브 등)
secrets_mode: plaintext     # none(참조만) | plaintext(local에서만 유효) | encrypted(age/SOPS)
secrets_format: sops-age    # (encrypted일 때만) 팀 표준 암호화 형식 — D11
secrets_recipients:         # (encrypted일 때만) name: age공개키 — 복호 가능한 팀원 + recovery 필수 (D11)
  alice: age1exampleaaaa
  recovery: age1examplerecovery   # 조직 복구 수신자(개인 이탈에도 접근 보존)
environments: [prod, stage, dev]
iac:
  repos:
    - terraform://github.com/org/infra-tf
policies:
  mutating:
    prod: confirm      # 항상 명시적 승인
    stage: confirm
    dev: allow
hooks:
  change_reminder: true
```

유효성 규칙: `secrets_mode: plaintext`는 `sharing: local`에서만 허용된다. `secrets_mode: encrypted`면 `secrets_recipients`에 `recovery` 항목이 있어야 한다(D11). 위반 조합은 audit가 실패 처리한다. `policies.mutating`에 없는 env는 `confirm`으로 취급한다(D4). `secrets_recipients`는 공개키만 담으므로(비밀 아님) 공유돼도 안전하다.

### 4.5 changes/ 템플릿 필드

날짜, 대상 엔티티(id), 변경 내용, 사유(또는 ADR 링크), 실행 명령/방법, 결과·검증, **롤백 방법(필수)**. 경로: `changes/YYYY/MM-DD-slug.md`.

### 4.6 decisions/ (ADR)

표준 ADR: 상태, 맥락, 결정, 고려한 대안, 결과. `ADR-NNNN-slug.md`. 번호는 기존 최대 번호 + 1로 자동 부여.

## 5. 플러그인 구조

```
infra/                       # 이 저장소 루트 = 플러그인 루트
├── .claude-plugin/
│   └── plugin.json          # name: "infra" — 이 파일만 이 디렉토리에 둔다
├── skills/
│   ├── init/SKILL.md
│   ├── register/SKILL.md
│   ├── lookup/SKILL.md
│   ├── connect/SKILL.md
│   ├── ops/
│   │   ├── SKILL.md
│   │   └── references/{kubectl,argocd,prometheus,helm}.md
│   ├── change/SKILL.md
│   ├── decide/SKILL.md
│   ├── sync/SKILL.md
│   ├── audit/SKILL.md
│   └── secrets/
│       ├── SKILL.md
│       └── references/backends.md
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── change_reminder.py
├── scripts/                 # audit·sync 검증 스크립트 (python3 stdlib 전용)
│   ├── harness_lib.py       # 공용: 하네스 탐색, frontmatter 파서, harness.yaml 로더
│   ├── audit.py
│   └── sync_snapshot.py     # 인벤토리 스냅샷 추출 + 실측 수집 명령 생성/실행 + diff
├── templates/               # 엔티티·change·ADR·settings.json·settings.local.json·.gitignore 등 (init이 복사)
├── tests/
│   ├── fixtures/
│   │   ├── harness-ok/       # 정상 하네스
│   │   ├── harness-bad/      # 오염 하네스 (완료 기준 9 재현)
│   │   ├── harness-off/      # hook 비활성화(hooks.change_reminder: false)
│   │   └── harness-onprem/   # onprem provider·서버 (수집기 없음 → sync "확인 불가" 경로)
│   ├── test_secret_containment.py   # 스크립트 출력에 시크릿 값이 새지 않는지 검증하는 카나리
│   ├── test_docs_consistency.py     # 스펙-구현 정합성 카나리 (Task 7에서 생성)
│   └── run_tests.sh
└── README.md
```

주의: 컴포넌트 디렉토리를 `.claude-plugin/` 안에 넣지 않는다(로드되지 않는 흔한 실수). 스킬·hook에서 플러그인 파일 접근은 `${CLAUDE_PLUGIN_ROOT}` 기준 경로를 쓴다.

## 6. 스킬 공통 규약

모든 스킬은 아래 실행 프로토콜을 공유한다. SKILL.md마다 이 규약을 짧게 재기술하거나 참조한다.

1. **하네스 발견(D1)**: cwd에서 루트 방향으로 `harness.yaml`을 탐색한다. 발견 → `HARNESS_ROOT` 확정. 미발견 → init은 생성 모드로 진입, 그 외 스킬은 "하네스 디렉터리에서 세션을 열거나 `/infra:init`으로 생성하세요"라고 안내하고 중단한다.
2. **정책 로드**: `harness.yaml`에서 `sharing`, `secrets_mode`, `environments`, `policies`, `hooks`를 읽는다. 파싱 실패 시 audit 실행을 안내한다.
3. **원칙 준수**: 시크릿 값을 읽거나 출력하지 않는다(원칙 1). `secrets/`의 deny 규칙은 기계적 방어선일 뿐이며, 스킬 스스로 읽기를 시도하지 않는 것이 1차 방어다.
4. **승인 UX**: 사용자 확인이 필요한 지점(mutating confirm, 인터뷰, 일괄 등록 확인)은 AskUserQuestion 도구를 우선 사용하고, 도구가 없는 환경이면 텍스트 질문으로 폴백한다.

### 6.1 description 작성 양식 (원칙 10 + D7)

한국어로, ① 역할 한 문장(인프라 도메인 어휘 우선) ② 트리거 발화 예시 ③ 인접 스킬 경계. 예시(lookup):

```yaml
description: >-
  인프라 하네스(서버·k8s 클러스터·컴포넌트·키 인벤토리)에서 접속 방법과 위치를 조회해 답한다.
  "prod DB 어떻게 붙어?", "argocd 어디 떠 있어?", "vm 토큰 어디 있어?" 같은 질문에 사용.
  키·토큰은 값이 아니라 위치 참조와 사용 명령만 답한다. 명령 실행은 ops,
  로컬 접근 재구성은 connect, 새 엔티티 등록은 register.
```

## 7. 스킬 명세 (10종)

### 7.1 init — 하네스 스캐폴딩

적용 원칙: 1, 2, 3, 8. 절차:

1. **기존 하네스 감지**: 상향 탐색으로 harness.yaml 발견 시 감사/확장 모드로 분기 — audit를 실행하고 구조 점검·누락 보완을 제안하며 새로 만들지 않는다.
2. **자동 발견**(메타데이터만): aws / gcloud / kubectl / terraform / ansible / docker / helm / argocd CLI 설치 여부(`command -v`), `aws configure list-profiles`, `gcloud config configurations list`, `kubectl config get-contexts`, `ssh-keygen -lf ~/.ssh/*.pub`. `~/.aws/credentials`·kubeconfig raw 파일은 읽지 않는다.
3. **확인 인터뷰**: 발견 결과 중 관리 대상 선택, 미발견 제공자(온프렘 등) 수동 추가. AskUserQuestion으로 한 턴에 2~3개씩.
4. **정책 결정**: sharing과 secrets_mode를 원칙 2의 유효 조합을 설명하며 결정받는다(무효 조합은 선택지에서 제외). 이어서 환경 목록, IaC 레포 등록 여부, change_reminder hook 활성화 여부.
5. **스캐폴딩**: 디렉토리 + providers/*.md + harness.yaml + CLAUDE.md(하네스용) + `.claude/settings.json`(D3 deny 규칙) + `.gitignore`(secrets/ 선등록) + (secrets_mode ≠ none이면) `secrets/` + ADR-0001(인터뷰 결정 기록). templates/에서 복사·치환한다.
6. **마무리**: audit 1회 실행 → "서버·컴포넌트는 register로 등록" 안내.

init은 **골격까지만** 책임진다. 서버 전수 등록을 강요하지 않는다(콜드 스타트 마찰 방지).

### 7.2 register — 엔티티 등록

적용 원칙: 1, 3, 5. 두 모드:

- **대화형**: 한 건씩 인터뷰. type별 필수 필드를 묻되 스캔 가능한 것은 먼저 스캔한다.
- **일괄**: 서버 목록·스프레드시트 텍스트 붙여넣기 → 파싱해 엔티티 초안 표로 제시 → 확인 후 파일 생성.

스캔 우선: k8s-cluster 등록 시 `helm list -A --kube-context <c>`·네임스페이스 스캔으로 컴포넌트 후보 제안, 서버 등록 시(ssh 접근 가능하면) systemd 유닛·`docker ps` 스캔 제안. provider·key(메타데이터)도 register로 추가 가능. env가 harness.yaml의 environments에 없으면 목록 추가 여부를 확인한다.

### 7.3 lookup — 조회

적용 원칙: 1, 4. "prod DB 어떻게 붙어?", "argocd 어디 떠 있어?", "vm 토큰 어디 있어?" 류 질의에 엔티티·provider·keys를 조합해 답한다. 접근 방법 응답 시 profile/context/레시피를 함께 제시하고, 키·토큰은 값이 아니라 위치 참조와 사용 명령 형태로만 답한다. 깨진 참조를 만나면 경고하되 가능한 범위로 응답한다.

### 7.4 connect — 접근 구성

적용 원칙: 1, 3, 6. 클러스터·서버의 `access_recipe`를 실행해 로컬 접근을 (재)구성한다. 실행 전 레시피 내용을 보여주고 진행하며, 실행 후 read-only 명령(`kubectl --context <c> get nodes` 등)으로 검증한다. 필요한 CLI가 없으면 설치 방법을 안내한다.

### 7.5 ops — 직접 제어

적용 원칙: 1, 4, 6, 7, 8, 9. 파이프라인:

1. **대상 해석**: 엔티티 id → access 메타데이터(context/profile/endpoint). component는 `runs_on` 체인을 따라 env·context를 해석한다(D5).
2. **분류**: read-only는 즉시 실행. mutating은 대상 확인(id·env 표시) → harness.yaml 정책 적용(`confirm`이면 AskUserQuestion 승인, `allow`면 진행, 미정의 env는 confirm — D4).
3. **실행**: 모든 명령에 `--context`/`--profile` 명시(원칙 6). 시크릿이 필요한 명령은 참조 실행 형태(`-i <경로>`, `${VAR}`, `sops exec-env`, `op run`)로만 구성.
4. **검증**: rollout status, 헬스체크 등.
5. **기록**: mutating 완료 시 change 스킬 절차로 `changes/` 초안 자동 생성.

도구별 조작 지식은 `references/kubectl.md`, `references/argocd.md`, `references/prometheus.md`(victoria-metrics 포함), `references/helm.md`로 분리하고 SKILL.md에서 필요 시 로드한다. 각 reference는 read-only/mutating 명령 분류표와 context/profile 명시 형태를 담는다.

### 7.6 change — 변경 기록

적용 원칙: 8, 9. 템플릿 기반으로 `changes/YYYY/MM-DD-slug.md` 생성. ops에서 자동 호출되거나 수동 실행("방금 작업 기록 남겨줘"). 대화 맥락에서 대상 엔티티·명령·결과를 최대한 자동 채우고, **롤백 방법이 비어 있으면 반드시 묻는다**. 기존 파일은 수정하지 않는 append-only 구조.

### 7.7 decide — ADR 작성

적용 원칙: 9. 표준 ADR(상태, 맥락, 결정, 고려한 대안, 결과) 생성. 번호 자동 부여. 관련 change 기록과 상호 링크.

### 7.8 sync — drift 감지

적용 원칙: 1, 3, 4, 6. 인벤토리 문서 vs 실제 상태 대조 후 **보고**(자동 수정 아님 — 보고 후 사용자 확인을 받아 문서 갱신):

- provider별: `aws ec2 describe-instances --profile <p>`, `gcloud compute instances list` 등 read-only만.
- 클러스터별: `kubectl --context <c> get nodes`, `helm --kube-context <c> list -A`, `argocd app list`.
- 대조 결과 3종: 실제엔 있는데 문서에 없음(누락) / 문서엔 있는데 실제에 없음(유령) / 버전 불일치(installed_by vs helm list).
- 자격 증명이 없거나 수집 명령이 실패한 대상은 "확인 불가"로 구분 보고한다(오탐 방지).

### 7.9 audit — 정합성 검증

적용 원칙: 1, 2, 8. `scripts/audit.py`를 실행하고 결과를 보고한다. 검사 항목은 §8.1. 실패 항목이 있으면 수정 방법을 제안한다.

### 7.10 secrets — 팀 시크릿 라이프사이클

적용 원칙: 1, 2, 8. `sharing`이 공유이고 `secrets_mode: encrypted`인 하네스에서만 동작한다
(`none`이면 외부 백엔드 참조로 위임하고, `plaintext`는 공유 조합 자체가 금지다).

- **신규 생성·최초 암호화**: `.sops.yaml` creation_rules를 경로별로 나눠 작성하고(단일 키
  침해 범위 축소), 최초 암호화는 사용자가 자기 터미널에서 `sops <파일>`로 수행한다.
  클로드는 값을 생성하지도 출력하지도 않는다(원칙 1).
- **온보딩**: `secrets_recipients`에 팀원 age 공개키를 추가하고 `sops updatekeys`로 재키잉.
- **오프보딩**: 수신자 제거 → 재키잉 → **하위 자격증명 로테이션**의 3단계가 모두 필수다.
  암호문에서 지워도 이미 본 값은 회수되지 않기 때문이다.
- **복구 수신자**: 조직 복구 수신자를 모든 creation_rule에 포함한다. 없으면 audit 실패(D11).
- **편집·재암호화**: 기존 암호문 수정도 사용자 터미널에서 `sops <파일>`로 한다.
- **외부 백엔드**: `op://`·`vault://`·`aws-secretsmanager://` 참조는 resolve하지 않고
  형식과 사용 명령만 다룬다(D14). 상세는 `references/backends.md`.

인접 경계: 키 **메타데이터** 등록은 register, 위치·사용법 조회는 lookup, 값 사용은 ops의
참조 실행이다. 이 스킬은 암호문 파일과 수신자 집합의 라이프사이클만 담당한다.

## 8. scripts/ 설계

python3 표준 라이브러리 전용(D2). 공용 로직은 `harness_lib.py`(하네스 상향 탐색, frontmatter 미니 파서, harness.yaml 로더)로 모은다. 모든 스크립트는 하네스 루트를 인자로 받거나 cwd에서 상향 탐색해 **하네스 저장소 어디서든 실행 가능**하다.

### 8.1 audit.py 검사 항목

| # | 검사 | 실패 조건 |
|---|------|-----------|
| 1 | 스키마·참조 무결성 | type별 필수 frontmatter 필드 누락, id-파일명(stem) 불일치, provider / runs_on / depends_on이 존재하지 않는 id를 가리킴, access의 `keys.md#앵커`가 keys.md에 없음 |
| 2 | 구조(중복 id·conflict-copy, D13) | 동일 id를 가진 엔티티 파일이 둘 이상 존재, 파일명이 conflict-copy 패턴(`*conflicted copy*`, `* (1).md` 등)에 매치 |
| 3 | 시크릿 스캔 | `secrets/` 바깥에서 시크릿 패턴 검출: `AKIA[0-9A-Z]{16}`, `ASIA[0-9A-Z]{16}`, `-----BEGIN .* PRIVATE KEY-----`, `aws_secret_access_key\s*[:=]`, `ghp_[A-Za-z0-9]{36}`, `github_pat_`, `xox[baprs]-`, `AIza[0-9A-Za-z_-]{35}`, `AGE-SECRET-KEY-1` |
| 4 | 시크릿 정책 | `sharing ≠ local` + `secrets_mode: plaintext` 조합. `secrets_mode: encrypted`인데 secrets/ 파일이 age/SOPS 암호문 헤더가 아님 — **헤더 매직 판별 결과만 출력하고 파일 내용은 절대 출력하지 않는다** |
| 5 | 수신자(recovery 필수, D11) | `secrets_mode: encrypted`인데 `secrets_recipients`에 `recovery` 수신자가 없음(형식이 dict가 아니어도 실패) |
| 6 | 자격증명(kind 어휘·위치 참조, D12) | keys.md 행의 `kind`가 허용 어휘(`ssh-key\|tls-cert\|api-token\|cloud\|account\|password`) 밖, 위치 참조 칸이 비어 있거나 `-` |
| 7 | 보호 설정(settings.json·settings.local.json 드리프트, D15) | `.claude/settings.json` 또는(git 하네스면) `.claude/settings.local.json`이 없거나 secrets/ 차단 deny 규칙이 누락. `secrets_mode: none`이면 경고로만 처리 |
| 8 | 만료 경고 | keys.md에서 만료·로테이션 예정일이 30일 이내(경고, 실패 아님) |
| 9 | harness.yaml(secrets_format 값 검증 포함) | 필수 키 누락, 알 수 없는 sharing/secrets_mode/secrets_format 값. `encrypted`인데 secrets_format 누락 또는 비-encrypted인데 secrets_format이 있으면 경고 |
| 10 | `--staged` 모드(D13) | git staged(ACM) 파일만 대상으로 시크릿 패턴 스캔(pre-commit용). git 저장소가 아니면 일반 audit로 폴백 |

출력: 사람이 읽는 리포트(검사별 통과/실패/경고). 실패가 있으면 종료 코드 ≠ 0.

### 8.2 sync 스크립트

`sync_snapshot.py`: ① 인벤토리 문서를 파싱해 기대 상태 스냅샷 생성 ② 엔티티 메타데이터로 read-only 수집 명령을 생성·실행(--profile/--context 명시) ③ 3종 diff 리포트 출력. 수집 실패는 "확인 불가"로 표기. 스킬(sync)은 이 리포트를 사용자에게 보고하고, 확인받은 항목만 문서에 반영한다.

### 8.3 frontmatter 미니 파서 범위

지원: `key: value`(스칼라), `key: [a, b]`(인라인 리스트), 따옴표 문자열, 주석(`#`). 미지원(중첩 맵 등)은 audit가 "지원하지 않는 구조" 오류로 보고한다. harness.yaml의 `iac.repos`, `policies.mutating` 같은 2단 중첩은 harness.yaml 전용 로더에서 별도 처리한다.

## 9. hooks 설계

`hooks/hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/change_reminder.py"
          }
        ]
      }
    ]
  }
}
```

`change_reminder.py` 흐름:

1. stdin JSON에서 `cwd`, `tool_input.command`를 읽는다.
2. `cwd`에서 harness.yaml 상향 탐색 — 미발견이면 exit 0 (하네스 밖에서는 침묵, D1).
3. `hooks.change_reminder: false`면 exit 0 (원칙 8 — 정책은 데이터).
4. 명령이 mutating 패턴에 매치되면 아래 형태의 JSON을 stdout으로 출력해 리마인드를 컨텍스트에 주입한다(정확한 필드명은 구현 시 공식 hooks 문서로 재확인):

   ```json
   {
     "hookSpecificOutput": {
       "hookEventName": "PostToolUse",
       "additionalContext": "방금 mutating 명령이 실행되었습니다. changes/에 변경 기록을 남기세요 (change 스킬)."
     }
   }
   ```

5. 어떤 오류가 나도 exit 0 — PostToolUse는 사후 실행이므로 절대 차단하지 않는다(D6).

mutating 패턴(기본값, 스크립트 내장). 각 항목은 "매치 → 제외(D6)" 순:

- **terraform**: `apply`, `destroy`, `import`, `taint`, `untaint`, `state mv`, `state rm`, `state push` 매치 → `plan`, `show`는 제외
- **kubectl**: `apply`, `create`, `delete`, `patch`, `replace`, `scale`, `edit`, `label`, `annotate`, `cordon`, `uncordon`, `drain`, `taint`, `rollout restart`, `rollout undo`, `rollout pause`, `rollout resume` 매치 → `rollout status`, `rollout history`, `get`, `describe`, `logs`, `top`, 그리고 `--dry-run` 포함 명령은 제외
- **helm**: `install`, `upgrade`, `uninstall`, `delete`, `rollback` 매치 → `list`, `status`, `get`, `template`은 제외
- **argocd**: `app sync`, `app delete`, `app set`, `app patch`, `app rollback` 매치 → `app list`, `app get`은 제외

## 10. templates/ 목록

init이 복사·치환하는 템플릿. 치환 변수는 `{{id}}`, `{{date}}`, `{{sharing}}` 같은 mustache 스타일 단순 치환.

| 파일 | 용도 |
|------|------|
| `provider.md`, `server.md`, `k8s-cluster.md`, `component.md` | 엔티티 frontmatter 골격 + 본문 작성 안내 주석 |
| `keys.md` | 키 목록 표 헤더 (이름/종류/fingerprint/위치 참조/소유자/생성일/만료일) |
| `change.md` | §4.5 필드 |
| `adr.md` | §4.6 필드 |
| `harness.yaml` | §4.4 골격 |
| `harness-CLAUDE.md` | 하네스 소개, 원칙 요약 포인터, 스킬 자연어 사용 안내, 하네스 변경 이력 섹션 |
| `settings.json` | D3 deny 규칙 |
| `settings.local.json` | 같은 deny 규칙 한 벌 더 — git 저장소 루트에서 로드되어 하위 디렉터리 세션의 구멍을 메운다 (D15) |
| `gitignore` | `secrets/` 선등록 |

## 11. 에러 처리 요약

| 상황 | 동작 |
|------|------|
| 하네스 미발견 | init 외 스킬은 안내 후 중단, hook은 침묵 통과 (D1) |
| harness.yaml 파싱 실패 | audit 실행 안내 |
| 깨진 엔티티 참조 | lookup은 경고 후 가능한 범위로 응답, audit가 정식 검출 |
| CLI 부재 | connect·ops에서 설치 명령 안내 |
| 정책에 없는 env | mutating은 confirm 기본 (D4) |
| sync 수집 실패 | "확인 불가"로 구분 보고 |
| hook 스크립트 오류 | 무조건 exit 0, 세션에 영향 없음 |

## 12. 검증 계획과 완료 기준

완료 기준 13개 시나리오와 검증 방법:

| # | 시나리오 | 방법 |
|---|----------|------|
| 1 | 빈 디렉토리 init → 자동 발견·선택·스캐폴딩 | 수동 (`claude --plugin-dir .`) |
| 2 | init이 sharing/secrets_mode 질문·기록, 모드별 secrets 구성 생성 | 수동 |
| 3 | credentials·kubeconfig raw 미독취, 시크릿 값 미출력 | 수동 (전 과정 관찰) + SKILL.md 명문화 |
| 4 | secrets/ Read 차단, 참조 실행은 정상 | 수동 (실제 Read 시도 — D3) |
| 5 | register 대화형 3종 + 일괄 등록 | 수동 |
| 6 | lookup "prod DB 접속 방법" 정확 응답 | 수동 |
| 7 | ops read 즉시 / prod mutating 승인 / change 초안 / context·profile 명시 | 수동 |
| 8 | sync 3종 diff 보고 | fixture 자동(파서·diff) + 수동(실환경) |
| 9 | audit: AKIA 검출, 무효 정책 조합, 만료 임박, 깨진 참조 | **자동** (`tests/` fixture) |
| 10 | hook 리마인드 on/off | **자동** (stdin JSON 주입 단위 테스트) + 수동 스모크 |
| 11 | 자연어만으로 올바른 스킬 자동 선택 | 수동 (발화 3종: lookup/ops/change) |
| 12 | 스크립트 출력에 시크릿 값이 새지 않는다(시크릿 봉쇄 카나리 회귀) | **자동** (`tests/test_secret_containment.py`) |
| 13 | 문서(스펙·README·CLAUDE.md)가 실제 구현과 어긋나지 않는다(문서 정합성) | **자동** (`tests/test_docs_consistency.py`, Task 7에서 생성) |

`tests/run_tests.sh`: fixture 하네스 4개(`harness-ok`·`harness-bad`·`harness-off`·`harness-onprem`)와 7개 테스트 파일(`test_audit.py`·`test_change_reminder.py`·`test_docs_consistency.py`·`test_harness_lib.py`·`test_secret_containment.py`·`test_skills.py`·`test_sync.py`, 총 132개 테스트)로 ① audit.py 기대 결과(통과/각 실패 항목) ② change_reminder.py 케이스(mutating / read-only / --dry-run / reminder off / 하네스 밖) ③ harness_lib의 하네스 상향 탐색·frontmatter 파서 ④ 스크립트 출력의 시크릿 봉쇄 카나리(원칙 1 회귀 방지) ⑤ SKILL.md frontmatter·본문 규약 ⑥ sync의 문서 스냅샷 파서·diff 로직(모의 수집 데이터 주입)을 assert한다. 수동 시나리오는 README에 체크리스트로 수록한다.

구현 각 단계 완료 시 `tests/run_tests.sh`를 실행한다.

## 13. 구현 순서

1. 스키마·템플릿 확정 (`templates/`) — 이후 모든 스킬의 기반
2. init (자동 발견 → 인터뷰 → 스캐폴딩)
3. register / lookup
4. change / decide
5. connect / ops (references 4종 포함)
6. sync / audit (scripts/ 포함, tests/ fixture 동시 작성)
7. hooks (단위 테스트 포함)
8. 검증 시나리오 통과 확인 → README 작성

## 부록 A. 플랫폼 스펙 확인 결과 (2026-07 문서 기준)

구현 시 아래를 전제로 하되, 정확한 필드명은 구현 시점에 공식 문서로 재확인한다.

- 플러그인 매니페스트: `.claude-plugin/plugin.json`, 필수 필드는 `name`(소문자·하이픈). `version` 미지정 시 git SHA가 버전으로 쓰임.
- 스킬: `skills/<name>/SKILL.md` 자동 발견 → `/infra:<name>`으로 노출. `description`이 자동 선택을 결정. `disable-model-invocation` 지원(본 플러그인은 사용하지 않음 — 자동 선택이 기본 사용 형태). `references/` 등 부속 파일은 자동 로드되지 않고 본문에서 참조 시 온디맨드 로드.
- hooks: 플러그인 루트 `hooks/hooks.json` 자동 로드. PostToolUse stdin에 `cwd`, `tool_name`, `tool_input.command`, `tool_response` 포함. exit 0 + stdout JSON의 `additionalContext`가 컨텍스트로 주입. PostToolUse에서 exit 2는 차단 효과 없음(이미 실행됨).
- permissions 경로 앵커: `//path`=절대 경로, `~/path`=홈, `/path`=설정 파일 위치(프로젝트 루트) 기준, `path`·`./path`=cwd 기준. 하네스 설정에는 `Read(/secrets/**)`(프로젝트 기준)와 `Read(./secrets/**)`(cwd 기준)를 병기(D3).
- 로컬 개발: `claude --plugin-dir .`, 세션 내 `/reload-plugins`. 같은 이름의 설치된 플러그인보다 로컬이 우선.
- `${CLAUDE_PLUGIN_ROOT}`: hooks 명령과 스킬 본문 모두에서 사용 가능. `templates/`·`scripts/` 등 임의 디렉토리 접근 가능.

참고 문서:
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/permissions

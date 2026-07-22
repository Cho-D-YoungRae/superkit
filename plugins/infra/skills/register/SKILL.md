---
name: register
description: 인프라 하네스 인벤토리에 서버·k8s 클러스터·컴포넌트·provider·키 메타데이터를 등록해 엔티티 파일을 만든다. "이 서버 등록해줘", "클러스터 추가해줘", 서버 목록·스프레드시트를 붙여넣는 일괄 등록 요청에 사용. 스캔으로 후보를 먼저 제안한다. 등록된 것 조회는 lookup, 하네스 골격 생성은 init, 문서-실제 대조는 sync.
---

# register — 인프라 엔티티 등록

하네스 인벤토리에 서버·k8s 클러스터·컴포넌트·provider·키 메타데이터를 개별(대화형) 또는
일괄로 등록해 엔티티 파일(및 `access/keys.md` 행)을 만든다. 등록 전에 로컬/원격에서 스캔
가능한 정보를 먼저 확인해 후보로 제안하고, 사용자 확인을 거친 값만 파일로 남긴다. 이미
등록된 것을 찾는 작업은 lookup, 하네스 자체가 없을 때의 골격 생성은 init, 문서와 실제 상태의
대조는 sync가 맡는다 — register는 항상 "새 엔티티 파일 하나(또는 여러 개)를 만드는" 작업만
한다.

## 1. 적용 원칙

이 스킬이 반드시 지키는 원칙(전 스킬 공통 원칙 중 register에 해당하는 항목)은 다음 세
가지다.

- **원칙 1 — 키는 위치 참조만 기록**: `access/keys.md`와 각 엔티티의 `access` 필드에는
  키·토큰·인증서의 **값을 절대 적지 않는다**. 기록하는 것은 종류·fingerprint·위치
  참조(`~/.ssh/deploy-key`, `secrets/vm-token.txt`, `op://vault/item` 등)·소유자·생성일·
  만료일 같은 메타데이터뿐이다. 인터뷰 중 사용자가 값(토큰 문자열, 개인키 내용 등)을
  붙여넣으려 해도 그 값을 파일에 옮겨 적지 않고 "값이 저장된 위치"를 대신 묻는다.
- **원칙 3 — 묻기 전에 스캔**: k8s-cluster 등록 직후의 컴포넌트 후보, server 등록 시의
  실행 중 서비스 후보처럼 로컬·원격에서 스캔 가능한 정보는 §4에 따라 먼저 스캔해 후보를
  제안하고, 사용자에게는 확인·선택만 받는다. 처음부터 빈 화면에 타이핑을 요구하지 않는다.
- **원칙 5 — managed_by는 엔티티별**: `managed_by`는 하네스 전역 설정이 아니라 등록하는
  개별 엔티티(server/k8s-cluster)마다 인터뷰로 확정한다(`terraform://org/repo//module`
  경로 또는 `manual`). 같은 하네스 안에 terraform 관리 엔티티와 manual 엔티티가 섞여
  있어도 정상이며, register는 이를 강제로 통일하려 하지 않는다.

## 2. 공통 규약

등록을 시작하기 전에 항상 cwd에서 상위 디렉터리 방향으로 `harness.yaml`을 상향 탐색해
`HARNESS_ROOT`를 정한다(전 스킬이 공유하는 하네스 발견 규약). 탐색해도 `harness.yaml`을
찾지 못하면 등록을 진행하지 않는다 — "하네스 디렉터리에서 세션을 열거나 init으로 하네스를
먼저 생성하세요"라고 안내하고 중단한다.

## 3. 대화형 모드

한 건씩 등록한다.

1. `AskUserQuestion`으로 등록할 `type`을 고른다: `server` / `k8s-cluster` / `component` /
   `provider` / `key`.
2. `key`가 아니면 `${CLAUDE_PLUGIN_ROOT}/templates/<type>.md` 골격을 읽어 필수 필드를
   확인하고(예: server면 `id/env/provider/runtime/purpose/access/managed_by`),
   `AskUserQuestion`으로 한 턴에 2~3개씩 인터뷰한다. §4의 스캔으로 이미 확인된 값은 다시
   타이핑을 요구하지 않고 "이 값이 맞습니까?" 확인만 받는다.
3. 확정되면 `id`를 파일명(stem)으로 그대로 사용해 생성한다: `provider` →
   `providers/<id>.md`, `server`/`k8s-cluster` → `inventory/<id>.md`, `component` →
   `inventory/components/<id>.md`. 템플릿의 `{{변수}}`를 인터뷰 값으로 채우고, 해당 없는
   선택 필드는 템플릿 주석 지시대로 그 줄을 삭제한다.
4. `type`이 `server`이면 3에서 만든 파일의 frontmatter뿐 아니라 **본문**도 인터뷰·스캔으로
   확인된 값으로 채운다. 본문의 관례 섹션(`## 네트워크`/`## 사양`/`## 특이사항`)에서 값이
   없는 항목이나 섹션은 비워두지 말고 그 줄(또는 섹션 전체)을 지운다(스펙 D10 — 관례
   섹션은 권장일 뿐 강제 스키마가 아니다). 사설/공인 IP·아키텍처·사양·서버별 특이사항은
   frontmatter 필드가 아니라 본문에 자유 서술한다 — 사용자가 frontmatter 필드에 없는
   정보를 주면 해당하는 본문 섹션(없으면 새 섹션)에 적는다. 클라우드 provider로 등록하는
   서버라면 `aws ec2 describe-instances --profile <p> --region <r>` / `gcloud compute
   instances describe --configuration <c>` 같은 **read-only** 명령으로 IP·아키텍처 후보를
   조회해 제안할 수 있다(원칙 6 — profile/region을 항상 명시). 조회 결과 중 사용자가
   채택한 값만 본문에 기록한다. ssh 접근이 있는 서버의 `## 사양`(arch·vCPU·메모리·디스크)
   수집 절차는 §4를 따른다.
5. `key`는 새 엔티티 파일을 만들지 않는다 — `access/keys.md` 표에 9컬럼(이름 / kind /
   principal / fingerprint / 위치 참조 / usage / 소유자 / 생성일 / 만료·로테이션, D12) 행을
   추가한다. **`access/keys.md`가 아직 없으면**(init은 `access/` 디렉토리만 만들고
   `keys.md`는 만들지 않는다) 먼저 `${CLAUDE_PLUGIN_ROOT}/templates/keys.md`를 그 경로로
   복사해 파일을 만든 뒤(헤더 + 빈 표) 첫 행을 추가한다(폴백). `kind`는 `ssh-key |
   tls-cert | api-token | cloud | account | password` 중 하나를 인터뷰로 확정한다(audit가
   이 어휘를 검증한다).
   - **계정·비밀번호 등록**(`kind: account`/`password`): `principal`(계정명·사용자명)을
     인터뷰로 묻는다. 값(비밀번호 문자열 등)은 어떤 경우에도 keys.md에 적지 않고, 값이
     저장된 위치만 `위치 참조`에 적는다(원칙 1). `usage` 컬럼에는 안전한 참조 실행
     방법을 적되 **argv 형태는 절대 제시하지 않는다**(ps·셸 히스토리로 유출된다) —
     `sops exec-env <파일> '<명령>'` · `op run -- <명령>` · stdin/FD로 넘기는 형태만
     쓴다. SSH 비밀번호 로그인이 필요하면 키 인증 전환을 권하고 `sshpass` 같은 도구는
     도입하지 않는다 — 불가피하게 비밀번호 로그인을 유지해야 한다면 그 제약을 `usage`에
     그대로 적어(예: "sshpass 없이는 자동화 불가 — 수동 로그인만 가능") 사용자가 위험을
     인지하게 한다.
   - **외부 매니저 참조**(D14): 값이 1Password·HashiCorp Vault·AWS Secrets Manager 등
     외부에 있으면 `위치 참조`에 해당 스킴을 그대로 적는다 — `op://vault/item/field` ·
     `vault://mount/path` · `aws-secretsmanager://secret-id` · 하네스 내부는
     `secrets/파일명.age`. 이 참조는 **불투명하게** 다룬다 — register는 등록 시점에 그
     값을 조회·검증하지 않고, 사용자가 부른 참조 문자열을 그대로 옮겨 적을 뿐이다.

## 4. 스캔 우선

등록 대상에 따라 다음 스캔을 먼저 실행해 후보를 표로 제시하고, 실제 등록 여부는 사용자
확인을 받는다.

- **k8s-cluster 등록 직후**: 방금 등록한 클러스터의 `context`를 사용해
  `helm --kube-context <c> list -A`와 `kubectl --context <c> get ns`를 실행하고, 결과를
  컴포넌트 후보 표(release/namespace/chart 등)로 제안한다. 채택된 항목만 §3의 component
  등록 절차로 이어간다.
- **server 등록 시**: 등록 중인 서버의 `access`에 ssh 정보가 있으면, **사용자 동의를
  받은 뒤** `ssh -i <키경로> <호스트> 'systemctl list-units --type=service --state=running;
  docker ps --format {{.Names}}'`로 실행 중인 서비스·컨테이너를 스캔해 컴포넌트 후보로
  제안한다. `<키경로>`는 값이 아니라 `access/keys.md`의 위치 참조 컬럼 값을 그대로 조립해
  넣는다 — 이 스캔 과정에서도 키 값 자체는 어디에도 노출하지 않는다(원칙 1). 같은 동의
  아래 `## 사양` 본문 후보도 수집할 수 있다 — 대상 호스트를 명시해(원칙 6) 아래
  **read-only allowlist** 명령만 사용한다: `ssh -i <키경로> -o BatchMode=yes -o
  ConnectTimeout=5 <사용자>@<호스트> 'uname -m; nproc; free -h 2>/dev/null | head -2; df -h
  --total 2>/dev/null | tail -1; lsblk -d -o NAME,SIZE 2>/dev/null'`. 이때도 `<키경로>`는
  `access/keys.md` 위치 참조 컬럼 값을 조립한 것일 뿐, 키 값 자체는 여기서도 노출하지
  않는다(원칙 1). **금지**: `sudo`, 환경변수 덤프(`env`/`printenv`), 클라우드 메타데이터
  엔드포인트(`169.254.169.254`), 프로세스 커맨드라인, 설정·자격증명 파일 열람.
  `StrictHostKeyChecking=no`는 붙이지 않는다(정상 host-key 검증 유지). 수집 결과 중
  `arch`만 확정 사양으로 `## 사양`에 남기고, vCPU·메모리·디스크는 `<!-- YYYY-MM-DD(등록
  시점 오늘 날짜) 수집 참고값, 런타임 관측치라 이후 달라질 수 있음 -->`처럼 수집 시각
  기준 참고값임을 주석으로 남긴다 — 하네스는 상태를 복제하는 엔진이 아니라 지도이기
  때문이다(원칙 4). 온프렘·baremetal 서버는 하드웨어가 사실상 불변이므로 참고값 주석
  없이 그대로 기록해도 무방하다. 일괄(batch) ssh 수집은 **대상 호스트 전체 목록을
  확인받은 뒤에만** 실행한다 — 열린 서브넷이나 인벤토리 전체 스윕은 금지한다.

## 5. 일괄 모드

서버 목록·스프레드시트 텍스트를 붙여넣아 여러 건을 한 번에 등록한다.

1. 붙여넣은 텍스트에서 열을 추정한다(`id`, `env`, `purpose`, `provider`, `runtime` 등 —
   헤더 유무·구분자(탭/쉼표/공백)는 유연하게 해석한다).
2. 추정 결과를 초안 표로 사용자에게 제시한다(아직 파일을 만들지 않은 상태).
3. 사용자가 확인하거나 정정하면, 그 결과를 그대로 반영해 일괄 생성한다(§3과 동일하게
   `id`=파일명 규칙 적용).
4. 생성 결과를 요약 보고한다 — 생성 건수, 각 파일 경로, 건너뛴 항목과 그 사유.

## 6. 검증

- 등록하려는 엔티티의 `env`가 `harness.yaml`의 `environments`에 없으면, 목록에 추가할지
  사용자에게 확인한다.
- 대화형·일괄 등록을 마친 뒤에는 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py` 실행을
  권고해 스키마·참조·정책 위반을 바로 확인하게 한다.

## 7. 명명 규약

sync는 문서와 실제 상태를 **id 기준**으로 대조하므로, 등록 시 다음 일치를 안내한다.

- 컴포넌트 `id`는 helm 릴리스 이름과 일치시킨다.
- 서버 `id`는 클라우드 Name 태그와 일치시킨다.

이 규약을 어기면 실제로는 같은 대상인데도 sync 실행 시 "실제에만 있음(문서 누락)"이나
"문서에만 있음(유령)"으로 잘못 보고될 수 있다는 점을 등록 시점에 미리 설명한다.

## 8. MCP 구성 (스펙 §4.3)

컴포넌트 접근에 MCP를 쓰는 경우(예: victoria-metrics MCP), `.mcp.json` 같은 MCP 구성
파일은 하네스 안에 보관한다(컴포넌트 `access` 메타데이터의 연장으로 취급). 단 토큰 등 값은
구성 파일에 `${VM_TOKEN}` 같은 환경변수 참조로만 쓰고 값 자체를 구성 파일에 적지 않는다 —
그 값을 실제로 어디에 어떻게 보관할지는 `secrets_mode`(원칙 2)를 그대로 따른다.

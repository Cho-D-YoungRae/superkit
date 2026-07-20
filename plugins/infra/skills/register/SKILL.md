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
4. `key`는 새 엔티티 파일을 만들지 않는다 — `access/keys.md` 표에 (이름 / 종류 /
   fingerprint / 위치 참조 / 소유자 / 생성일 / 만료·로테이션) 행을 추가한다. **`access/keys.md`가
   아직 없으면**(init은 `access/` 디렉토리만 만들고 `keys.md`는 만들지 않는다) 먼저
   `${CLAUDE_PLUGIN_ROOT}/templates/keys.md`를 그 경로로 복사해 파일을 만든 뒤(헤더 +
   빈 표) 첫 행을 추가한다(폴백).

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
  넣는다 — 이 스캔 과정에서도 키 값 자체는 어디에도 노출하지 않는다(원칙 1).

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

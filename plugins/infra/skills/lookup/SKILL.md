---
name: lookup
description: 인프라 하네스(서버·k8s 클러스터·컴포넌트·키 인벤토리)에서 접속 방법·위치·구성 정보를 조회해 답한다. "prod DB 어떻게 붙어?", "argocd 어디 떠 있어?", "vm 토큰 어디 있어?" 같은 질문에 사용. 키·토큰은 값이 아니라 위치 참조와 사용 명령만 답한다. 명령 실행은 ops, 로컬 접근 재구성은 connect, 새 엔티티 등록은 register.
---

# lookup — 인프라 하네스 조회

하네스(서버·k8s 클러스터·컴포넌트·키 인벤토리)에서 접속 방법·위치·구성 정보를 찾아 답하는
조회 전용 스킬이다. 아무 파일도 새로 만들거나 고치지 않는다 — 이미 있는 문서를 읽고
조합해서 답할 뿐이다. 명령을 실제로 실행해 상태를 확인하고 싶으면 ops, 로컬 kubeconfig 등
접근을 재구성하고 싶으면 connect, 아직 등록되지 않은 대상을 새로 등록하려면 register를
안내한다.

## 1. 적용 원칙

이 스킬이 반드시 지키는 원칙은 다음 두 가지다.

- **원칙 1 — 값 대신 위치 참조 + 사용 명령**: 키·토큰을 묻는 질문에도 값 자체를 절대 읽거나
  출력하지 않는다. 항상 "위치 참조 + 그 값을 참조 실행으로 사용하는 명령" 형태로 답한다.
  예: "vm 토큰은 `secrets/vm-token.txt`에 있고, `curl -H "Authorization: Bearer ${VM_TOKEN}"`
  형태로 사용하세요." `VM_TOKEN=$(cat secrets/vm-token.txt)`처럼 값을 변수에 담아 화면에
  노출시키거나 그대로 출력하라는 지시는 어떤 형태로도 하지 않는다 — 셸 히스토리·로그·
  대화 컨텍스트에 값이 그대로 남기 때문이다.
- **원칙 4 — 하네스는 색인이지 엔진이 아니다**: 하네스 문서는 참고용 지도이며, "지금 실제로
  떠 있는지" 같은 실시간 상태의 SSOT가 아니다. "지금 살아있어?", "실제로 정상이야?"처럼
  실제 상태를 묻는 질문을 받으면, 문서 조회 결과를 답한 뒤 "실제 상태 확인은 ops로
  `kubectl --context <c> get pods` 같은 명령을 실행해 보자"고 제안한다.

## 2. 절차

1. 먼저 cwd에서 상위 디렉터리 방향으로 `harness.yaml`을 상향 탐색해 `HARNESS_ROOT`를
   정한다(전 스킬이 공유하는 하네스 발견 규약). 찾지 못하면 조회를 진행하지 않고 "하네스
   디렉터리에서 세션을 열거나 init으로 하네스를 먼저 생성하세요"라고 안내한 뒤 중단한다.
2. 질의에서 키워드(엔티티 id·이름·종류 등)를 뽑아 `providers/`, `inventory/`
   (`inventory/components/` 포함), `access/keys.md`를 검색(grep)해 관련 엔티티·행을
   찾는다.
3. 찾은 엔티티의 frontmatter, 그 엔티티가 참조하는 provider의 `cli_profile`/`context`,
   관련 `keys.md` 참조(엔티티 `access` 필드의 `keys.md#이름` 앵커가 가리키는 행)를 조합해
   답을 구성한다.
4. 접근 방법을 묻는 질문이면 값이 아니라 그대로 실행 가능한 명령 형태로 제시한다. 예:
   `ssh -i ~/.ssh/deploy-key ec2-user@<host>`, `kubectl --context prod-k8s get pods -n
   monitoring`. 명령에는 항상 엔티티에 기록된 context/profile을 명시하고, 현재 kubectl
   컨텍스트나 기본 aws profile에 의존하는 형태로는 답하지 않는다.
5. 서버의 사양·IP·특이사항을 묻는 질의(예: "prod-db-01 사양 알려줘", "그 서버 사설 IP
   뭐야?")에는 frontmatter뿐 아니라 엔티티 본문의 관례 섹션(`## 네트워크`/`## 사양`/
   `## 특이사항`)까지 읽어 답한다(스펙 D10 — 이 정보는 frontmatter 필드가 아니라 본문에
   자유 서술돼 있다). IP·사양·아키텍처 값은 시크릿이 아니므로 본문에서 찾은 값을 그대로
   답해도 된다 — 원칙 1은 키·토큰·인증서의 값에만 적용되고 IP·사양은 그 대상이 아니다.
   단 같은 흐름에서 키·토큰을 물으면 종전대로(§1 원칙 1) 값이 아니라 위치 참조와 사용
   명령만 답한다. 본문에 해당 섹션이나 항목 자체가 없어 답을 찾을 수 없으면 "하네스에
   기록돼 있지 않다"고 답하고, 실제 값이 필요하면 ops로 실측 조회(예: ssh로 `uname -m`,
   클라우드 `describe-instances`)를 제안한다 — 값을 지어내 답하지 않는다(원칙 4).
6. 키·토큰·비밀번호를 묻는 질의는 `access/keys.md`에서 찾은 행의 **위치 참조 + `usage`
   컬럼에 적힌 참조 실행 레시피**를 그대로 답한다(원칙 1, D12) — 값 자체는 절대 조회·
   출력하지 않는다. `usage` 컬럼이 비어 있지 않으면 그 명령을 그대로 안내하고, 비어
   있으면 `kind`에 맞는 기본 레시피를 제안한다(예: `sops exec-env <위치 참조> '<명령>'`).
   비밀번호 계열(`kind: account`/`password`)은 어떤 경우에도 argv 형태(`--password
   1234`, `mysql -p1234`, `curl -u user:1234` 등)를 제시하지 않는다 — `sops exec-env
   <파일> '<명령>'` · `op run -- <명령>` · stdin/FD로 넘기는 형태만 안내한다. 위치
   참조가 `op://`·`vault://`·`aws-secretsmanager://` 같은 외부 매니저 스킴이면(D14) 그
   백엔드의 참조 실행 명령을 안내한다 — `op run -- <명령>`(1Password), `vault kv get
   -mount=<mount> <path>`(HashiCorp Vault, `VAULT_ADDR`/`VAULT_NAMESPACE`를 명시),
   `aws secretsmanager get-secret-value --secret-id <id> --profile <p> --region <r>`
   (AWS Secrets Manager)처럼 profile/region/namespace를 항상 명시적으로 붙인다(원칙 6).
   lookup은 이때도 명령을 대신 실행하거나 값을 조회·출력하지 않는다 — 안내만 하고 실행은
   사용자의 몫이다. 백엔드별 상세 관례(플래그, 인증 전제조건 등)는 `secrets` 스킬의
   `references/backends.md`를 참조하도록 안내한다.

## 3. 에러 처리

- 참조가 깨진 경우(예: `keys.md#앵커`가 `access/keys.md`에 없음, `provider`/`runs_on`이
  가리키는 엔티티 파일이 없음)에는 그 사실을 경고로 답변에 포함하고, 나머지 확인 가능한
  정보만으로 가능한 범위까지 답한다. 이어서 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py`
  실행을 권고해 참조 무결성을 정식으로 점검하게 한다.
- 질의한 엔티티 자체가 인벤토리에 없으면 "해당 엔티티를 찾을 수 없다"고 답하고, 필요하면
  register로 등록하라고 안내한다.

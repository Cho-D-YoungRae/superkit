# infra 플러그인 검토 보고서

- 작성일: 2026-08-06
- 검토 대상: 워크트리 `.claude/worktrees/infra-plugin-impl`, 브랜치 `feat/infra-plugin`, **기준 커밋 `ec22855`**
- 판정 준거: **오픈소스 범용성** (특정 개인 환경 최적화 관점 아님)
- 검증 방법: 정적 분석 + 스텁 CLI 격리 하네스 모의 구동(카나리 프로토콜 실측) + 외부 리서치
- 범위 밖: 스펙 개정, 플러그인 구현 변경, 실제 인프라 접속, marketplace 배포

> 이 보고서는 **판정과 권고까지만** 한다. 스펙 개정·구현 변경은 §4의 D 결정 후보를 채택한 뒤 별도 작업으로 진행한다.

> **후속 조치 (2026-08-06)**: §4의 **P0 4건은 이후 조치되었다** — 워크트리 `feat/infra-plugin`에
> 반영했고 스펙에 **D15**로 기록했다. 아래 본문은 기준 커밋 `ec22855` 시점의 판정을 그대로
> 보존한 것이므로, P0 항목을 읽을 때는 조치 이후 상태와 다르다는 점에 유의한다.
> P1·P2는 아직 열려 있다.

---

## 0. 요약

77개 자동 테스트가 전부 통과하는, 설계 원칙이 코드까지 일관되게 내려온 플러그인이다. 특히 **시크릿을 다루는 방식은 실측으로 검증된다** — 플러그인 자신의 스크립트·hook·git 경로 어디로도 시크릿 값이 새지 않았다(§3). 인벤토리 모델은 온프렘 전용부터 멀티 클라우드까지 5개 환경 프로파일에서 그대로 성립했다.

한계는 두 갈래다. 첫째, **커버리지가 k8s·GitOps 축에 편중**돼 있어 백업·복구, 로그 조회, DNS·인증서 갱신, DB 설치·튜닝, 비-k8s 클러스터(카프카·DB active-standby)는 담당 스킬 자체가 없다. 둘째, **시크릿 "생성·내보내기" 방향이 비어 있다** — 기존 값을 안전하게 쓰는 규약은 정교한데, 새 자격증명을 만들어 최초 저장하거나 값을 담은 설정을 다른 프로젝트에 전달하는 경로는 설계에 없다.

가장 시급한 것은 P0 네 건이다. `audit.py`가 특정 입력에서 크래시해 **시크릿 스캔 자체가 수행되지 않는 경로**가 있고(P0-1), README FAQ가 방어선 강도를 **실측과 다르게 과대 주장**한다(P0-2). 그리고 방어선 자체에 구조적 한계가 둘 있다 — **하네스 하위 디렉터리에서 세션을 열면 deny 규칙이 아예 로드되지 않고**(P0-3, 하네스 발견은 상향 탐색인데 설정 로드는 부모 폴백이 없어서 생기는 비대칭), **플러그인 자신의 파이썬 스크립트는 deny 적용 대상이 아니다**(P0-4). 넷 다 문서·설정·테스트 층위에서 해소 가능하며 구조 재설계를 요구하지 않는다.

한편 외부 리서치는 이 플러그인의 방향을 뒷받침한다. 원칙 1·2는 2026-08-04 발행된 **OWASP LLM08:2026 Hidden Context Exposure**("컨텍스트 안의 어떤 것도 비밀로 간주해서는 안 된다")와 Anthropic·HashiCorp의 공식 아키텍처가 수렴하는 지점과 정확히 일치한다. 그리고 "온프렘 물리 서버 인벤토리 + 비-k8s 클러스터 역할 모델링 + read-only 기본 AI 운영"의 조합은 NetBox·Ansible·Backstage 어디에도 없는, 실제로 비어 있는 자리다.

---

## 1. 원질문 8건 판정

### 판정 루브릭

이 절의 등급은 아래 경계를 따른다. 준거는 **오픈소스 범용성**이며, 사용자 개인 환경에 대입한 결론은 내지 않는다(비목표).

| 등급 | 경계 |
|---|---|
| ✅ | 담당 스킬·절차가 존재하고, 대표 환경 프로파일 대부분에서 실측 또는 문서 근거로 성립한다 |
| ⚠️ | 절차가 있으나 특정 환경·시나리오에서 성립하지 않거나, 핵심 조각이 빠져 사람이 메워야 한다 |
| ❌ | 담당 스킬·절차가 없다 (언급만 있는 경우 포함) |

- **"용이성"의 비교 기준**: 순수 CLI 수동 운영(사람이 직접 `kubectl`/`ssh`를 치고 위키에 기록) 대비 마찰이 줄어드는가.
- **Q1은 서술형**이다. "현재 어떻게 쓰고 있는가"는 좋고 나쁨을 가릴 명제가 아니라 사실 기술이므로 등급을 매기지 않는다.

### Q1. 현재 플러그인을 어떻게 사용하고 있는가 (서술형)

**사실 기술.** 사용 형태는 두 층으로 나뉜다.

- **플러그인**(이 저장소)은 재사용 도구다. 그 자체에는 어떤 인프라 정보도 없다.
- **하네스 인스턴스**는 실제 데이터가 담기는 별도 저장소 1개다. `init` 스킬이 스캐폴딩한다.

기본 사용 경로는 **하네스 디렉터리에서 세션을 열고 자연어로 말하는 것**이다. 모든 스킬이 cwd에서 루트 방향으로 `harness.yaml`을 상향 탐색해 `HARNESS_ROOT`를 정하고(D1), 하네스를 못 찾으면 `init`을 제외한 스킬은 안내 후 중단한다. 슬래시 호출(`/infra:lookup` 등)은 보조 경로다.

스킬은 10종이며 전부 한국어 `description`에 ①역할 ②트리거 발화 예시 ③인접 스킬 경계를 담아 클로드가 대화 흐름에서 스스로 고르도록 설계됐다.

| 스킬 | 역할 |
|---|---|
| `init` | 하네스 스캐폴딩 / 기존 하네스 점검·확장 |
| `register` | 서버·클러스터·컴포넌트·provider·키 등록 |
| `lookup` | 접속 방법·위치·구성 조회 |
| `connect` | `access_recipe` 실행으로 로컬 접근 재구성 |
| `ops` | context/profile 명시 명령 실행 (read/mutating 분리) |
| `change` | 변경 기록 (`changes/`, append-only) |
| `decide` | ADR 기록 (`decisions/`) |
| `sync` | 문서 vs 실제 상태 drift 대조 |
| `audit` | 하네스 문서 정합성 검증 |
| `secrets` | 팀 시크릿(SOPS+age) 라이프사이클 |

여기에 `PostToolUse` hook 1종이 붙어 mutating 명령 실행 후 기록을 유도한다.

### Q2. Vault로 대응 가능한가 — ✅ (환경별 혼재는 ⚠️)

**가능하다.** D14가 `access/keys.md`의 위치 참조에 `vault://<mount>/<path>` 스킴을 규정하고, `skills/secrets/references/backends.md`가 사용 규약을 담고 있다. 규약의 품질이 특히 높다:

- **항상 `-field=<key>`로 특정 필드만** 뽑아 환경변수 대입이나 파일 리다이렉트로만 쓴다 — `-field` 없이 `vault kv get`을 실행하면 시크릿 전체가 stdout에 테이블로 출력되기 때문이다.
- `VAULT_ADDR`/`VAULT_NAMESPACE`를 환경변수나 플래그로 **반드시 명시**한다(원칙 6 — 현재 셸 기본값 암묵 의존 금지).
- argv에 값을 절대 넣지 않는다(`ps`·셸 히스토리 유출 방지).
- 인증(`vault login`)은 사용자가 사전 구성한 것을 전제하고, 스킬이 토큰을 대신 발급·저장하지 않는다.

실측으로도 확인했다. 프로파일 P3(멀티 클라우드 + `vault://` 참조 + `secrets_mode: none`)에서 audit 실패 0건으로 통과했다(§3 프로파일 표).

**⚠️ 단서 — 환경별 혼재는 표현할 자리가 없다.** `secrets_mode`는 `harness.yaml`의 **전역 단일 스칼라**이고, `keys.md` 9컬럼에도 env 컬럼이 없다. "prod 키는 Vault, dev 키는 로컬 암호문"은 키 이름이나 앵커 관례로만 암시할 수 있을 뿐 기계가 읽을 수 없다. 다만 설계 의도 자체는 혼재를 허용한다 — backends.md가 "전역 `secrets_backend` 설정은 없다 … 한 하네스 안에 `secrets/…`와 `op://…`가 섞여 있어도 정상"이라고 명시한다. 즉 **참조 단위 혼재는 되지만 환경 단위 정책 분기는 안 된다.**

### Q3. Vault가 없을 경우 MCP를 만들어 쓰는 것은 어떤가 — ⚠️ (조건부 유효, 1단계는 MCP 불필요)

**현행 대응**: Vault 없이도 자체 관리가 성립한다. `sharing: local`이면 `secrets/`에 평문 보관, 공유 모드면 SOPS+age 암호화만 허용하며, D11이 팀 라이프사이클(수신자 추가·`sops updatekeys`·오프보딩 시 재키잉과 자격증명 로테이션·복구 수신자 필수)까지 규정한다. 금지 조합(공유+평문)은 audit이 실측으로 잡아낸다(§3 P5).

**MCP 동봉안의 판정은 §3 말미**에 있다. 결론만 옮기면: 시크릿 영역에 P0·P1 갭이 존재하므로 트리거가 발동해 설계안을 포함하되, **1단계에서 MCP는 필수가 아니다.** 값이 컨텍스트를 거치지 않게 하는 데 필요한 것은 "값을 반환하지 않는 실행 경계"이고, 그것은 플러그인 동봉 python3 stdlib 스크립트로도 동일하게 달성된다(D2 제약도 그대로 지킬 수 있다). MCP가 추가로 주는 것은 도구 단위 권한 게이팅과 장기 세션 상태이며, 그 값이 필요해지는 시점에 2단계로 올리는 편이 낫다. 플랫폼이 플러그인의 MCP 동봉을 지원하므로 두 단계는 연속적이다(§6.1).

**질문의 다른 갈래 하나를 분리해 둘 필요가 있다.** "MCP를 만들어 쓴다"에는 ①시크릿을 다루는 자체 MCP와 ②컴포넌트 접근용 MCP(victoriametrics 등)가 섞여 있는데, 후자는 **만들 필요가 없다.** VictoriaMetrics·VictoriaLogs 모두 1st-party MCP 서버가 이미 존재하고 write 기능이 아예 구현돼 있지 않아 read-only이며, 인증은 bearer token 하나뿐이다(§6.3.3). 자체 제작이 아니라 연결·안내가 과제다.

### Q4. 서버 사양은 하네스에서 관리할지, 필요할 때마다 조회할지 — ⚠️ (D10 조건 충족, 부분 승격 권고)

**현행(D10)**: 사양·IP·특이사항은 frontmatter가 아니라 **엔티티 본문에 자유 서술**한다. `templates/server.md`가 `## 사양` / `## 네트워크` / `## 특이사항` 관례 섹션을 권장하되 강제하지 않고, **audit은 본문을 검사하지 않는다**. `lookup`은 본문까지 읽어 답하고, 값이 없으면 지어내지 않고 `ops` 실측 조회를 제안한다. `register`는 수집한 vCPU·메모리·디스크에 "런타임 관측치라 이후 달라질 수 있음"이라는 주석을 달도록 지시한다.

**판정 술어**: D10 자신이 "스킬이 특정 값을 **결정론적으로 소비해야 할 때에만** 그 값을 frontmatter로 승격한다"는 조건부 규칙이므로, 판정은 그 조건의 충족 여부로 환원된다.

**충족됐다.** 필수 시나리오 중 "서버 사양 기반 DB 튜닝"(예: RAM에서 `innodb_buffer_pool_size` 산출)은 정의상 사양 값을 기계가 읽어 계산해야 한다. 현행 데이터 모델에서 그 값은 파싱 대상이 아닌 자유 텍스트이고, 오히려 신뢰도를 낮추는 주석이 붙는다. 따라서 이 시나리오는 현행 구조 위에서 결정론적으로 수행될 수 없다.

**업계 관행이 이 판단을 뒷받침한다** (§6.3.1). NetBox는 물리 `Device`에 CPU·RAM·디스크 필드를 두지 않으면서 `VirtualMachine`에는 `vCPUs`·`Memory`·`Disk`를 1급 필드로 둔다. 즉 "사양을 구조화할지"는 전부-아니면-전무가 아니라 **대상에 따라 갈리는 문제**로 다뤄지고 있다.

**권고 — 전면 승격이 아니라 최소 승격.** 원칙 4(하네스는 상태를 복제하지 않는다)를 지키면서 조건을 만족시키는 절충은:

- 클라우드 서버는 `instance_type`을, 온프렘·베어메탈은 `spec_vcpu`/`spec_ram_gb`를 **frontmatter 선택 필드**로 승격한다. 전자는 사양의 원천(instance type)만 담아 상태 복제를 피하고, 후자는 하드웨어가 사실상 불변이라 복제 문제가 약하다.
- 승격한 값을 소비하는 시점(튜닝 등)에는 `ops` 실측 재확인을 **필수 단계로 강제**한다. 하네스 값은 계산의 출발점이지 최종 근거가 아니다.
- 나머지(디스크 구성·네트워크·특이사항)는 D10 현행대로 본문에 남긴다.

### Q5. SSH로 에이전트가 직접 서버에 접속하는 것이 용이한가 — ✅ (ops 분류표 부재는 ⚠️)

**용이하다.** `register`가 동의 기반 SSH 수집 절차를 갖췄고, 설계가 방어적이다.

- 실행 형태: `ssh -i <keys.md 위치 참조> -o BatchMode=yes -o ConnectTimeout=5 <사용자>@<호스트> '<allowlist 명령>'` — 키는 **값이 아니라 위치 참조**를 그대로 `-i`에 조립한다.
- allowlist: `uname -m`, `nproc`, `free -h`, `df -h --total`, `lsblk`, `systemctl list-units`, `docker ps`.
- **금지 목록이 특히 잘 설계됐다**: `sudo`, `env`·`printenv`, `169.254.169.254`(클라우드 메타데이터 서비스), 프로세스 커맨드라인 조회, 설정·자격증명 파일 읽기, `StrictHostKeyChecking=no`.
- 일괄 SSH는 대상 호스트 전체 목록을 확인받은 뒤에만 수행한다.
- `connect`가 `ssh -i <위치 참조> <host> 'true'`로 접속을 검증한다.

**⚠️ 단서**: `ops`의 references는 kubectl·helm·argocd·prometheus 4종뿐이라 ssh·systemd·docker의 read-only/mutating 분류표가 없다. `ops`는 "표에 없는 서브커맨드는 항상 mutating으로 취급"하므로, **서버에 대한 단순 조회조차 승인 게이트를 타게 된다**. 안전한 방향의 기본값이지만 마찰이 크다.

### Q6. 서버에서 관리 중인 시스템 접속이 용이한가 (메트릭·로그·DB) — ⚠️ (메트릭만 ✅)

셋의 성숙도가 크게 다르다.

| 대상 | 판정 | 근거 |
|---|---|---|
| 메트릭 | ✅ | `references/prometheus.md`에 즉시/범위 PromQL, `/api/v1/labels`, `/api/v1/targets`, vmui 예시. 토큰은 `${VM_TOKEN}` 환경변수 참조로만 쓰고 `export`는 사용자가 실행 |
| 로그 | ❌ | 담당 절차 없음. `kubectl logs`가 read-only 어휘 목록에 단어로만 존재하고 실행 예시 0건. victorialogs·ELK·Loki 관련 기술 전무 |
| DB | ❌ | `ops` 절차·reference 없음. `psql`은 `keys.md`의 `usage` 레시피 예시로만, `mysql`은 `lookup`의 **금지 예시**(`mysql -p1234`)로만 등장 |

로그가 비어 있는 것은 장애 대응 시나리오 전체의 병목이다(§2 참조).

### Q7. 쿠버네티스 서버도 관리 가능한가 — ✅ (노드 조인만 ❌)

**가능하다.** `k8s-cluster` 엔티티가 `context`·`access_recipe`·`managed_by`를 갖고, `component`가 `runs_on`으로 클러스터에 매달린다. `ops`가 kubectl·helm·argocd 조작을 read/mutating으로 분류해 실행하고, `sync`가 `kubectl get nodes`·`helm list -A`로 실제 상태를 대조한다. 인벤토리 범위를 **클러스터·컴포넌트 수준까지로 의도적으로 제한**하고 내부 리소스는 GitOps 레포에 넘기는 것도 원칙 4에 부합하는 선택이다.

멀티 클러스터도 성립한다 — 프로파일 P3(AWS EKS + GCP GKE 2개 클러스터)에서 각 클러스터에 대해 `--context stub-k8s`, `--context stub-gke`로 수집 명령이 분리 생성되는 것을 실측했다.

**❌ 예외 — 서버를 클러스터에 조인하는 시나리오는 없다.** 조인 명령(`kubeadm join` 등)도, 조인 토큰을 담을 `kind` 어휘도, **서버 엔티티에 "어느 클러스터의 노드인지"를 적을 필드도** 없다(`runs_on`은 component 전용이고 `k8s-cluster`에 members가 없다).

### Q8. 클라우드와 온프렘 모두 관리 가능한가 — ⚠️ (인벤토리 ✅, sync에 사각지대)

**인벤토리·정책·audit 층은 완전히 성립한다.** provider `kind`가 `aws|gcp|onprem`을 구분하고, 온프렘은 `cli_profile`을 비우면 된다. 프로파일 P1(온프렘 only), P3(AWS+GCP 동시), P4(온프렘 + 비-k8s 클러스터) 모두 audit 실패 0건으로 통과했다.

**⚠️ sync에 조용한 사각지대가 있다.** `sync_snapshot.py`가 `kind`가 aws/gcp가 아닌 provider를 **조용히 건너뛴다**. 온프렘 하네스에서 `--collect`를 돌리면 "문서 누락 0건 / 유령 0건 / 버전 불일치 0건 / **확인 불가 0건**"이 나온다. 즉 대조하지 않았는데 "문서와 실제가 일치한다"처럼 읽힌다. 스펙이 "자격 증명이 없거나 수집 명령이 실패한 대상은 '확인 불가'로 구분 보고한다(오탐 방지)"고 규정한 것과 어긋나는 방향이다.

추가로 aws 수집 명령에 `--region`이 없어 profile 기본 리전만 조회한다. `provider.regions` 필드는 정의만 되고 **어디서도 소비되지 않는다** — 원칙 6(암묵 컨텍스트 금지)의 정신과 어긋난다.

---

## 2. 환경 프로파일 × 시나리오 커버리지

### 대표 환경 프로파일

전수 조합(클라우드 구성 3 × k8s 2 × Vault 3 = 18셀)은 형식적 O/X 표가 되므로, **각 축 값이 최소 1회 등장**하도록 대표 프로파일 5개를 선정했다. 5개 전부 실제로 하네스를 만들어 `audit`·`sync --collect`를 돌린 실측 대상이다.

| ID | 클라우드 구성 | k8s | 시크릿 백엔드 | sharing/secrets_mode | 선정 근거 |
|---|---|---|---|---|---|
| P1 | 온프렘 only | 無 | 없음(로컬 평문) | local / plaintext | 최소 구성. 클라우드·k8s 전제가 하드코딩됐는지 검출 |
| P2 | 단일 클라우드(AWS) | 有 | 자체 관리(age/SOPS) | git / encrypted | 팀 공유 + 암호화의 표준 경로 |
| P3 | 멀티 클라우드(AWS+GCP) | 有 (2개) | **Vault** | git / none | 멀티 클라우드·멀티 클러스터·외부 백엔드 동시 |
| P4 | 온프렘 | 無 | 없음 | local / plaintext | 비-k8s 클러스터(카프카 3노드, DB active/standby) |
| P5 | 온프렘 | 無 | 로컬 평문 | **git / plaintext (금지 조합)** | 음성 대조 — 정책 위반을 잡는지 |

축 커버리지: 온프렘 only(P1·P4) / 단일 클라우드(P2) / 멀티 클라우드(P3) · k8s 有(P2·P3) / 無(P1·P4·P5) · Vault 有(P3) / 無(P1·P2·P4·P5). **Vault "환경별 혼재"는 어느 셀로도 표현할 수 없다** — 이유는 Q2 참조. 이는 프로파일 선정의 한계가 아니라 스키마의 한계다.

### 기반 계층 실측 결과

| | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| `audit` | 통과 | 통과 | 통과 | 통과 | **실패(의도대로)** |
| `sync --collect` | 정상(단 온프렘 미대조) | 정상 | 정상, 2클러스터 분리 수집 | 정상(온프렘 미대조) | 정상 |

P5는 `FAIL [정책] secrets_mode: plaintext는 sharing: local에서만 허용 (현재 sharing: git)`으로 정확히 잡혔다.

### 시나리오 커버리지

판정 기호: **O** 담당 절차 있음 / **△** 부분(핵심 조각 결여) / **X** 담당 없음 / **N/A** 해당 프로파일에 논리적으로 성립 안 함

#### 중점 3영역

| 시나리오 | P1 | P2 | P3 | P4 | P5 | 비고 |
|---|---|---|---|---|---|---|
| 백업·복구·DR | X | X | X | X | X | `runbooks/`가 빈 채로 생성될 뿐, 읽거나 채우는 스킬·템플릿이 하나도 없다. 백업 대상·주기·보존·RTO/RPO를 적을 자리 없음 |
| 장애 대응·진단 | △ | △ | △ | △ | △ | 개별 명령(재시작·롤백·메트릭)은 있으나 **진단 흐름이 없다**. 증상→로그→메트릭→최근 변경 역조회 순서 없음, `changes/`를 원인 후보로 조회하는 절차 없음, **로그 조회 경로 자체가 없음**, 인시던트 기록 형식 없음(change 템플릿은 계획된 변경 전제) |
| 네트워크·DNS·인증서 | △ | △ | △ | △ | △ | 인증서는 **만료 경고만**(audit이 30일 이내 WARN) 있고 갱신 절차·도구 없음. `keys.md`에 도메인/SAN/발급자 칸 없음. DNS·방화벽·보안그룹은 엔티티 타입조차 없음 |

#### 필수 9건

| 시나리오 | P1 | P2 | P3 | P4 | P5 | 비고 |
|---|---|---|---|---|---|---|
| ① 인프라 시스템 설치(victorialogs·argocd) | X | △ | △ | X | X | k8s+helm 경로만 `helm install`이 분류표에 있어 ops 파이프라인을 탄다. **서버 직접 설치(apt·docker·systemd)는 분류표가 없어** 전부 "표에 없음=mutating" 게이트. 제품별 레시피·전제조건·설치 후 검증 없음 |
| ② VM MCP 설치 + 타 프로젝트 제공 | X | X | X | X | X | §3.4에서 상술. 현행 미지원이며 스펙 §4.3과 **요구가 정면 충돌**. 다만 §6.3.3에서 대상 MCP가 1st-party·read-only·bearer token 단일 인증임이 확인돼 **구현 난이도는 낮다** |
| ③ DB 설치 | X | X | X | X | X | `component.category`에 `db` 어휘만 있음. 설치·초기화·서비스 등록 절차 전무 |
| ④ 서버 사양 기반 DB 튜닝 | X | X | X | X | X | 튜닝·innodb·buffer_pool 언급 0건. 사양이 기계 파싱 대상이 아님(Q4) |
| ⑤ 작업 내용 로깅 | O | O | O | O | O | **구현 중 가장 완결**. ops가 mutating 후 자동 호출, 롤백 방법이 비면 반드시 묻고 답 전까지 완료 처리 안 함, append-only, 파일명 충돌 처리. 단 hook 리마인드는 terraform/kubectl/helm/argocd 4종에만 |
| ⑥ DB 계정 추가 | △ | △ | △ | △ | △ | 메타데이터 등록(`keys.md` 행, argv 금지)은 O. **값 생성·최초 암호화가 공백** — init이 "secrets 스킬로 넘어가 초기 암호화 진행"이라 인계하는데, secrets는 "**기존** 암호문 편집"만 다루고 신규 생성 절차가 없다. CREATE USER/GRANT 절차도 없음 |
| ⑦ 서버 추가 | O | O | O | O | O | 가장 상세. 대화형+일괄, 스캔 우선, env 확인, 명명 규약(클라우드 Name 태그 일치) |
| ⑧ 서버 k8s 클러스터 조인 | N/A | X | X | N/A | N/A | 조인 명령·토큰 `kind`·노드 소속 필드 전부 없음(Q7) |
| ⑨ 서버 구성 다이어그램 | X | X | X | X | X | 산출 스킬·스크립트 없음. 관계 데이터(`provider`·`runs_on`·`depends_on`)는 있어 생성 자체는 가능한 상태 |

#### 다양성 변형

| 시나리오 | P1 | P2 | P3 | P4 | P5 | 비고 |
|---|---|---|---|---|---|---|
| 비-k8s 클러스터(카프카·DB active/standby) | N/A | N/A | N/A | **△** | N/A | 엔티티 타입이 4종으로 하드코딩돼 `type: kafka-cluster`는 `FAIL [스키마] 알 수 없는 type`. server 3개 + `depends_on` 상호 참조 + 본문 서술로 **적을 수는 있으나**(P4에서 audit 통과 실측) `role: active/standby`·클러스터 멤버십을 **읽는 스킬이 0건**. sync 대조 수단도 없음 |
| 로그 스택(victorialogs / ELK) | X | X | X | X | X | references 4종 중 로그 담당 없음. LogsQL·Lucene·KQL 질의 문법, 인덱스·보존정책 필드 전무 |
| 배포·릴리스(저가중치) | N/A | O | O | N/A | N/A | argocd `app sync`·helm `upgrade`가 정책 게이트→실행→검증→기록 파이프라인을 완주. 카나리·블루그린 등 릴리스 **전략**은 범위 밖 |

### 시크릿 축 (sharing × secrets_mode)

시크릿 점검은 클라우드 구성이 아니라 이 두 축에 종속되므로 별도 표로 본다.

| sharing \ secrets_mode | `none` (참조만) | `plaintext` | `encrypted` |
|---|---|---|---|
| `local` | O — 외부 백엔드(`op://`·`vault://`) 참조 | O — `secrets/` 평문 허용. deny 방어선은 §3 한계 참조 | O — age/SOPS |
| `git` | O — P3 실측 통과 | **X — 금지 조합.** P5에서 audit이 정확히 FAIL | O — P2 실측 통과. recovery 수신자 없으면 FAIL(D11) |
| `shared-drive` | O(동일 규칙) | **X — 금지 조합** | △ — 암호문은 안전하나 POSIX 권한 미보존 문제는 ssh 키에 한해 스펙이 원위치 유지로 회피 |

---

## 3. 시크릿 유출 경로 점검

### 3.1 격리 구성

모든 모의 구동은 리포 밖 스크래치의 격리 실험실에서 수행했다. **실 인프라 호출 0건**이다.

- **PATH shim 스텁 15종**으로 실 CLI를 대체: `aws` `gcloud` `kubectl` `helm` `argocd` `ssh` `vault` `terraform` `docker` `ssh-keygen` `psql` `mysql` `sops` `age` `op`. 각 스텁은 호출을 로그에 기록하고 합성 데이터만 반환한다.
- 환경 봉인: `HOME`을 가짜 홈으로, `AWS_CONFIG_FILE`·`AWS_SHARED_CREDENTIALS_FILE`·`KUBECONFIG`를 `/dev/null`로, `VAULT_ADDR`를 닫힌 포트로 지정.
- `command -v aws|kubectl|helm|gcloud|ssh|vault`가 전부 스텁 경로로 해석되는 것을 실행 전 확인했다.

**스텁이 실제로 받은 호출** (모의 구동 전체):

```
[kubectl] --context stub-k8s get nodes -o name
[helm]    --kube-context stub-k8s list -A -o json
[aws]     ec2 describe-instances --profile stub-profile-a --query ... --output text
[gcloud]  compute instances list --configuration stub-gcp-config --format value(name)
[kubectl] --context stub-gke get nodes -o name
[helm]    --kube-context stub-gke list -A -o json
```

생성된 명령 6종이 **전부** `--context`/`--kube-context`/`--profile`/`--configuration`을 명시했다. 암묵 컨텍스트에 의존한 명령은 0건으로, 원칙 6이 문서 수사가 아니라 코드에서 지켜지고 있음이 실측으로 확인된다.

증거로 인용한 식별자는 전부 합성값(`stub-profile-a`, `stub-k8s`, `example.invalid`)이며 실 머신 메타데이터는 포함하지 않았다.

### 3.2 카나리 프로토콜

- **카나리 형식**: `BLINDCANARY-<24자>`, `BLINDTWO-<24자>` (합성값 — 실제 자격증명이 아니다).
- **심은 위치**: 모의 하네스 `secrets/blind-token.txt`, `secrets/db-admin.txt`, `secrets/vm-token.txt`, 그리고 오염 하네스의 `access/keys.md`(`ghp_` 패턴).
- **검사 대상**: 세션 트랜스크립트(`~/.claude/projects/**/*.jsonl`), 하네스 산출 문서 전체(`secrets/` 제외), 증거 파일.
- **판정 술어**: 위 검사 대상 어디에든 카나리 문자열이 나타나면 유출로 판정한다.

**양성 대조를 설계에 넣었다.** 1차 카나리는 의도적으로 Read·Bash 채널로 노출시켜 **검사기가 실제 유출을 잡아낼 수 있는지** 먼저 입증했다(→ 트랜스크립트에서 검출됨). 2차 카나리는 에이전트가 값을 보지 않은 채 플러그인 경로로만 관찰했다(→ 어디에서도 미검출). 양성 대조가 없으면 "미검출"은 검사기가 고장 난 것과 구별되지 않는다.

### 3.3 채널 열거표

| # | 채널 | cwd **하위** `secrets/` | cwd **밖** `secrets/` (절대경로) |
|---|---|---|---|
| C1 | Read 도구 | 차단 | **통과 — 유출** |
| C2 | Bash `cat` | 차단 | **통과 — 유출** |
| C3 | Bash `python3 -c "open(...).read()"` | **통과 — 우회** | 통과 |
| C4 | `audit.py` 리포트 | 무유출 (패턴명·파일명만) | 무유출 |
| C5 | `audit.py` encrypted 위반 경로 | 무유출 (파일명만) | 무유출 |
| C6 | `audit.py --staged` | 무유출 | 무유출 |
| C7 | `sync_snapshot.py` 리포트 | 무유출 | 무유출 |
| C8 | hook `additionalContext` | 무유출 | 무유출 |
| C9 | `git diff --cached` | 무유출 (`.gitignore`로 스테이징 제외) | 무유출 |
| C10 | 스텁 CLI 호출 로그 | 무유출 | 무유출 |

**핵심 결론 두 가지.**

첫째, **플러그인 자신이 만들어내는 경로(C4~C10)로는 시크릿이 새지 않는다.** `audit.py`는 오염 하네스에서 `AKIA` 패턴과 AWS Secret Key 할당문을 정확히 검출하면서도 **매치된 값을 출력하지 않고** 파일명·패턴명만 보고한다. encrypted 정책 위반 경로에서도 파일 내용 대신 "age/SOPS 암호문 형식이 아님"만 출력한다. 스펙 §8.1 #4의 요구가 코드에서 지켜진다.

둘째, **위험은 전적으로 플랫폼 deny 규칙의 경계에 있다.** 실측된 두 경계, 그리고 문서로 확인된 세 번째 경계:

- **cwd 밖은 보호되지 않는다.** deny 규칙은 cwd 기준이므로, 하네스 밖에서 세션을 열고 절대 경로로 하네스 `secrets/`를 가리키면 Read도 Bash도 통과한다.
- **명령어 형태를 바꾸면 우회된다.** cwd 하위에서 `cat`은 차단되는데 `python3 -c "open(경로).read()"`는 통과했다. 이는 문서가 Warning으로 명시한 동작이다 — "Read and Edit deny rules apply to Claude's built-in file tools and to file commands Claude Code recognizes in Bash, such as `cat`, `head`, `tail`, and `sed`. **They don't apply to arbitrary subprocesses that read or write files indirectly, like a Python or Node script that opens files itself.** For OS-level enforcement that blocks all processes from accessing a path, enable the sandbox." 실측이 이 서술과 정확히 일치한다.

  여기에 뼈아픈 함의가 있다. **플러그인 자신의 `scripts/*.py`가 바로 이 "arbitrary subprocess"에 해당한다.** `audit.py`가 `secrets/`를 재귀 스캔할 수 있는 것도 deny가 파이썬 프로세스에 적용되지 않기 때문이다. 즉 플러그인은 자기 방어선이 자기에게 적용되지 않는 위치에서 동작하며, 실제 안전은 §3.3의 실측이 보인 대로 **"스크립트가 값을 출력하지 않도록 작성됐다"**는 규율에서 나온다. 문서가 지목하는 유일한 진짜 경계는 **샌드박스**다.

- **하네스 하위 디렉터리에서 세션을 열면 방어선이 통째로 사라진다** (문서 확인, 이번 검토에서 가장 실용적인 결함). 공식 문서: "Hooks and other `.claude/settings.json` keys load from **the current working directory's `.claude/` folder with no parent-directory fallback**". 반면 이 플러그인의 하네스 발견은 D1에 따라 **cwd에서 루트 방향 상향 탐색**이다.

  두 규칙이 어긋나는 지점이 그대로 구멍이 된다. 사용자가 `<하네스>/inventory/`에서 `claude`를 실행하면 — 인벤토리 파일을 편집하려는 지극히 자연스러운 행동이다 — 스킬은 상향 탐색으로 하네스를 정상적으로 찾아 동작하지만, `<하네스>/.claude/settings.json`의 deny 규칙은 **로드되지 않는다.** 보호받고 있다고 믿는 상태에서 보호가 없다. (`settings.local.json`은 git 저장소 루트에서 로드되지만, 플러그인이 쓰는 것은 `settings.json`이라 이 폴백을 받지 못한다.)

deny 글롭이 **cwd 하위 임의 깊이의 `secrets/`를 매치**한다는 것도 확인됐는데, 이는 버그나 과잉이 아니라 **문서화된 의도적 동작**이다 — 공식 문서는 "Deny and ask rules: `Read(secrets/**)`는 현재 디렉터리 아래 **임의 깊이**의 `secrets` 디렉터리를 매치하므로 중첩된 사본에도 적용된다"고 명시한다(allow 규칙은 반대로 cwd 직속만 매치한다). 이 검토 세션이 플러그인 자신의 `skills/secrets/` **문서**를 읽지 못해 git 경유로 열람해야 했던 것(§3.6)은 그 규칙이 의도대로 작동한 결과이며, 플러그인의 디렉터리 이름이 흔한 deny 패턴과 충돌한 문제다(§4 P2-5).

**부수 확인 — D3의 이중 표기는 옳다.** 공식 문서의 앵커 규칙에 따르면 `/path`는 **설정 파일의 출처**를 기준으로 하고(프로젝트 설정이면 프로젝트 루트), `./path`는 cwd 기준이다. 하네스의 `.claude/settings.json`에 두 형태를 병기한 D3는 "하네스 루트 기준"과 "하위 디렉터리에서 세션을 연 경우"를 모두 덮으므로 정확한 선택이다. 다만 같은 규칙을 **사용자 설정**에 넣으면 `~/.claude/secrets/**`로 해석돼 전혀 다른 곳을 가리킨다는 점은 문서가 경고하는 함정이다.

**스펙 D13이 이 한계를 서술한 방향은 옳으나, 정밀도는 실측과 다르다.** D13은 "deny는 **Read 도구만** 막는 가드레일이며 보안 경계가 아님(**Bash/Python은 여전히 읽음**)"이라고 적었다. 실측 결과는 절반만 일치한다 — cwd 하위에서 Bash `cat`은 **차단됐고**, `python3 -c`는 통과했다. 즉 게이트는 Read 전용이 아니라 Bash에도 적용되지만, **명령어 형태에 대한 휴리스틱**이라 형태를 바꾸면 뚫린다. 결론(보안 경계가 아니다)은 유효하고, 오히려 실제 위험의 성격은 D13이 예상한 것과 다르다: "Bash면 무조건 뚫림"이 아니라 "특정 명령 형태만 막힌다"이므로, 사용자가 `cat`이 막히는 것을 보고 방어선이 일반적으로 작동한다고 오해하기 쉽다.

문제는 README FAQ가 같은 것을 "실수로도 값을 컨텍스트에 들일 수 없다"고 더 강하게 주장한다는 점이다. 더 나아가 **D13이 지시한 "문서에 명시한다"가 이행되지 않았다** — README·스킬 문서 어디에도 이 한계 서술이 없고, 유일한 언급은 스펙의 D13 행 자체뿐이다(§4 P0-2).

### 3.4 신규 요구 갭 평가 — 시크릿 export 플로우

**이 항목은 현행 감사가 아니라 갭 평가다.** "secret 값을 담은 `.mcp.json`·설치 스크립트를 생성해 타 프로젝트에 전달한다(설치는 개발자 수동)"는 요구에 해당하는 구현이 **없음을 실측으로 확인**했다:

- `.mcp.json` 파일 없음, `plugin.json`에 `mcpServers` 필드 없음.
- MCP 구성을 **생성**하는 스킬·스크립트 없음.
- `skills/register/SKILL.md` §8의 5줄 안내가 전부이며, 그 내용은 "`.mcp.json`은 **하네스 안에 보관**하고 값은 `${VM_TOKEN}` 같은 환경변수 참조로만 쓰고 **값 자체를 구성 파일에 적지 않는다**"이다.

즉 현행 규정은 요구와 **정면으로 충돌**한다. 모든 스킬이 `HARNESS_ROOT` 안에서만 동작하므로 타 프로젝트로 내보내는 경로도 설계상 존재하지 않는다.

**합격 술어** (컨텍스트 무유입만으로는 부족하다):

1. **컨텍스트 무유입** — 값이 Claude 컨텍스트를 거치지 않고 파일→파일로 주입되는가. 생성 스크립트가 백엔드에서 직접 읽어 치환하면 달성 가능하다.
2. **at-rest 취급** — 산출 파일이 놓이는 위치가 정해져 있는가, 대상 프로젝트의 `.gitignore`에 등록되는가, 만료·회수 절차가 있는가, 최소 권한 자격증명인가.
3. **전달 채널** — 파일 자체를 어떻게 건네는가(회수 가능한 채널인가).

**현재 판정: 세 술어 모두 미충족(구현 부재).** 1은 설계만 하면 달성 가능하지만, 2·3은 이 요구가 본질적으로 "평문 시크릿을 다른 저장소에 확산시키는" 행위이므로 별도 규약이 필요하다.

**외부 표준이 이 요구를 정면으로 다룬다** (§6.2). OWASP Secrets Management Cheat Sheet 3.6절은 암호화된 비밀을 저장소에 두는 것을 허용하되 **두 조건을 건다**: ①개발자 본인이 그 비밀을 복호화할 수 없어야 하고 ②각 소비자가 **자기 전용 암호화 변형본**을 가져야 한다. 값을 담은 파일을 그대로 건네는 방식은 두 조건을 모두 위반한다. NIST SP 800-57 Part 1 Rev.5는 cryptoperiod 결정 요인에 "키 사본의 수와 그 사본들의 배포"를 명시해, **배포 자체가 유효기간을 단축시켜야 하는 요인**임을 규정한다.

**그리고 플랫폼이 이 문제에 이미 답을 갖고 있다.** `plugin.json`의 `userConfig`에 `sensitive: true`로 선언된 필드는 입력이 마스킹되고 `settings.json`이 아니라 **secure storage**에 저장된다(§6.1). MCP 서버의 bearer 토큰처럼 "받는 쪽이 채워야 하는 값"은 파일로 배포할 게 아니라 이 경로로 받는 것이 플랫폼의 정식 설계다.

**따라서 권고는 "값을 담지 않는 산출물"이다.** 하네스가 생성하는 것은 `${VM_INSTANCE_BEARER_TOKEN}` 참조형 `.mcp.json`(또는 `userConfig` 선언을 포함한 플러그인 스캐폴드)이고, 값은 수신 개발자가 자기 secure storage·패스워드 매니저에 직접 넣는다. 이 형태는 원칙 1·2를 지키면서 요구의 실질(개발자가 바로 설치할 수 있게 해준다)을 대부분 충족한다. 값을 담은 산출이 정말 필요하다면 **수신자별 암호화 변형본 + 짧은 만료 + 회수 절차**를 갖춘 예외 경로로 두어야 하며, 그때도 OWASP 2.7.1의 "사용자명과 비밀번호를 같은 채널로 보내지 않는다"가 적용된다.

### 3.5 신규 요구 갭 평가 — 시크릿 생성·저장 방향

"DB 계정 추가"처럼 **새 자격증명을 만들어 최초 저장**하는 방향은 현행 설계의 공백이다.

- `register`는 `keys.md`에 메타데이터 행을 추가한다(값 아님, argv 금지). 여기까지는 O.
- `init`은 "실제 시크릿 파일은 사용자가 직접 둔다"고 하고, encrypted 모드면 "`secrets` 스킬로 넘어가 `.sops.yaml` 생성과 **초기 암호화**를 진행하라"고 인계한다.
- 그런데 **인계 대상인 `secrets` 스킬에 신규 암호문 최초 생성 절차가 없다.** 이 스킬은 수신자 추가·재키잉·"**기존** 암호문의 내용을 바꿀 때"의 편집만 다룬다.

결과적으로 "계정 생성 → `keys.md` 행 → `secrets/` 파일 → 접속 검증"의 end-to-end 체인이 끊긴다. 사용자가 그 틈을 임시로 메우는 가장 쉬운 방법이 평문 파일을 잠깐 두는 것이라는 점에서, 이 공백은 단순한 미구현이 아니라 **원칙 위반을 유도하는 구조적 유인**이다.

### 3.6 git 경유로 열람한 파일

deny 규칙이 `skills/secrets/**`까지 차단해, 아래 파일은 사용자 승인 범위(시크릿 값이 아닌 스킬 문서)에서 `git show ec22855:<path>`로 열람했다.

- `skills/secrets/SKILL.md`
- `skills/secrets/references/backends.md`

### 3.7 동봉안 판정

**시크릿 영역에 P0 1건·P1 2건이 존재하므로 트리거가 발동한다** — P0-1(audit 크래시로 시크릿 스캔 미수행), P0-2(README 과대 주장), P1-6(신규 시크릿 최초 암호화 공백), P1-7(export 플로우 미지원). 따라서 아래 설계안을 포함한다.

**설계안: 값 취급 전담 실행 경계**

목표는 "값이 존재해야 하는 순간에도 Claude 컨텍스트를 통과하지 않게 한다"이며, 필요한 것은 MCP라는 형식이 아니라 **값을 반환하지 않는 실행 경계**다.

| 기능 | 입력 | 출력(컨텍스트로 가는 것) |
|---|---|---|
| `secret_exec` | 위치 참조 + 명령 템플릿 | 명령의 stdout에서 값을 마스킹한 결과, 종료 코드 |
| `secret_new` | 종류·길이·대상 엔티티 | 생성·암호화 저장된 **경로와 fingerprint만** (§3.5 공백 해소) |
| `secret_export` | 참조 목록 + 대상 경로 + 형식 | 기록된 **파일 경로와 만료 메타만** (§3.4 요구 해소) |
| `secret_rotate` | 위치 참조 | 로테이션 결과 요약 |

**1단계는 MCP가 아니라 python3 stdlib 스크립트를 권고한다.** 근거:

- **D2 제약을 그대로 지킨다.** 외부 의존 없이 표준 라이브러리만으로 구현 가능하다.
- **안전성 이득이 동등하다.** MCP 도구의 반환값도 컨텍스트로 들어간다. 안전은 "값을 반환하지 않는다"는 계약에서 오지 형식에서 오지 않는다.
- **기존 구조와 정합적이다.** 이미 `scripts/`에 stdlib 전용 스크립트 3종이 있고 `${CLAUDE_PLUGIN_ROOT}` 경로로 호출된다.

**2단계에서 MCP로 올릴 조건**은 다음 중 하나가 실제로 필요해질 때다:

- **도구 단위 권한 게이팅** — `Bash(*)`보다 `mcp__infra_secrets__exec`가 훨씬 좁은 허용 범위를 만든다. §3.3에서 본 "명령어 이름만 바꾸면 우회" 문제는 Bash를 넓게 허용하는 한 남는데, MCP 도구는 그 우회면이 없다. **이것이 MCP를 택할 가장 강한 근거다.**
- **장기 세션 상태** — 복호 세션·Vault 토큰 캐시를 프로세스에 유지해야 할 때.
- **비-Bash 런타임** — Bash를 못 쓰는 호스트에서 동일 기능이 필요할 때.

**플랫폼 전제는 충족된다** (§6.1 확인). 플러그인은 MCP 서버를 동봉할 수 있고, 위치는 플러그인 루트의 `.mcp.json` 또는 `plugin.json` 인라인이며 `command`·`args`·`env`에서 `${CLAUDE_PLUGIN_ROOT}`를 쓸 수 있다. 따라서 1단계 스크립트를 그대로 MCP 서버의 실행 본체로 재사용할 수 있고, 두 단계가 버리는 작업 없이 연속된다.

한 가지 덧붙일 것은, MCP로 올려도 **§3.3의 우회면이 완전히 사라지지는 않는다**는 점이다. Bash가 넓게 허용된 세션에서는 사용자가·모델이 여전히 임의 명령으로 파일을 읽을 수 있다. MCP 도구가 좁히는 것은 "이 플러그인이 제공하는 정상 경로"이지 시스템 전체가 아니다. 진짜 경계가 필요하면 Bash 자체를 좁히거나 샌드박스를 써야 하며, 이 구분을 문서에 적어두는 것이 P0-2 정정의 일부가 되어야 한다.

**구현 시 반드시 지킬 교훈이 하나 있다** (§6.3). `mcp-server-kubernetes`의 **CVE-2026-46519**는 read-only 모드를 `tools/list` 디스커버리 핸들러에서만 필터링하고 `tools/call` 실행 핸들러에는 적용하지 않아, 도구 이름을 아는 클라이언트가 `kubectl_delete`를 직접 호출해 파드를 지울 수 있었다. **접근 제어를 도구 목록 노출로 구현하면 무력화된다 — 실행 지점에서 강제해야 한다.** 위 표의 `secret_exec`·`secret_export`를 만들 때 "위험한 참조는 목록에서 감춘다" 같은 설계를 택하지 않아야 한다.

**덧붙여, D3가 템플릿 복사 방식인 것은 차선이 아니라 유일해다.** 플러그인의 `settings.json`은 `agent`와 `subagentStatusLine` 키만 지원하므로 **플러그인이 자기 `permissions.deny`를 배포할 수 없다**(§6.1). `init`이 하네스에 템플릿을 복사하는 현행 방식이 플랫폼상 가능한 유일한 경로이며, 설계 선택 자체는 정당하다. 다만 그 대가로 (a)사용자가 그 파일을 편집·삭제하면 보호가 사라지고 (b)플러그인 업데이트가 그 파일을 갱신하지 못한다. **이 드리프트 감지는 `audit`의 책임 범위여야 한다** — 현재는 점검 항목에 없다.

---

## 4. 우선순위 갭 목록과 다음 단계 D 결정 후보

### 등급 정의

| 등급 | 정의 |
|---|---|
| **P0** | 시크릿 유출 또는 오조작이 가능하다 |
| **P1** | 중점 시나리오를 수행할 수 없다 |
| **P2** | 마찰·문서 드리프트 |

### P0

**P0-1. `audit.py`가 특정 입력에서 크래시해 시크릿 스캔이 아예 수행되지 않는다**
`component`의 `runs_on`이 리스트일 때 `TypeError: cannot use 'list' as a set element`로 스택 트레이스를 내고 종료한다. 검사 리포트가 한 줄도 나오지 않으므로 **시크릿 스캔·정책 검사가 통째로 건너뛰어진다.** frontmatter 파서가 `[a, b]`를 리스트로 만들기 때문에, 다중 노드 컴포넌트를 표현하려는 자연스러운 시도만으로 재현된다.
→ **D 결정 후보**: 알 수 없는 필드 형태를 만나면 크래시 대신 `FAIL [스키마]`로 보고하도록 방어한다. 나아가 audit 전체를 검사별 예외 격리로 감싸 **한 검사의 실패가 다른 검사를 막지 않게** 한다.

**P0-2. 방어선의 한계가 사용자 대면 문서에 없고, README FAQ는 반대로 과대 주장한다**
README FAQ는 "하네스의 `secrets/`는 Read 도구가 `.claude/settings.json` deny로 차단되어, **실수로도 값을 컨텍스트에 들일 수 없다**"고 서술한다. §3.3 실측은 `python3 -c`로 우회되고 cwd 밖 절대 경로는 아예 보호되지 않음을 보였다.

이것은 단순한 문서 간 불일치가 아니다. **스펙 D13은 "deny는 가드레일이며 보안 경계가 아님을 문서에 명시한다"고 스스로 지시했는데, 그 지시가 이행되지 않았다** — README·스킬 문서 어디에도 한계 서술이 없고 유일한 언급은 스펙의 D13 행 자체다. 사용자가 접하는 유일한 서술이 과대 주장인 셈이다.

위험 경로는 구체적이다. 사용자가 이 주장을 믿고 `sharing: local` + `secrets_mode: plaintext`를 선택한 뒤, 하네스 밖 프로젝트에서 세션을 열어 하네스를 절대 경로로 참조하면 방어선이 전혀 작동하지 않는다. `cat`이 막히는 것을 본 사용자가 방어선이 일반적으로 작동한다고 오해하기 쉽다는 점이 위험을 키운다.
→ **D 결정 후보**: ①README FAQ 문구를 D13 서술에 맞춰 정정한다. ②deny의 세 가지 실측 경계(cwd 밖 미적용, 명령어 형태 우회, cwd 하위 임의 깊이 과잉 매칭)를 README에 명시해 D13 지시를 이행한다. ③1차 방어선은 어디까지나 "스킬이 스스로 읽지 않는 것"이고 deny는 2차 가드레일임을 재확인한다.

**P0-3. 하네스 하위 디렉터리에서 세션을 열면 `secrets/` 차단이 로드되지 않는다**
D1은 하네스를 **cwd 상향 탐색**으로 찾는데, 플랫폼은 `.claude/settings.json`을 **cwd의 `.claude/`에서만, 부모 폴백 없이** 로드한다(§3.3, 공식 문서 확인). 따라서 `<하네스>/inventory/`에서 `claude`를 실행하면 스킬은 정상 동작하지만 deny 규칙은 없다. 하네스 서브디렉터리에서 작업하는 것은 예외가 아니라 흔한 사용 방식이므로 노출 창이 넓다.
→ **D 결정 후보**: ①`init`이 deny 규칙을 `.claude/settings.json`이 아니라 **`.claude/settings.local.json`에 함께 쓴다** — 후자는 git 저장소 루트에서 로드되므로 하위 디렉터리 세션도 덮는다(하네스가 git 저장소일 때). ②git을 쓰지 않는 하네스를 위해, `init`이 하네스 CLAUDE.md와 README에 "세션은 하네스 루트에서 열 것"을 경고로 명시한다. ③`audit`이 이 비대칭을 점검 항목으로 추가한다.

**P0-4. 방어선의 실효 범위가 플러그인 자신의 스크립트에는 적용되지 않는다**
문서가 명시하듯 deny는 "arbitrary subprocesses … like a Python or Node script"에 적용되지 않는다. 플러그인의 `scripts/*.py`가 정확히 여기 해당하므로, `audit.py`·`sync_snapshot.py`는 deny와 무관하게 `secrets/`를 읽는다. 이것이 잘못된 설계라는 뜻은 아니다 — `audit.py`는 `secrets/`를 재귀 스캔해야 하는 정당한 이유가 있다. 문제는 **이 사실이 위협 모델 문서에 없다**는 점이다. 향후 기여자가 스크립트에 진단 출력 한 줄을 추가하는 것만으로 방어선이 무력화되는데, 그것을 막는 것은 현재 코드 리뷰 관행뿐이다.
→ **D 결정 후보**: ①`CLAUDE.md`의 "수정 시 반드시 지킬 것"에 "스크립트는 deny 밖에서 동작하므로 `secrets/` 내용을 변수에 담더라도 출력·예외 메시지·리포트에 싣지 않는다"를 명문화한다. ②테스트로 강제한다 — fixture의 `secrets/`에 카나리를 심고 `audit.py`·`sync_snapshot.py`의 전체 출력에 그 값이 없음을 assert하는 회귀 테스트를 추가한다(이번 검토의 §3.2 프로토콜을 테스트로 고정하는 것이다). ③진짜 OS 수준 경계가 필요한 사용자를 위해 샌드박스 활성화를 README에 안내한다.

### P1

**P1-1. 백업·복구·DR 전무** — `runbooks/`가 빈 채로 생성될 뿐 이를 읽거나 채우는 스킬·템플릿이 없다. 인프라 관리에서 가장 비싼 실패(데이터 유실)에 대응할 자리가 하네스에 없다.
→ **D 결정 후보**: `runbook` 템플릿과 `runbooks/` 작성·조회 절차를 도입한다. 서버·DB 엔티티에 백업 대상·주기·보존·최근 검증일을 담는 선택 필드를 두고, audit이 "백업 기록이 오래됨"을 경고한다.

**P1-2. 로그 조회 경로 없음** — 장애 대응 시나리오의 병목. `references/`에 로그 담당이 없어 victorialogs·ELK·Loki 어느 것도 다루지 못한다.
→ **D 결정 후보**: `references/logs.md`를 추가하되 스택별 질의 문법(LogsQL·Lucene·KQL)을 분기로 담고, `component`에 로그 스택 종류·인덱스·보존정책 필드를 둔다. **대안이 더 저렴할 수 있다** — VictoriaLogs는 1st-party MCP 서버(`VictoriaMetrics/mcp-victorialogs`, read-only 전용)를 제공하므로(§6.3.3), 그 스택을 쓰는 사용자에게는 질의 문법을 문서화하는 대신 MCP 연결을 안내하는 편이 유지보수 부담이 적다. ELK 등 MCP가 없는 스택만 reference로 다루는 혼합 전략을 검토할 만하다.

**P1-3. DNS·방화벽·인증서 갱신 없음** — 인증서는 만료 경고만 있고 갱신 절차가 없다. DNS 레코드·보안그룹은 엔티티 타입조차 없다.
→ **D 결정 후보**: 인증서 갱신을 먼저 다룬다(만료 경고가 이미 있어 연결이 자연스럽다). `keys.md`의 `tls-cert` 행에 도메인·SAN·발급자·갱신 방법 칸을 추가한다. DNS·방화벽은 별도 엔티티 타입 도입 여부를 P1-5와 함께 판단한다.

**P1-4. sync가 온프렘을 조용히 건너뛴다** — 대조하지 않았는데 "0건"으로 보고돼 "일치"로 오해된다. 스펙의 "확인 불가로 구분 보고(오탐 방지)" 규정과 어긋나는 방향이다.
→ **D 결정 후보**: 수집기가 없는 provider는 **"확인 불가"로 명시 보고**한다. 함께 `provider.regions`를 소비해 aws 수집 명령에 `--region`을 붙인다(원칙 6).

**P1-5. 비-k8s 클러스터를 표현할 수 없다** — 엔티티 타입 4종이 하드코딩돼 `type: kafka-cluster`는 즉시 실패한다. 카프카·DB active/standby는 `depends_on`과 본문 서술로 적을 수는 있으나 그 정보를 읽는 스킬이 0건이다.
→ **D 결정 후보** (택일 판단 필요):
  - (a) 일반 `cluster` 타입을 도입하고 `kind`(kafka·postgres-ha·…)와 `members`·`role`을 필드로 둔다. 표현력은 크지만 sync 대조 수단이 없으면 문서가 실제와 갈라진다.
  - (b) `server`에 `cluster`·`role` 선택 필드만 추가해 멤버십을 표현하고, 클러스터 자체는 엔티티로 만들지 않는다. 최소 변경이며 원칙 4에 더 부합한다.
  - 현재로선 **(b)를 권고**한다 — 하네스는 지도이지 클러스터 상태 저장소가 아니고, (a)는 sync 수집기를 스택마다 만들어야 성립한다. **외부 조사가 이 판단을 강화한다**(§6.3.1): NetBox의 `Cluster`는 가상화 전용이고 Backstage에는 역할 개념이 없으며, 그룹 멤버십을 1급으로 다루는 것은 Ansible inventory뿐이다. 즉 참고할 무거운 선례가 없고, 검증된 최소 패턴은 그룹 멤버십 필드다.
  - **다만 이 공백은 이 플러그인만의 결함이 아니다.** 인벤토리 도구 어느 것도 카프카·DB active-standby를 1급으로 모델링하지 않는다. 우선순위를 정할 때 "업계 표준을 따라가지 못한 지연"이 아니라 "아직 아무도 채우지 않은 자리"로 평가하는 것이 정확하다.

**P1-6. 신규 시크릿 최초 암호화 절차 공백** — §3.5. 사용자가 이 틈을 평문으로 메우도록 유도한다.
→ **D 결정 후보**: `secrets` 스킬에 "신규 시크릿 생성·최초 암호화" 절을 추가하고, `init`의 인계 문구가 실제 존재하는 절을 가리키게 한다. §3.7의 `secret_new`가 이를 스크립트로 구현하는 형태다.

**P1-7. MCP export 플로우 미지원 + 스펙과 요구 충돌** — §3.4.
→ **D 결정 후보**: 먼저 스펙 §4.3의 "값을 적지 않는다" 규정을 유지할지 예외를 열지 결정한다. 여는 쪽이면 만료·회수·`.gitignore` 등록을 동반한 `secret_export` 규약을 신설하고, 유지하는 쪽이면 `${VAR}` 참조형 산출 + 값은 별도 채널이라는 대안 절차를 명문화한다.

**P1-8. ops references가 k8s에 편중돼 서버 조회도 승인 게이트를 탄다** — 4종 중 3종이 k8s 도구다. ssh·systemd·docker·DB·클라우드 CLI 분류표가 없어 "표에 없음=mutating" 규칙에 따라 단순 조회까지 confirm을 요구한다.
→ **D 결정 후보**: `references/server.md`(ssh·systemd·docker)와 `references/db.md`를 추가해 read-only 어휘를 분류표에 등재한다. 테스트가 references 4종의 존재만 강제하고 있어 확장 유인이 없다는 점도 함께 고친다.

**P1-9. DB 설치·튜닝, k8s 노드 조인, 구성 다이어그램 없음** — 관계 데이터(`provider`·`runs_on`·`depends_on`)가 이미 있어 다이어그램은 가장 적은 노력으로 추가할 수 있다.
→ **D 결정 후보**: 다이어그램을 먼저 도입한다(mermaid 산출 스크립트 + `diagram` 스킬). DB 설치·튜닝은 Q4의 사양 필드 승격과 묶어 판단한다. 노드 조인은 P1-5의 멤버십 필드가 정해진 뒤에 다룬다.

### P2

| ID | 내용 | D 결정 후보 |
|---|---|---|
| P2-1 | `CLAUDE.md`가 스테일 — "스킬 9종"(실제 10종), "결정 D1~D9"(스펙은 D14), "테스트 55개"(실제 77개), plan 문서 1개만 열거(실제 3개) | 갱신. 나아가 테스트가 이 수치들의 정합성을 검사하게 한다 |
| P2-2 | `provider.regions`가 정의만 되고 소비되지 않으며 aws 수집에 `--region` 없음 | P1-4와 함께 처리 |
| P2-3 | `secrets_format`이 스키마에만 있고 아무도 읽지 않는 死키 — `secrets_format: pgp` 같은 오설정이 통과 | audit에 값 검증을 추가하거나 스키마에서 제거 |
| P2-4 | 워크트리 스펙의 상세 절(§1·§5·§7·§8.1·§10·§12)이 자기 D표를 따라가지 못함. §7에 `secrets` 스킬 명세 자체가 없어 스펙만으론 절차를 알 수 없음 | 상세 절을 D14까지 반영해 갱신 |
| P2-5 | 스킬 디렉터리명 `secrets`가 흔한 deny 패턴과 충돌해 플러그인 자신의 **문서**가 차단된다. deny 규칙이 임의 깊이를 매치하는 것은 문서화된 동작이므로 플랫폼 버그가 아니라 **이름 선택의 문제**다. 오픈소스로 배포하면 `Read(secrets/**)` 계열 규칙을 쓰는 사용자·기여자 모두가 겪는다 | 스킬 디렉터리를 `secret-lifecycle` 등으로 개명한다(스킬 이름은 frontmatter `name`과 디렉터리명이 일치해야 하므로 함께 변경). 개명하지 않는다면 README에 알려진 제약과 `git show` 우회를 기록한다 |
| P2-6 | hook mutating 패턴이 terraform·kubectl·helm·argocd 4종 한정 — ssh·apt·docker·psql·클라우드 CLI 변경은 리마인드 없음 | P1-8의 references 확장과 함께 패턴 추가 |
| P2-7 | 들여쓴 frontmatter가 "중첩 구조 미지원"으로 오진 — 실제 원인은 선행 공백 | 오류 메시지에 선행 공백 사례를 분기해 안내 |
| P2-8 | `harness-off` fixture가 스펙에 미기재(스펙은 fixture 2개) | 스펙 §12 갱신 |

---

## 5. 3자 괴리 목록 (main 스펙 / 워크트리 스펙 / 구현)

기준 커밋 **`ec22855`**. 세 축은 ①main 스펙(D1~D9) ②워크트리 스펙(D1~D14) ③구현이다.

### 5.1 main 스펙 vs 워크트리 스펙 — 전부 문서화된 진화

`main..HEAD` 미병합 커밋은 **46개**다. main 스펙에 D10~D14가 없는 이유는 단순히 미병합 브랜치이기 때문이며, 비의도 드리프트가 아니다.

| 결정 | 내용 | 구분 |
|---|---|---|
| D10 | 서버 정보 분리 — 스킬이 결정론적으로 소비하는 값만 frontmatter, IP·사양·특이사항은 본문 자유 서술 | 문서화된 진화 |
| D11 | 팀 시크릿 라이프사이클 — `secrets_recipients` + 복구 수신자 필수, 온보딩·오프보딩 재키잉, **신규 `secrets` 스킬** | 문서화된 진화 |
| D12 | 자격증명 스키마 개정 — `keys.md` 9컬럼, `kind` 어휘 6종, 비밀번호 argv 금지 | 문서화된 진화 |
| D13 | audit 하드닝 — 심링크 거부, `secrets/` 재귀 스캔, encrypted 헤더 엄격 검사, 중복 id·충돌 사본 탐지, `--staged` 모드 | 문서화된 진화 |
| D14 | 외부 백엔드 참조 규약 — `op://`·`vault://`·`aws-secretsmanager://`, 참조는 불투명(resolve 안 함) | 문서화된 진화 |

### 5.2 워크트리 스펙 vs 구현 — 실질 드리프트

**공통 원인 하나가 표의 절반을 설명한다**: 워크트리 스펙은 **D 결정표(§2)만 진화했고 상세 절은 D9 시점 그대로**다. §1·§5·§7·§8.1·§10·§12가 main과 바이트 단위로 동일하다. 따라서 "스펙이 말하는 것"이 자기 D표와 모순되는 행이 생긴다.

| # | 항목 | 스펙이 말하는 것 | 구현 실제 | 구분 |
|---|---|---|---|---|
| 1 | 스킬 수 | §1·§7 "9종", §7에 secrets 명세 절 없음 | 10종 | 문서화된 진화(D11) + 스펙 상세 절 스테일 |
| 2 | 엔티티 필수 필드 | §4.1 | `REQUIRED_FIELDS`·템플릿 4종과 정확히 일치 | **일치** (3자 정합) |
| 3 | harness.yaml 필수 키 | §4.4 + §6 로드 목록 | 5키 필수 검사, `iac`는 선택 | **일치** |
| 4 | `secrets_format` | §4.4가 스키마 키로 정의 | **어떤 코드도 읽지 않음** | **비의도 드리프트** |
| 5 | `secrets_recipients` + recovery 강제 | §4.4 유효성 규칙 | `check_recipients()`가 정확히 구현 | **일치** |
| 6 | audit 검사 항목 | §8.1 표 6개 | 9개 검사 함수 + `--staged` | 문서화된 진화(D11~D13) + §8.1 스테일 |
| 7 | audit 스캔 제외 경로 | §8.1은 `secrets/` 밖만 규정 | `.git`·`.claude`도 제외 | **비의도 드리프트(경미)** |
| 8 | hook mutating 패턴 | §9 4계열 전 동사 | 6개 정규식이 빠짐없이 커버 | **일치** |
| 9 | `--dry-run` 제외 범위 | §9는 kubectl 항목에서만 | **전 도구 전역** 적용 | **비의도 드리프트(경미, 안전 방향)** |
| 10 | hooks.json | §9 JSON 블록 | 바이트 단위 동일 | **일치** |
| 11 | 템플릿 목록 | §10 표 11개 | 정확히 11개, 이름 일치 | **일치** |
| 12 | `keys.md` 컬럼 | §10 표는 7컬럼(D12 이전) | 9컬럼 | 문서화된 진화(D12) + §10 스테일 |
| 13 | fixture 수 | §5·§12 모두 2개 | **3개**(`harness-off` 추가) | **비의도 드리프트(경미)** |
| 14 | 테스트 범위 | §12 3항목 | 5개 파일 | 문서화된 진화 + §12 스테일 |
| 15 | audit 시나리오 | §12 4종 | 32개 audit 테스트 | 문서화된 진화(D13) + §12 스테일 |
| 16 | `CLAUDE.md` 스킬 수 | 실제 10종 | "9종" | **비의도 드리프트** |
| 17 | `CLAUDE.md` 테스트 수 | 실제 77개 | "55개" | **비의도 드리프트** |
| 18 | `CLAUDE.md` D 범위 | 스펙 D1~D14 | "D1~D9" | **비의도 드리프트** |
| 19 | `CLAUDE.md` 계획 문서 | 3개 | 1개만 열거 | **비의도 드리프트** |
| 20 | README | 실제와 일치 | 스킬 10종·D1~D14·fixture 3 전부 최신 | **일치** |
| 21 | `keys.md` 템플릿 vs fixture vs audit 파싱 | D12 9컬럼 | 3자 정합 | **일치** |

**비의도 드리프트는 총 9건**(#4·#7·#9·#13·#16~#19, 그리고 #7·#9는 경미). 나머지 대형 차이는 D10~D14가 근거인 문서화된 진화다.

### 5.3 main 스펙만 읽은 사람이 놀랄 지점

1. 10번째 스킬 `secrets`가 존재한다.
2. `keys.md`가 7컬럼 → 9컬럼으로 **파괴적 변경**됐다. 기존 7컬럼 파일은 audit에서 즉시 실패한다.
3. `harness.yaml`에 `secrets_format`·`secrets_recipients`가 생겼고, encrypted 하네스는 복구 수신자가 없으면 **audit 실패**로 전환된다.
4. audit 실패 카테고리 `[구조]`·`[키]`가 신설돼 기존에 통과하던 하네스가 실패할 수 있다.
5. audit이 심볼릭 링크를 읽기 전에 거부하고 `secrets/`를 재귀 스캔한다.
6. 위치 참조에 `op://`·`vault://`·`aws-secretsmanager://` 스킴이 도입됐다.

### 5.4 테스트

`bash tests/run_tests.sh` → **77 tests, OK (실패 0, 에러 0)**. 구성: audit 32 · change_reminder 15 · harness_lib 14 · sync 11 · skills 5.

---

## 6. 외부 리서치

조사일은 전부 **2026-08-06**이다. 확인하지 못한 항목은 "확인 불가"로 남겼다.

### 6.1 플랫폼 스펙 재확인 (공식 문서)

스펙 부록 A가 "구현 시점에 재확인한다"고 전제한 항목들을 현재 문서로 다시 확인했다.

| 항목 | 확인 결과 | 출처 |
|---|---|---|
| 권한 규칙 경로 앵커 | 스펙 부록 A의 서술이 **정확하다**. `//path`=파일시스템 루트, `~/path`=홈, `/path`=**설정 파일 출처** 기준, `path`·`./path`=cwd 기준. Read/Edit 규칙은 **gitignore 패턴 문법**을 쓴다 | [Configure permissions](https://code.claude.com/docs/en/permissions) |
| deny 규칙의 매칭 깊이 | **allow와 deny가 다르다.** 단일 세그먼트 디렉터리 패턴에서 allow는 cwd 직속만, **deny·ask는 임의 깊이**를 매치한다. §3.3의 실측이 이 규정과 일치한다 | 동상 |
| 사용자 설정의 `/secrets/**` | 문서가 함정을 명시: 사용자 설정의 `Read(/secrets/**)`는 `~/.claude/secrets/**`를 막고 **프로젝트의 `secrets`는 막지 않는다**. 프로젝트마다 적용하려면 `//` 절대 경로나 `~/`를 쓰라고 안내 | 동상 |
| Read 규칙의 적용 범위 | **문서 자신이 "best-effort"라고 표현한다** — "Claude makes a **best-effort** attempt to apply `Read` rules to all built-in tools that read files like Grep and Glob". 즉 D13의 "가드레일이며 보안 경계가 아님"은 플랫폼 문서와 정합적이다 | 동상 |
| Bash와 파일 읽기 | `cat`·`head`·`grep`·`ls` 등은 **내장 read-only 명령 집합**으로 인식되며, 이 집합에 대해 deny 규칙을 걸 수 있다. 반면 임의 인터프리터 호출(`python3 -c`)은 이 집합 밖이라 파일 읽기로 분석되지 않는다 — §3.3에서 `cat`은 막히고 `python3 -c`는 통과한 실측이 이 구조로 설명된다 | 동상 |
| Read deny와 쓰기 | Read deny 규칙은 같은 경로의 **Edit도** 막지만 **Write·NotebookEdit은 막지 않는다**. `secrets/`에 대한 쓰기를 막으려면 `Edit` deny를 따로 걸어야 한다 | 동상 |
| `.claude/settings.json` 로드 위치 | **cwd의 `.claude/`에서만, 부모 폴백 없이** 로드된다. `settings.local.json`만 git 저장소 루트에서 로드된다. D1의 상향 탐색과 어긋나는 비대칭의 근거(§4 P0-3) | 동상 |
| **플러그인의 MCP 서버 동봉** | **가능하다.** 위치는 **플러그인 루트의 `.mcp.json`** 또는 `plugin.json` 인라인 `mcpServers`. `command`·`args`·`env`에서 `${CLAUDE_PLUGIN_ROOT}` 사용 가능. 도구 이름은 `mcp__plugin_<플러그인>_<서버>__<도구>`로 스코프되며, hook matcher·권한 규칙에 **풀네임을 써야** 발화한다 | [Plugins reference](https://code.claude.com/docs/en/plugins-reference), [MCP](https://code.claude.com/docs/en/mcp) |
| **플러그인 `settings.json`의 지원 키** | **`agent`와 `subagentStatusLine`뿐** — 즉 플러그인이 자기 `permissions.deny`를 배포할 수 없다. D3의 템플릿 복사 방식이 유일해임을 확정한다 | [Plugins reference](https://code.claude.com/docs/en/plugins-reference) |
| **`userConfig`의 `sensitive: true`** | 플러그인이 사용자에게 값을 묻는 필드를 선언할 수 있고, `sensitive: true`면 입력이 마스킹되고 `settings.json`이 아니라 **secure storage**에 저장된다. MCP 토큰 취급의 플랫폼 정식 경로(§3.4) | 동상 |
| 플러그인 컴포넌트 | 스킬·에이전트·hooks·**MCP 서버**·LSP 서버·모니터. `.claude-plugin/`에는 `plugin.json`만 두어야 한다는 것도 Warning으로 확인 | 동상 |
| `-p` 비대화형 실행 | trust verification이 비활성화된다. 자동화 경로 운영 지침에 반영 필요 | [Security](https://code.claude.com/docs/en/security) |

**§3.7에 주는 함의**: 2단계 MCP 전환의 플랫폼 전제가 충족된다. `.mcp.json`을 플러그인 루트에 두고 `command`를 `${CLAUDE_PLUGIN_ROOT}/scripts/secret_server.py`로 지정하면 D2(python3 stdlib)를 지키면서 동봉이 가능하다. 1단계 스크립트를 그대로 MCP 서버의 실행 본체로 재사용할 수 있으므로 두 단계가 연속적이다.

### 6.2 시크릿 관리 모범사례

| 항목 | 확인 결과 | 출처 |
|---|---|---|
| `sops exec-env` 권장 근거 | 복호값이 **자식 프로세스 메모리에만** 존재하고 종료 시 사라진다. `source <(sops -d ...)`는 호출 셸 환경에 값이 남으므로 열등하다 — 플러그인이 `exec-env`를 표준으로 택한 것은 모범사례와 일치 | [Commit Your Secrets to Git, Encrypted, with SOPS and age](https://tvi.al/commit-your-secrets-to-git-encrypted-with-sops-and-age/), [SOPS 공식 문서](https://getsops.io/docs/) |
| 환경변수 노출 잔여 위험 | `ps e`·`/proc/<PID>/environ`으로 같은 권한 사용자가 환경변수를 읽을 수 있다. 다중 사용자 시스템은 `hidepid=2`로 완화한다 | [Linux: Securing Environment Variables](https://linuxvox.com/blog/linux-securing-environment-variables/) |
| age 키 관리 | **개인 키는 절대 git에 넣지 않는다**가 핵심 규칙 — 패스워드 매니저·`~/.config/sops/age/`·CI 시크릿에 둔다. D11의 "암호문만 동기화, 복호 키는 각 머신 로컬"과 일치 | [Managing Secrets with SOPS, AGE, and 1Password](https://paulocurado.com/blog/managing-secrets-with-sops-age-and-1password/) |
| 런타임 복호 원칙 | 암호화 상태로 보관하고 **필요한 순간에만** 복호해 노출 창을 최소화한다 | [How to Use Mozilla SOPS for Secret Encryption](https://oneuptime.com/blog/post/2026-03-02-how-to-use-mozilla-sops-for-secret-encryption-on-ubuntu/view) |

**보강 발견 3건**:

- **`sops exec-file`이 `exec-env`보다 강하다.** `exec-file`은 기본이 **FIFO**여서 평문이 디스크에 닿지 않고 **자식이 단 한 번만 읽을 수 있다**. 또 SOPS 문서는 unix에서 `--user <username>` 권한 강등을 "added security를 위해 가능한 곳에서는 써야 한다"고 명시 권고한다. 플러그인의 표준 예시가 `exec-env` 일변도인 점은 재검토 여지가 있다. ([SOPS advanced usage](https://getsops.io/docs/usage/advanced/))
- **환경변수 위험의 근거는 SOPS가 아니라 OWASP다.** SOPS 공식 문서에는 `/proc/PID/environ`·`ps eww` 경고가 없다. 근거로 인용할 것은 [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) 5.1절이며, 여기서 환경변수를 명시적으로 비권장한다(모든 프로세스가 접근 가능 + 로그·시스템 덤프에 포함될 수 있음).
- **이 위험은 Claude Code에서 실증됐다.** Claude Code GitHub Action 프롬프트 인젝션 체인에서 에이전트가 `/proc/self/environ`을 읽어 `ANTHROPIC_API_KEY`와 쓰기 권한 `GITHUB_TOKEN`을 탈취한 사례가 문서화됐다. 가설이 아니라 이 도구에서 실제로 성립한 공격이다. ([CSA Research Note, 2026-06-05](https://labs.cloudsecurityalliance.org/research/csa-research-note-claude-code-github-action-prompt-injection/))
- **Vault 측 근거**: HashiCorp Production Hardening이 "Use standard input for vault secrets"를 항목으로 두고, 커맨드라인 인자 위험을 shell history 잔존 + **같은 호스트의 다른 비특권 사용자가 읽을 수 있음**으로 설명한다. 플러그인의 argv 금지 규칙에 붙일 공식 근거다. 단 `vault kv get -field=` 전용 경고는 공식 문서에 없으므로 원리로 유추 인용해야 한다. ([Production Hardening](https://developer.hashicorp.com/vault/docs/concepts/production-hardening))

**함의**: 플러그인의 시크릿 규약(argv 금지, 복호 키 로컬 분리, `-field` 강제)은 외부 모범사례와 어긋나는 지점이 없고 오히려 근거가 튼튼하다. 보강할 곳은 두 군데다 — ①`exec-file`/`--user`를 표준 예시에 반영 ②`exec-env`가 남기는 `/proc` 노출 잔여 위험을 문서에 명시(§4 P0-2 정정과 함께).

### 6.2.1 AI 에이전트 컨텍스트에 시크릿을 두지 않는 설계 — 표준 근거가 있다

이전 조사에서 "확인 불가"로 두었던 항목인데, **확립된 최신 근거가 존재한다.**

- ⭐ **OWASP LLM Top 10 2026판이 2026-08-04에 발행됐다**(이 검토 이틀 전). 신규 항목 **LLM08:2026 Hidden Context Exposure**가 "비밀은 컨텍스트에 들어가면 안 된다"를 정면으로 명문화한다. 명제 셋: ①hidden context는 **발견 가능하다고 가정하고** 설계하라 ②자격증명·연결 문자열·토큰을 hidden context에 임베드하지 말라 ③hidden context를 **보안 경계로 삼지 말라**. 원문 표현이 특히 정확하다 — "any contents of the context should not be considered a secret". ([OWASP GenAI LLM Top 10 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/))
- **LLM02:2026 Sensitive Information Disclosure**는 유출 채널이 최종 답변만이 아님을 강조한다 — tool-call 인자, reasoning trace, 검색 청크, 로그, 텔레메트리가 전부 유출면이며 **모두 output으로 취급해 동일한 마스킹 규칙을 적용**하라고 한다. 이번 검토가 §3.3에서 채널을 열거해 각각 측정한 방식이 이 권고와 같은 형태다.
- **Anthropic 공식 입장도 같은 방향이다** — "the environment the agent loop runs in should never hold a credential worth stealing", 그리고 커넥터 인가 토큰은 샌드박스에 들어가지 않고 리버스 프록시가 실제 자격증명을 주입한다. ([CISO's guide to agentic AI, 2026-07-17](https://claude.com/blog/ciso-guide-to-agentic-ai))
- **HashiCorp도 동일 아키텍처를 벤더 공식 패턴으로 문서화했다** — LLM은 민감 리소스에 직접 접근하지 않고 위임 신원으로 MCP 서버만 호출하며, **MCP 서버가 Vault와 API 로직을 캡슐화**한다. ([Validated Pattern: Secure AI agent authentication using Vault dynamic secrets](https://developer.hashicorp.com/validated-patterns/vault/ai-agent-identity-with-hashicorp-vault))

**함의 — 평가가 바뀐다.** 앞선 조사에서는 원칙 1을 "선행 사례 없는 독자적 설계"로 볼 여지를 남겼으나, 실제로는 **OWASP·Anthropic·HashiCorp 세 독립 출처가 수렴하는 패턴과 정확히 일치한다.** 이 플러그인의 원칙 1·2는 업계 방향을 앞서 구현한 쪽에 가깝다. 다만 인용할 때 "secret never enters prompt"는 표준 용어가 아니므로 **LLM08:2026 Hidden Context Exposure**를 쓰는 편이 정확하다. 그리고 같은 표준이 "hidden context를 보안 경계로 삼지 말라"고 하는 만큼, §4 P0-2의 README 정정은 표준 준수 차원에서도 필요하다.

**MCP 스펙과의 긴장 하나**: MCP 인가 스펙은 **stdio 전송 구현이 인가 스펙을 따르지 말고 환경으로부터 자격증명을 조회하라**고 규정해, 로컬 stdio 서버에 대해 환경변수 방식을 사실상 승인한다. 이는 OWASP 5.1절 및 위 CSA 실증과 충돌한다. §3.7의 MCP 2단계로 갈 때 이 충돌을 **명시적으로 다뤄야 한다**(플랫폼의 `userConfig sensitive:true`가 이 문제의 실질적 우회로다).

### 6.3 유사 도구 비교

| 도구 | 접근 방식 | 이 플러그인에 주는 시사점 | 출처 |
|---|---|---|---|
| NetBox | DCIM/IPAM 전용 DB. 호스트명·기본 IP·플랫폼·디바이스 역할·사이트를 **구조화 필드**로 두고, config context로 추가 변수를 얹는다. 사이트·랙·역할·플랫폼 등 임의 섹션으로 그룹핑 | 사양·네트워크를 **구조화 필드로 두는 쪽**이 업계 표준에 가깝다 — §1 Q4의 최소 승격 권고를 뒷받침한다. 다만 NetBox는 전용 DB를 두는 무거운 선택이며, 하네스가 "지도이지 엔진이 아니다"(원칙 4)를 유지하려면 전면 도입은 부적합 | [NetBox as Ansible dynamic inventory](https://netboxlabs.com/blog/how-to-use-netbox-as-a-dynamic-inventory-source-for-the-red-hat-ansible-automation-platform/), [nb_inventory 문서](https://docs.ansible.com/projects/ansible/latest/collections/netbox/netbox/nb_inventory_inventory.html) |
| Ansible inventory | 그룹이 1급 개념이다. 호스트를 그룹에 넣고 그룹 변수를 상속시킨다 | **P1-5(비-k8s 클러스터)의 직접적 참고**: 클러스터를 새 엔티티 타입으로 만들지 않고 **그룹 멤버십 필드**로 표현하는 것이 검증된 패턴이다. §4 P1-5의 권고 (b)와 일치 | [ansible-netbox-inventory](https://pypi.org/project/ansible-netbox-inventory/) |
| NetBox + Ansible 동적 인벤토리 | NetBox를 SSOT로 두고 인벤토리를 **API에서 동적 생성**해 정적 파일 유지보수를 없앤다 | 하네스의 `sync`가 지향하는 방향과 같되, 이 플러그인은 문서를 SSOT로 두지 않고 "실제 상태가 SSOT"라고 선언한 점이 다르다(원칙 4). 대신 drift 보고로 간극을 드러내는 방식인데, **P1-4(온프렘 미대조)가 그 방식의 신뢰도를 직접 훼손**한다 | [NetBox+Ansible 동적 인벤토리](https://smenode-academy.com/blog/netbox-ansible-how-to-build-a-dynamic-inventory-that-actually-stays-accurate/) |

### 6.3.1 인벤토리 도구의 데이터 모델링 — 업계도 비어 있는 자리

Q4와 P1-5에 직접 걸리는 발견이다.

- ⭐ **NetBox의 물리 `Device`에는 CPU·RAM·디스크 구조화 필드가 없다.** 필드는 Device Type·Platform·Rack·Position 등 배치·식별 중심이다. 그런데 **`VirtualMachine`에는 `vCPUs`·`Memory`·`Disk`가 1급 필드로 있다.** 즉 업계 표준 도구조차 **물리 서버 스펙은 모델링하지 않고 VM만 모델링한다**. CPU/RAM 추가는 Custom Field로 가능하지만 core 필드가 아닌 우회 경로다. ([Device](https://netboxlabs.com/docs/netbox/models/dcim/device/), [VirtualMachine](https://netboxlabs.com/docs/netbox/models/virtualization/virtualmachine/))
- ⭐ **NetBox의 `Cluster`는 가상화 전용**이다("virtual machines run within"). `VirtualChassis`는 컨트롤 플레인을 공유하는 스택 스위치용이다. **카프카 클러스터나 DB active-standby를 표현하는 용도가 아니다.** active/standby를 명시 모델링하는 것은 `FHRPGroup`(HSRP/VRRP) 정도인데 이는 네트워크 게이트웨이 이중화 프로토콜 레벨이다. ([Cluster](https://netboxlabs.com/docs/netbox/models/virtualization/cluster/))
- **Ansible inventory**는 그룹 멤버십이 1급이지만(parent/child) host/group 변수는 **스키마 없는 자유형**이고, active/standby 역할은 그룹명 관습이나 변수로 표현될 뿐 스키마 강제가 없다. ([intro_inventory](https://raw.githubusercontent.com/ansible/ansible-documentation/devel/docs/docsite/rst/inventory_guide/intro_inventory.rst))
- **Backstage**는 소프트웨어 카탈로그라 CPU/RAM/IP/VLAN 구조화 필드가 표준 descriptor format에 없고 역할 개념도 없다. ([Descriptor format](https://backstage.io/docs/features/software-catalog/descriptor-format))
- ⚠️ **Terraform state는 "매핑 도구이지 인벤토리가 아니다"**라고 문서가 명시하며, 수동 수정 시 **"exposure of secrets stored in the state file"**을 경고한다. 하네스가 `managed_by: terraform://`로 state를 참조만 하고 값을 끌어오지 않는 설계는 이 위험을 피한다. ([Terraform state](https://developer.hashicorp.com/terraform/language/state))

**함의 — P1-5의 성격이 바뀐다.** "비-k8s 클러스터를 표현할 수 없다"는 이 플러그인만의 결함이 아니라 **인벤토리 도구 4종 전부에 비어 있는 자리**다. 따라서 무거운 신규 타입을 발명하기보다 Ansible식 **그룹 멤버십 필드**(§4 P1-5 권고 (b))가 검증된 최소 해법이라는 판단이 강화된다. 동시에 Q4에서 사양 필드를 **선택적으로만** 승격하자는 권고도 NetBox의 비대칭(물리는 미모델링, VM만 모델링)과 일관된다.

### 6.3.2 AI 인프라 운영 도구의 읽기/쓰기 분리

| 도구 | 분리 방식 | 시사점 |
|---|---|---|
| ⭐ **HolmesGPT** (CNCF sandbox) | **"By design, HolmesGPT has read-only access and respects RBAC permissions. It is safe to run in production environments."** write는 별도 opt-in 툴셋으로 완전 분리(기본 비활성). 안전장치 둘 다 기본 `["*"]` — `restrictedTools`(runbook 호출로만 허용), `approvalRequiredTools`(실행 전 확인 필수). `--kubeconfig`/`--context`/`--token` 플래그는 **항상 차단**, 셸 메타문자 거부 | **이 플러그인에 가장 직접적인 프라이어 아트.** 원칙 7(읽기/변경 분리)과 정책 게이트가 같은 구조다. 배울 점은 "승인 필요 도구를 runbook 경유로만 허용"하는 이중 게이트 ([repo](https://github.com/robusta-dev/holmesgpt)) |
| **k8sgpt** | read-only 분석 전용, mutation 기능 자체가 없음 | 가장 보수적 |
| **kubectl-ai** | mutating을 실제 실행, 확인 프롬프트가 유일한 장치이며 `--skip-permissions`로 우회 가능 | 안전장치 최약 — 참고하지 말 것 |
| ⚠️ **AWS API MCP Server** (awslabs) | `READ_OPERATIONS_ONLY`·`REQUIRE_MUTATION_CONSENT` **둘 다 기본 `false`** | 공식 도구도 기본값이 위험할 수 있다 |
| ⭐⭐ **CVE-2026-46519** | `mcp-server-kubernetes` v3.6.0 이전에서 read-only 환경변수가 `tools/list`에만 적용되고 `tools/call`에는 미적용 → **read-only 상태에서도 `kubectl_delete`를 이름으로 직접 호출해 파드 삭제 가능** | **접근 제어를 도구 목록 필터링으로 구현하면 무력화된다.** §3.7 설계안에 반영함 ([분석](https://www.manifold.security/blog/mcp-server-kubernetes-readonly-bypass)) |
| ⭐ **NetBox Cloud Branching** | "Agents can work in isolated branches. **Changes stay contained until a human reviews the diff and merges.**" | **인벤토리 문서를 다루는 이 플러그인에 가장 잘 맞는 승인 게이트 패턴** — git PR 워크플로와 동형이며, `sharing: git` 하네스라면 거의 그대로 적용 가능하다 ([NetBox MCP](https://netboxlabs.com/docs/mcp/)) |

**MCP 스펙 준수 체크리스트**(동봉 시): Token Passthrough 금지(MUST NOT), state handle을 인증으로 취급 금지, Scope Minimization(와일드카드 `*`/`all`/`full-access` 금지), SSRF로 `169.254.169.254` 클라우드 메타데이터 탈취 경고. 마지막 항목은 이 플러그인이 이미 SSH allowlist에서 차단하고 있는 대상과 같다. ([MCP Security Best Practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices))

### 6.3.3 VictoriaMetrics·VictoriaLogs MCP — 존재하며 1st-party다

시나리오 ②의 대상이 실재하는지 확인했다. **둘 다 VictoriaMetrics 조직 공식 서버다.**

- `VictoriaMetrics/mcp-victoriametrics` — 설치는 릴리스 바이너리, Docker(`ghcr.io/victoriametrics/mcp-victoriametrics`), 소스 빌드(Go 1.26+), Helm. 전송은 `MCP_SERVER_MODE`로 stdio(기본)/sse/http.
- 필수 환경변수는 **`VM_INSTANCE_ENTRYPOINT`**와 **`VM_INSTANCE_TYPE`**("single"/"cluster")이고, 인증은 **`VM_INSTANCE_BEARER_TOKEN`(선택) 하나뿐**이다.
- ⭐ **read-only 전용 플래그가 없는데, write 기능 자체가 구현돼 있지 않기 때문이다.** "All read-only APIs of VictoriaMetrics"만 지원한다. 도구 24종+(query, query_range, labels, series, rules, alerts 등).
- `VictoriaMetrics/mcp-victorialogs`도 1st-party이며 `VL_INSTANCE_ENTRYPOINT`·`VL_INSTANCE_BEARER_TOKEN`을 쓰고 역시 read-only다.

([mcp-victoriametrics](https://github.com/VictoriaMetrics/mcp-victoriametrics), [mcp-victorialogs](https://github.com/VictoriaMetrics/mcp-victorialogs))

**함의 — 시나리오 ②의 난이도가 크게 낮아진다.** 대상 MCP가 ①write 미구현이라 읽기/쓰기 분리 고민이 불필요하고 ②인증이 bearer token 단 하나다. 따라서 §3.4의 권고("값을 담지 않는 산출물")가 실용적으로 충분하다 — 하네스가 `VM_INSTANCE_ENTRYPOINT`·`VM_INSTANCE_TYPE`을 채운 `.mcp.json` 스캐폴드를 생성하고, 토큰만 수신 개발자가 `userConfig sensitive:true`나 자기 환경에서 채우면 된다. **값을 담아 전달할 실질적 이유가 거의 없다.**

덧붙여 이 발견은 P1-2(로그 조회 경로 없음)에도 답을 준다. VictoriaLogs MCP를 `ops`의 대안 경로로 두면 LogsQL 문법을 reference에 직접 담지 않고도 로그 조회를 커버할 수 있다.

### 6.3.4 온프렘·비-k8s 영역

- ⭐ **HolmesGPT만이 k8s를 넘어선다** — DB(PostgreSQL·MySQL·MongoDB 등), 관측(Prometheus·Grafana·**VictoriaMetrics**), **메시지 큐(Kafka·RabbitMQ)**, 클라우드, Bash 툴셋을 갖췄다. **카프카 + DB + VictoriaMetrics 조합을 이미 커버하는 유일한 오픈소스 선행 사례**다.
- **Kafka 1st-party MCP는 제안 단계**(KIP-1318, Under Discussion). 설계상 read/write를 MCP 프리미티브로 분리한다 — **Resources=read-only, Tools=state-changing**. `mcp.readonly`, `mcp.tools.allowed/denied`, `mcp.allowed.topic.prefixes`, `mcp.approval.required.tools`. 승인 게이트 설계의 참고가 된다. ([KIP-1318](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1318:+Model+Context+Protocol+(MCP)+Server+for+Apache+Kafka))
- **Red Hat AAP MCP 서버**(Technology preview)가 비-k8s 온프렘 AI 운영의 가장 성숙한 선행 사례다. dual-layer security model(서버 레벨 + 사용자 레벨 권한), read-only 또는 read-write **모드 택일**. ([Red Hat 블로그](https://www.redhat.com/en/blog/it-automation-agentic-ai-introducing-mcp-server-red-hat-ansible-automation-platform))
- **SSH 기반 베어메탈 AI 에이전트는 신뢰할 만한 1st-party 프로젝트가 없다** — 커뮤니티 소규모 MCP만 산재한다(낮은 신뢰도).

**함의**: "온프렘 물리 서버 인벤토리 + 비-k8s 클러스터 역할 모델링 + read-only 기본 AI 운영"의 조합은 현재 선행 사례에 **실제로 비어 있는 자리**다. 이 플러그인이 겨냥한 위치가 유효하다는 뜻이면서, 동시에 참고할 설계가 적어 스스로 결정해야 할 것이 많다는 뜻이기도 하다.

**여전히 확인 불가**: OWASP Agentic AI Threats & Mitigations 등의 PDF 원문은 다운로드 게이팅으로 확인하지 못했고(ASI01–ASI10 항목 목록만 검증), Ansible Lightspeed의 2026년 현재 상태는 문서 호스트 접근 실패로 확인하지 못했다.

---

## 부록 A. 재현 절차

```bash
cd <scratchpad>
python3 setup_lab.py        # 스텁 CLI 15종 + 모의 하네스 + 오염 하네스
python3 blind_canary.py     # 1차 블라인드 카나리 (양성 대조용)
python3 channel_probe.py    # 2차 카나리 심기 + 채널별 유출 측정
python3 profile_matrix.py   # 환경 프로파일 5종 × audit/sync
python3 verify_leak.py      # 트랜스크립트·산출물 최종 카나리 검사
```

모든 산출물은 리포 밖 스크래치에만 생성된다. 실 머신 메타데이터(프로파일명·컨텍스트명·호스트명)는 전부 합성값으로 대체했다.

## 부록 B. 증거의 한계 (정직한 기재)

- **스텁 충실도**: `sync --collect`가 보고한 "문서 누락/유령" 항목 일부는 스텁 출력이 실제 CLI 출력 형식과 달라 생긴 산물이다(예: `gcloud --format value(name)`은 실제로 헤더를 내지 않는데 스텁은 냈다). 따라서 **diff 내용 자체는 정확도 판정의 근거로 쓰지 않았다.** 이 구동에서 채택한 근거는 ①실 인프라 호출 0건 ②생성 명령의 context/profile 명시 ③파싱 불가 출력을 "확인 불가"로 분리하는 동작 세 가지뿐이다.
- **LLM 비결정성**: 스크립트·hook은 결정론적이라 1회 실행으로 충분하지만, 스킬 문서를 따르는 클로드의 행동은 실행마다 달라질 수 있다. §3의 "무유출"은 **결정론적 경로(스크립트·hook·git)에 대한 결론**이며, 스킬 지시를 따르는 행동 경로에 대해서는 문서 분석 근거만 있다.
- **프로파일 축약**: 18개 조합 전수가 아니라 대표 5개다. 각 축 값은 최소 1회 등장하지만 조합 간 상호작용은 전부 검증되지 않았다.
- **논외 기록**: 언어(스킬 본문·산출 문서가 한국어 고정)와 OS(스크립트가 python3/POSIX 전제) 범용성, marketplace 배포는 이번 판정 범위 밖이다. 오픈소스 공개 시에는 한국어 고정이 사용자층을 제한한다는 점만 기록해 둔다.

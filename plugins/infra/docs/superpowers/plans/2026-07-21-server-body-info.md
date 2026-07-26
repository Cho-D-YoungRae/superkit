# 서버 정보 본문화(D10) 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development(권장) 또는 executing-plans로 태스크 단위 실행. 스텝은 체크박스(`- [ ]`)로 추적.

**Goal:** 서버의 사양·IP·아키텍처·특이 정보를 frontmatter 필드로 규정하지 않고 markdown **본문**에 자유 서술로 관리한다(스펙 D10). 파서·`REQUIRED_FIELDS`·`schema_version`은 건드리지 않는다.

**Architecture:** 세 갈래 변경 — ① 데이터 모델: `templates/server.md` 본문에 관례 섹션(`## 네트워크`/`## 사양`/`## 특이사항`) 스캐폴드 + 본문이 기계 계층(파서·audit)에 영향을 주지 않음을 fixture로 회귀 고정. ② 쓰기: `register`가 확정 값으로 본문을 채우고, ssh 접근이 있으면 동의 기반 read-only allowlist로 사양을 수집해 본문에 기록. ③ 읽기: `lookup`이 사양·IP 질의에 본문 관례 섹션을 읽어 답. scripts/ 변경 없음(순수 skill/template/fixture/doc).

**Tech Stack:** SKILL.md(한국어 마크다운), 엔티티 템플릿, python3 stdlib unittest(fixture 회귀).

## Global Constraints

- 스펙 D10이 SSOT. frontmatter는 스킬이 파싱하는 운영 메타데이터만, 이질적 정보는 본문.
- **frontmatter 파서·`REQUIRED_FIELDS`·harness.yaml 로더를 변경하지 않는다**(후방호환). audit은 본문을 검사하지 않는다.
- 원칙 1: ssh 사양 수집 시에도 키 **값**을 노출하지 않는다 — `access/keys.md`의 위치 참조를 조립(`ssh -i <경로>`)해 실행. 수집 명령은 read-only allowlist만(sudo·자격증명 파일·메타데이터 엔드포인트 금지).
- 원칙 6: register가 제안·실행하는 모든 원격 명령은 대상 호스트를 명시(현재 ssh 컨텍스트 의존 금지).
- 테스트 실행은 `bash tests/run_tests.sh`. 커밋은 태스크마다, 한국어 Conventional Commits + 트레일러 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- 스킬 편집은 `tests/test_skills.py`의 강제 조건(frontmatter name=디렉토리, description 한 줄 스칼라 ≥80자, 본문에 "원칙"·"harness.yaml")을 계속 통과해야 한다.

---

### Task 1: server 템플릿 본문 관례 + 본문-무시 회귀 테스트

**Files:**
- Modify: `templates/server.md` (본문에 관례 섹션 스캐폴드 추가)
- Modify: `tests/fixtures/harness-ok/inventory/prod-db-01.md` (본문 추가)
- Modify: `tests/test_harness_lib.py` (본문 무시 assert 추가)
- Test: `tests/test_audit.py`(기존 `test_ok_harness_passes`가 본문 추가 후에도 통과함을 재확인 — 코드 변경 없음)

**Interfaces:**
- Consumes: 기존 `harness_lib.parse_frontmatter`/`iter_entities`, `audit.run_audit`.
- Produces: D10 불변식의 회귀 고정 — "엔티티 본문(콜론 줄·리스트·`---` 수평선 포함)은 frontmatter 파싱·audit에 영향을 주지 않는다". 이후 Task 2/3가 이 본문 구조를 채우고 읽는다.

- [ ] **Step 1: 실패 테스트 작성 — 본문 추가 + 파서가 본문을 무시하는지 검증**

먼저 `tests/fixtures/harness-ok/inventory/prod-db-01.md`에 본문을 추가한다(frontmatter는 그대로, 닫는 `---` 아래에 본문 append). 최종 파일:

```markdown
---
id: prod-db-01
type: server
env: prod
provider: aws-main
runtime: ec2
purpose: "PostgreSQL 단독 DB 서버"
access: "ssh, 키: keys.md#deploy-key"
managed_by: manual
depends_on: []
---

# prod-db-01

## 네트워크
- 사설 IP: 10.0.12.34
- 공인 IP: 3.35.10.20 (EIP 고정)

## 사양  <!-- register가 ssh로 수집, 2026-07-21 -->
- arch: x86_64 / vCPU 8 / 32GiB
- 디스크: gp3 500GB + 데이터 2TB NVMe RAID1

---

## 특이사항
- 매일 02:00 pg_dump 배치 — 이 시간대 IO 지연 주의
```

(본문에 콜론 줄 `- 사설 IP: ...`, `arch: ...`, 그리고 마크다운 수평선 `---`를 일부러 포함해 파서 견고성을 함께 고정한다.)

그다음 `tests/test_harness_lib.py`의 `TestParseFrontmatter` 클래스에 메서드를 추가한다:

```python
    def test_body_is_ignored(self):
        # 본문에 콜론 줄·리스트·--- 수평선이 있어도 frontmatter만 파싱된다 (스펙 D10)
        fm = harness_lib.parse_frontmatter((OK / "inventory" / "prod-db-01.md").read_text(encoding="utf-8"))
        self.assertEqual(set(fm), {"id", "type", "env", "provider", "runtime",
                                   "purpose", "access", "managed_by", "depends_on"})
        self.assertNotIn("사설 IP", fm)
        self.assertNotIn("arch", fm)
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `bash tests/run_tests.sh 2>&1 | tail -6`
Expected: `test_body_is_ignored`가 FAIL — 현재 `prod-db-01.md`엔 본문이 없어 새 assert 자체는 통과할 수 있으나, **본문 추가 전이라면** 이 스텝은 "본문을 먼저 추가"가 전제다. 본문을 추가한 상태에서 만약 파서가 본문을 잘못 먹으면 `set(fm)`에 `arch` 등이 섞여 FAIL한다. (파서가 이미 올바르면 GREEN이 나올 수 있음 — 그 경우 이 테스트는 회귀 방지용 고정으로서 유효하며, Step 3~4를 건너뛰고 커밋으로 진행한다.)

- [ ] **Step 3: 템플릿에 관례 섹션 추가**

`templates/server.md`의 본문(`# {{id}}` 아래 `<!-- 히스토리·주의사항 자유 서술 -->` 부분)을 다음으로 교체한다:

```markdown
# {{id}}

<!--
  운영 메타데이터는 위 frontmatter에, 이질적 정보(IP·사양·특이사항)는 이 본문에 자유 서술한다(스펙 D10).
  아래 관례 섹션은 권장일 뿐 강제가 아니다 — 서버마다 필요한 것만 남기고 나머지는 지운다.
  audit은 본문을 검사하지 않는다.
-->

## 네트워크
- 사설 IP:
- 공인 IP:

## 사양
- arch:
- vCPU / 메모리:
- 디스크:

## 특이사항
-
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `bash tests/run_tests.sh 2>&1 | tail -6`
Expected: PASS — `test_body_is_ignored`·`test_parses_server`(기존)·`test_ok_harness_passes`(audit, 본문 추가 후에도 실패 0) 모두 통과.

- [ ] **Step 5: 커밋**

```bash
git add templates/server.md tests/fixtures/harness-ok/inventory/prod-db-01.md tests/test_harness_lib.py
git commit -m "feat: server 본문 관례 섹션(D10) + 본문-무시 회귀 테스트

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: register — 본문 채우기 + ssh 사양 수집

**Files:**
- Modify: `skills/register/SKILL.md`

**Interfaces:**
- Consumes: Task 1의 `templates/server.md` 본문 관례, 기존 §4 스캔 규약(ssh 키 위치 참조 조립).
- Produces: server 등록 시 본문을 채우는 절차 — Task 3의 lookup이 이 본문 구조를 읽는다.

- [ ] **Step 1: §3 대화형 모드에 "본문 채우기" 규정 추가**

`skills/register/SKILL.md`의 §3(대화형 모드) 3번 항목(server/k8s-cluster/component 파일 생성) 뒤에, server일 때 본문을 채우는 절차를 추가한다. 반드시 담을 내용:

- server 엔티티는 frontmatter(운영 메타데이터)만이 아니라 **본문**의 관례 섹션(`## 네트워크`/`## 사양`/`## 특이사항`)도 인터뷰·스캔으로 확인된 값으로 채운다. 값이 없는 항목·섹션은 비워두지 말고 그 줄/섹션을 지운다(스펙 D10 — 강제 아님).
- 사설/공인 IP·아키텍처·사양·특이사항은 frontmatter 필드가 아니라 **본문**에 쓴다. 사용자가 "필드에 없는 정보"를 주면 적절한 본문 섹션(없으면 새 섹션)에 서술한다.
- 클라우드 provider면 IP·arch를 `aws ec2 describe-instances --profile <p> --region <r>` / `gcloud compute instances describe --configuration <c>` 같은 **read-only** 명령으로 조회해 후보로 제안할 수 있다(원칙 6 — profile/region 명시). 채택 값은 본문에 기록한다.

- [ ] **Step 2: §4 스캔 우선에 "server 사양 ssh 수집" 규정 추가**

`skills/register/SKILL.md`의 §4(스캔 우선) "server 등록 시" 항목을 확장한다. 반드시 담을 내용:

- 등록 중인 server의 `access`에 ssh 정보가 있으면, **사용자 동의를 받은 뒤** 아래 **read-only allowlist** 명령만으로 사양을 수집해 `## 사양` 섹션 후보로 제안한다. `<키경로>`는 값이 아니라 `access/keys.md` 위치 참조 컬럼 값을 조립해 넣는다(원칙 1 — 키 값 미노출):

  ```
  ssh -i <키경로> -o BatchMode=yes -o ConnectTimeout=5 <사용자>@<호스트> \
    'uname -m; nproc; free -h 2>/dev/null | head -2; df -h --total 2>/dev/null | tail -1; lsblk -d -o NAME,SIZE 2>/dev/null'
  ```

- **금지**: `sudo`, 환경변수 덤프(`env`/`printenv`), 클라우드 메타데이터 엔드포인트(`169.254.169.254`), 프로세스 커맨드라인, 설정·자격증명 파일 열람. `StrictHostKeyChecking=no`를 붙이지 않는다(정상 host-key 검증 유지).
- 수집 결과 중 **`arch`만 확정 사양으로** `## 사양`에 남기고, vCPU·메모리·디스크는 "수집 시각(오늘 날짜) 기준 참고값"으로 주석과 함께 기록한다(런타임 관측값이라 낡을 수 있음 — 원칙 4). 온프렘·baremetal은 하드웨어가 사실상 불변이므로 그대로 기록해도 무방하다고 안내한다.
- 일괄(batch) ssh 수집은 대상 호스트 **전체 목록을 확인**받은 뒤에만 실행한다(열린 서브넷·인벤토리 전체 스윕 금지).

- [ ] **Step 3: 테스트 통과 확인**

Run: `bash tests/run_tests.sh 2>&1 | tail -4`
Expected: PASS — `tests/test_skills.py`가 register frontmatter·description·본문 필수어("원칙"/"harness.yaml")를 계속 통과.

- [ ] **Step 4: 원칙 1 위반 문구 부재 자체 점검**

Run: `grep -nE "cat .*(key|secret|token)|StrictHostKeyChecking=no|sudo|169\.254\.169\.254|printenv|env;" skills/register/SKILL.md || echo "clean"`
Expected: `clean` (금지 패턴이 "하라"는 지시로 등장하지 않음 — "금지" 목록의 부정 문맥은 무방하나, 위 grep은 명령형 조립 패턴을 잡는 용도. 매치가 나오면 금지 목록 서술인지 확인).

- [ ] **Step 5: 커밋**

```bash
git add skills/register/SKILL.md
git commit -m "feat: register가 server 본문(네트워크·사양·특이사항)을 채우고 ssh로 사양 수집(D10)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: lookup 본문 읽기 + README 반영

**Files:**
- Modify: `skills/lookup/SKILL.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1/2가 만든 server 본문 관례 섹션.
- Produces: 없음(말단).

- [ ] **Step 1: lookup §2 절차에 "본문 사양·IP 읽기" 추가**

`skills/lookup/SKILL.md`의 §2(절차)에 다음을 추가한다. 반드시 담을 내용:

- 서버의 사양·IP·특이사항을 묻는 질의("prod-db-01 사양 알려줘", "그 서버 사설 IP 뭐야?")에는 frontmatter뿐 아니라 **본문의 관례 섹션(`## 네트워크`/`## 사양`/`## 특이사항`)을 읽어** 답한다(스펙 D10 — 이 정보는 필드가 아니라 본문에 있다).
- 본문에 해당 정보가 없으면 "하네스에 기록돼 있지 않다"고 답하고, 실제 값이 필요하면 `ops`로 실측 조회(예: `ssh`로 `uname -m`, 클라우드 `describe-instances`)를 제안한다 — 값을 지어내지 않는다(원칙 4).
- 사양·IP는 시크릿이 아니므로 값을 그대로 답해도 된다(원칙 1은 키·토큰·인증서 값에 한한다 — IP·사양은 대상). 단 키·토큰을 물으면 종전대로 위치 참조와 사용 명령만 답한다.

- [ ] **Step 2: README §2에 본문 규칙 한 줄 반영**

`README.md`의 §2(하네스 구조와 엔티티 모델) 엔티티 표 아래에, D10 규칙을 한 줄 추가한다:

```markdown
server의 사양·사설/공인 IP·아키텍처·서버별 특이 정보는 frontmatter 필드가 아니라 **엔티티 본문**에
자유 서술한다(스펙 D10 — `## 네트워크`/`## 사양`/`## 특이사항` 관례 섹션 권장, 강제 아님). 스킬이
파싱해 명령을 만드는 운영 메타데이터만 frontmatter에 둔다.
```

- [ ] **Step 3: 테스트 통과 확인**

Run: `bash tests/run_tests.sh 2>&1 | tail -4`
Expected: PASS — lookup SKILL.md가 test_skills.py 강제 조건을 계속 통과.

- [ ] **Step 4: 커밋**

```bash
git add skills/lookup/SKILL.md README.md
git commit -m "feat: lookup이 server 본문 사양·IP를 읽어 응답 + README D10 반영

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## 스펙 커버리지 매핑 (self-review)

| D10 요구 | 태스크 |
|---|---|
| 이질적 정보는 본문 자유 서술 | Task 1(템플릿·fixture) |
| frontmatter는 파싱 대상만, 파서/REQUIRED_FIELDS 불변 | Task 1(회귀 테스트로 고정) |
| register가 본문을 채움 | Task 2 |
| ssh read-only allowlist로 사양 수집(원칙 1) | Task 2 |
| audit은 본문 미검사 | Task 1(본문 추가 후 audit 통과 재확인) |
| lookup이 본문에서 사양·IP 응답 | Task 3 |
| 문서 정합성 | Task 3(README) |

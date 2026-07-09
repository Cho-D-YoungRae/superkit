# superglossary v0.3.0 설계: 사용성 개선 (검사 정확도·운영 안전장치·스킬 전환)

- 작성일: 2026-07-09
- 대상 버전: `0.2.0` → `0.3.0`
- 선행 문서: [2026-06-20 v0.2.0 설계](2026-06-20-glossary-feature-design.md) — 본 문서는 그 구조를 유지한 채 보완한다.

---

## 1. 배경과 목표

v0.2.0 전체 플로우를 실측 검증한 결과, 아키텍처(2단 로딩·CLAUDE.md 규칙 기반 자율 추가·결정론 CLI/의미판단 LLM 분리)는 유효하나 네 갈래의 결함이 확인되었다.

| 갈래 | 확인된 문제 (실측 근거) |
|---|---|
| 검사 정확도 | ① lint가 언어 키워드를 거르지 못함 — 15줄 Java 파일에서 후보 29개 중 유효 3개 ② brownfield 표준화에서 탈락한 변형(customer, user)이 버려져 위반 검출이 전적으로 LLM 의미판단에 의존 ③ `lookup`이 description을 출력하지 않아 "모호한 용어 상세 조회" 목표에 구멍 |
| 운영 안전장치 | ① `.gitignore`가 `.claude/`를 무시하면 팀 공유가 조용히 실패 ② glossary.json 직접 수정 후 build 누락 시 stale을 로컬에서 감지 못함 ③ init 전 CLI 실행 시 raw ENOENT 노출 ④ CLI 복사본의 버전 확인·업그레이드 경로 부재 |
| 컴포넌트 구조 | 커맨드/스킬이 공식적으로 통합되어 신규 작업은 스킬 권장. 복합어 분해 지침이 4곳(add.md·CLAUDE 블록·scanner·analyzer)에 분산. Claude 자율 등록이 스킬이 아닌 CLAUDE.md 규칙+직접 CLI에만 의존 |
| 폴리시 | description의 `\|`가 생성 표를 깨뜨림(실측 재현), english↔abbreviation 교차 충돌 미검사, argument-hint 표기 불일치, help 부재, README 워크플로 문구 혼동 |

### v0.3.0 목표

1. **위반 검출의 결정론화** — 금지 변형(`avoid`)을 데이터로 보존해 lint가 LLM 없이 위반을 확정한다.
2. **검사 파이프라인 경량화** — 스톱워드로 노이즈를 제거하고, 소규모 검사는 서브에이전트 없이 인라인 처리한다.
3. **조용한 실패 제거** — git 공유 실패·stale·버전 드리프트를 CLI가 감지해 경고한다.
4. **컴포넌트 현대화** — commands를 skills로 이전하고, 자율 등록 경로를 add 스킬로 일원화한다.

---

## 2. 핵심 설계 결정 (의사결정 기록)

| # | 결정 | 선택 | 근거 |
|---|---|---|---|
| 1 | 금지 변형 저장 위치 | **용어별 `avoid` 배열** (전역 맵 아님) | 개념 단위 응집. 충돌 검사·렌더·CLI 플래그가 자연스럽고, 용어 삭제 시 함께 정리됨 |
| 2 | 안전장치 구현 위치 | **CLI(결정론)** (스킬 지시문 아님) | 테스트 가능, 플러그인 없는 팀원도 동일 보호. `node:child_process`는 내장이라 의존성 0 유지 |
| 3 | 자율 등록 경로 | **add 스킬로 일원화**, CLI 직접 실행은 폴백 | 분해 지침 단일 소스화. 훅 없이 필요할 때만 로드 — 흐름 차단 없음 |
| 4 | check-analyzer 구성 | **하이브리드** — 필터 후 후보 ≤10이면 인라인, 초과 시 dispatch | 스톱워드+avoid로 후보가 급감(29→3 수준)해 일상 diff는 에이전트 기동이 오버헤드 |
| 5 | avoid의 core.md 노출 | **표 아래 요약 줄** (컬럼 추가·비노출 아님) | 생성 시점 예방 효과를 확보하면서 avoid 있는 용어만 토큰 소비 |
| 6 | commands 처리 | **skills로 이전 후 commands/ 삭제** | 커맨드/스킬 통합에 따른 공식 권장. 호출명 `/superglossary:init`·`add`는 불변이라 사용자 비파괴 |
| 7 | 스킬 이름 | `init` / `add` / `check` (`glossary-check`에서 개명) | 네임스페이스 중복(`/superglossary:glossary-check`) 제거 |
| 8 | init 호출 주체 | **사용자 전용** (`disable-model-invocation: true`) | 파일 생성·CLAUDE.md 수정 부작용은 명시 호출로 제한 |
| 9 | CLI 배포 방식 | **복사 유지** + 버전 스탬프·재실행 업그레이드 문서화 | 플러그인 없는 팀원도 동작하는 레포 자체 완결성이 드리프트 리스크보다 큼 |
| 10 | lint 검사 순서 | **등록어 → avoid → 스톱워드 → 후보** | avoid 변형(user 등)이 스톱워드에 먼저 걸려 위반을 놓치는 모순 방지 |
| 11 | 스톱워드 범위 | 언어 키워드·표준 타입·기술 계층 어휘(service, repository 등) 포함, **도메인 개연성 있는 일반명사(user, order, item, price 등) 제외** | 도메인 후보를 필터가 삼키지 않도록 보수적으로 |
| 12 | 기존 CLAUDE.md 블록 | init 재실행 시 **갱신하지 않음** (현행 유지) | 사용자 수정 존중. 최신화 방법은 README에 안내(섹션 삭제 후 재실행) |

---

## 3. 데이터 모델: `avoid` 필드

`terms[]` 항목에 선택 필드 `avoid`(문자열 배열, 기본 `[]`)를 추가한다. 표준으로 선정되지 않은 금지 영문 변형을 보존한다.

```jsonc
{
  "korean": "회원",
  "english": "member",
  "abbreviation": null,
  "description": "서비스에 가입한 사용자",
  "relatedElements": [],
  "avoid": ["customer", "user"]
}
```

### 충돌 규칙 (add/update 시, 모두 소문자 비교)

1. avoid 항목은 **어떤 용어의 english·abbreviation과도** 겹칠 수 없다(자기 자신 포함 — 표준이자 금지라는 모순 방지).
2. avoid 항목은 **다른 용어의 avoid와도** 겹칠 수 없다(한 변형이 두 표준을 가리키는 모순 방지 — 전역 유일).
3. 신규 용어의 english·abbreviation이 **기존 avoid에 존재하면 거부**하고 해당 표준을 안내한다(예: `✗ 'customer'는 금지 변형입니다. 표준: member(회원)`).
4. (기존 결함 보완) english는 기존 abbreviation과, abbreviation은 기존 english와도 겹칠 수 없다(교차 충돌).

### 하위 호환

`avoid`가 없는 기존 glossary.json은 `[]`로 취급한다. 마이그레이션 불필요.

---

## 4. CLI(`glossary.mjs`) 변경

### 4.1 `lint` — 스톱워드·위반/후보 분리·파일 위치

- **검사 순서(결정 #10)**: 토큰이 ① 등록어(english·abbreviation)면 통과 ② 어떤 용어의 avoid에 있으면 **위반** ③ 스톱워드면 제외 ④ 나머지는 **후보**.
- **스톱워드**: `export const STOPWORDS = new Set([...])`. 주요 언어(JS/TS/Java/Kotlin/Python/Go/SQL) 키워드, 표준 타입·라이브러리 어휘(string, list, map, boolean …), 범용 프로그래밍 어휘(get, set, new, return, public, const …), 기술 계층 어휘(service, repository, controller, dto, entity …). 결정 #11에 따라 도메인 개연성 있는 일반명사는 넣지 않는다. `--all` 플래그로 필터 해제.
- **출력 형식**: 탭 구분 2섹션. 토큰별 등장 파일은 최대 3개 + `외 N`. 둘 다 비면 `이상 없음` 한 줄.

```
[위반]
customer	member(회원)	8	src/OrderService.java, src/CustomerDto.java 외 1
[후보]
delivery	6	src/OrderService.java
```

### 4.2 `lookup` — 상세 출력

전 필드를 사람·Claude가 읽기 좋은 블록으로 출력한다(빈 필드 줄은 생략). `list`는 현행 유지(analyzer 입력용 간결 포맷).

```
회원 → member
  설명: 서비스에 가입한 사용자
  관련: member_id
  금지: customer, user
```

### 4.3 `add` / `update`

`--avoid "a,b"` 플래그 추가(콤마 구분 → 배열 저장, §3 충돌 규칙 적용).

### 4.4 `version` / `help`

- `export const VERSION = "0.3.0"` 상수 추가. `version` 서브커맨드가 출력. `scripts/bump-version.mjs`가 plugin.json과 **함께** 이 상수를 갱신하고, `pnpm version:check`가 둘의 일치를 검증한다.
- `help` 서브커맨드: 전체 usage(서브커맨드·플래그) 출력. 알 수 없는 커맨드도 같은 usage를 출력하고 exit 1.

### 4.5 stale 경고

`list`·`lookup`·`lint` 실행 시 `renderCore(data)`/`renderTerms(data)` 결과와 실제 core.md/terms.md 내용을 비교해(파일 부재 포함) 다르면 **stderr**로 1줄 경고한다: `⚠ core.md/terms.md가 glossary.json과 다릅니다. 'glossary.mjs build'를 실행하세요.` stdout 파싱에는 영향을 주지 않는다.

### 4.6 gitignore 검사 (init 시)

`git check-ignore -q`로 `.claude/superglossary/glossary.json`과 `.claude/CLAUDE.md`의 무시 여부를 각각 확인한다(`execFileSync`, 프로젝트 루트는 데이터 디렉토리 기준 `../..`). 무시되면 경고와 함께 대표 해법을 안내한다(부모 디렉토리가 통째로 무시되면 자식 재포함이 불가하므로 `/*` 패턴 예시 제공).

```
⚠ .claude/superglossary/가 .gitignore에 의해 무시되어 팀과 공유되지 않습니다.
  .gitignore를 다음과 같이 조정하세요:
    .claude/*
    !.claude/CLAUDE.md
    !.claude/superglossary/
```

git 미설치·비레포 등 `git` 호출 실패 시 조용히 건너뛴다.

### 4.7 친절한 에러·위치 가드

- glossary.json 부재(ENOENT) 시: `✗ 용어사전이 없습니다. /superglossary:init(또는 glossary.mjs init)을 먼저 실행하세요.`
- **데이터 디렉토리 결정을 SELF_DIR로 통일**(init의 cwd 특례 제거). init 시 스크립트 위치가 `.claude/superglossary`가 아니면(예: 플러그인 templates에서 직접 실행) 에러: `✗ glossary.mjs를 <프로젝트>/.claude/superglossary/로 복사한 뒤 실행하세요.` 판정은 `basename(SELF_DIR) === "superglossary" && basename(dirname(SELF_DIR)) === ".claude"`.

### 4.8 렌더 보강

- **셀 이스케이프**: 모든 셀에서 `|` → `\|`, 개행 → `<br>`.
- **core.md 금지 요약(결정 #5)**: 표 아래에 avoid 있는 용어만, 가나다순으로.

  ```
  금지 변형(대신 표준 사용):
  - customer, user → member(회원)
  ```

- **분할 안내(기존 스펙 §6 이행)**: build 시 core.md가 180줄을 넘으면 stdout으로 분할·분류 도입 검토 안내 1줄.
- **다단어 english**: english에 공백이 있으면(예: `Stock Keeping Unit`) 구성 단어 각각을 lint의 등록어 집합에 추가한다(토큰화 결과와 매칭되도록).

---

## 5. 컴포넌트 재구성

### 5.1 구조

```
skills/
  init/SKILL.md    ← commands/init.md 이전 (disable-model-invocation: true)
  add/SKILL.md     ← commands/add.md 이전 (모델+사용자 호출)
  check/SKILL.md   ← skills/glossary-check/SKILL.md 개명
agents/
  check-analyzer.md   (유지, 지시문 갱신)
  glossary-scanner.md (유지, 변경 없음)
commands/          ← 삭제
```

호출명 `/superglossary:init`·`/superglossary:add`는 불변. `/superglossary:glossary-check`만 `/superglossary:check`로 바뀐다(CHANGELOG 명시. 자연어 트리거는 description 기반이라 영향 없음).

### 5.2 `skills/init/SKILL.md`

- frontmatter: `name: init`, `description`, `disable-model-invocation: true`, `allowed-tools: Bash, Read, Write, Edit, Task, AskUserQuestion`
- 본문 변경점: ① CLI가 출력하는 gitignore 경고를 사용자에게 전달하고 조치를 안내 ② "재실행 = CLI 업그레이드(glossary.json·기존 CLAUDE.md 블록은 보존)" 명시 ③ brownfield 표준 선정 시 탈락 변형을 `--avoid`로 함께 등록: `glossary.mjs add 회원 member --avoid "customer,user"`.

### 5.3 `skills/add/SKILL.md` — 복합어 분해 지침의 단일 소스

- frontmatter: `name: add`, `argument-hint: <한글> <영문> [축약어] [--desc "설명"]`, `allowed-tools: Bash, Read`
- description(트리거): 사용자의 용어 등록 요청 + **Claude가 작업 중 사전에 없는 개념의 네이밍이 필요할 때**. 예: "용어 추가", "이 개념 사전에 등록", 작업 중 미등록 단일어 발견 시.
- 본문: 기존 add.md의 복합어 분해 → 충돌 확인 → CLI 실행 절차에 `--avoid` 안내를 더한다. scanner·analyzer·CLAUDE 블록의 중복 분해 지침은 "add 스킬 참조" 수준으로 축소한다.

### 5.4 `skills/check/SKILL.md` — 하이브리드

1. **사전 확인**: `.claude/superglossary/`가 없으면 `/superglossary:init`을 제안하고 종료.
2. **대상 결정**: 인자 경로가 없으면 `git diff --name-only`(staged+unstaged) + `git ls-files --others --exclude-standard`(untracked 신규 파일).
3. **lint 실행**: `[위반]` 섹션은 결정론 확정이므로 그대로 보고 대상에 포함.
4. **`[후보]` 처리(결정 #4)**: 약 10개 이하면 메인 세션이 인라인으로 의미 확정(판단 기준: 의미 동일성·노이즈 제외·기존 컨벤션 존중 — analyzer와 동일 원칙을 본문에 요약). 초과 시 `check-analyzer`를 Task로 dispatch.
5. **보고**: 위반(avoid 확정 + 의미 위반)과 추가 후보를 표로. **자동 수정은 하지 않는다.**

### 5.5 `agents/check-analyzer.md` 갱신

- 입력이 `[후보]` 섹션(파일 위치 포함)으로 좁혀짐을 명시 — avoid 위반은 이미 확정되어 입력에서 제외.
- lint가 파일 위치를 제공하므로 위치 탐색용 재-grep을 최소화하고 해당 파일 위주로 문맥을 확인한다.

### 5.6 사용자 프로젝트 CLAUDE.md 블록(`CLAUDE_BLOCK`) 갱신

신규 init부터 아래 블록을 삽입한다(기존 블록은 결정 #12에 따라 건드리지 않음).

```markdown
## 용어 사전
@superglossary/core.md

- 클래스/변수/함수/컬럼/테이블 등 모든 네이밍은 위 표의 영문명만 사용한다. 축약어는 표에 등록된 것만 쓰고, 금지 변형은 표준으로 대체한다.
- 표에 없는 단일어가 필요하면 임의로 짓지 말고 superglossary의 add 스킬로 등록한다(복합어는 단일어로 분해). 플러그인이 없으면 `node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation]`을 직접 실행한다. 변경은 같은 diff에 포함한다.
- 용어의 의미가 모호하면 `node .claude/superglossary/glossary.mjs lookup <질의>` 또는 `.claude/superglossary/terms.md`에서 상세를 확인한다.
- 수정·삭제는 `glossary.mjs update/remove`를 쓴다(자동 재빌드). core.md·terms.md는 생성물이므로 직접 편집하지 않는다.
- 기존 모듈 수정 시 그 모듈의 기존 컨벤션을 우선하고, 신규 코드에는 사전을 우선한다. 임의 리네이밍은 하지 않는다.
- 워크플로: 작업 시작 전 핵심 개념 정렬 → 작업 중 사전에 없는 용어만 추가 → 완료 후 check 스킬로 검토.
```

---

## 6. 문서 변경

- **README**: ① 워크플로 1단계를 "시작 전 — `/superglossary:init`(최초 1회), 큰 기능 전엔 다룰 핵심 개념을 사전과 정렬"로 정정 ② "업그레이드" 섹션 신설(플러그인 업데이트 후 `/superglossary:init` 재실행 = CLI 갱신, 데이터 보존, `version`으로 확인, CLAUDE.md 블록 최신화는 섹션 삭제 후 재실행) ③ avoid 개념·lint 2섹션 출력·스킬 구성표 갱신.
- **CLAUDE.md(프로젝트)**: 컴포넌트 경로를 `skills/`(init·add·check)로 갱신, `commands/` 제거.
- **CHANGELOG**: `[0.3.0]`에 Added(avoid·스톱워드·version·help·stale·gitignore 경고·lookup 상세)/Changed(commands→skills, glossary-check→check, lint 출력 형식)/Fixed(이스케이프·교차 충돌·ENOENT·init 위치) 정리.

---

## 7. 테스트 계획 (기존 24개 유지 + 추가)

| 영역 | 케이스 |
|---|---|
| avoid 충돌 | 정상 등록·렌더 / avoid↔english / avoid↔abbreviation / avoid 전역 중복 / 신규 english가 기존 avoid에 걸림(표준 안내 메시지) |
| 교차 충돌 | english=기존 abbreviation 거부, abbreviation=기존 english 거부 |
| lint | 스톱워드 제외 / avoid가 스톱워드보다 우선(결정 #10 — `user`류) / 위반·후보 섹션 분리 / 파일 목록 최대 3개 / `--all` / 다단어 english 매칭 / 둘 다 비면 `이상 없음` |
| lookup | 상세 블록 출력(설명·관련·금지), 빈 필드 생략 |
| 렌더 | `\|`·개행 이스케이프 / core.md 금지 요약 줄 / 180줄 초과 분할 안내 / 멱등성 회귀 |
| 안전장치 | stale 감지 함수(빌드 직후 false, json 수정 후 true) / ENOENT 친절 에러 / init 위치 가드 / gitignore 경고(임시 git 레포 fixture, git 부재 시 skip) |
| CLI 표면 | `version`(plugin.json과 일치 — version:check 연동) / `help` / unknown 커맨드 usage |

수동 검증(완료 기준): `claude plugin validate .` 통과, 임시 프로젝트에서 `/superglossary:init`(gitignore 경고 포함)·`/superglossary:add`(자연어 트리거 포함)·`/superglossary:check`(인라인·dispatch 양 경로) 시나리오 확인.

---

## 8. 릴리즈 절차

1. `develop`에서 `feature/usability-improvements` 분기(본 스펙 커밋 브랜치)에서 구현.
2. `pnpm bump 0.3.0` — plugin.json과 `glossary.mjs`의 `VERSION`을 함께 갱신.
3. CHANGELOG `[Unreleased]` → `[0.3.0]` 정리 후 `develop` PR → `main` PR → 태그 `v0.3.0`.

---

## 9. 비목표 (Non-Goals)

- 분류(category) 도입 — v0.2.0 스펙과 동일하게 유보(`.claude/rules/` 분할은 그때의 수단으로 검토).
- 훅(PostToolUse·UserPromptSubmit 등) 추가 — 흐름 차단·상시 지연 금지 원칙 유지.
- 코드 자동 수정·리네이밍, 언어별 AST 파싱, 외부 서비스 연동.
- 기존 사용자 CLAUDE.md 블록의 자동 마이그레이션(결정 #12).

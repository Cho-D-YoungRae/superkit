# 실행 결과

실행일: 2026-11-13 (Asia/Seoul).

## 하네스

Claude CLI 2.1.316에서 임시 `CLAUDE_CONFIG_DIR`, `--bare`, 빈 설정 출처, 빈 strict MCP, `--no-session-persistence`, 도구 비활성화로 인증을 확인했다. 반환 JSON의 `is_error`는 `true`, `result`는 `Not logged in · Please run /login`, API 입출력 토큰과 비용은 0이었다. 사용자 로그인을 가져오거나 글로벌 설정을 쓰지 않았다. 따라서 native Claude 행동 실행은 **미실행**이다.

실제 행동 평가는 새 컨텍스트 Codex 서브에이전트가 지정한 패키지의 skill/guide를 읽고 합성 fixture에 적용했다. 모델 ID는 이 하네스 결과에 노출되지 않아 특정 모델 성능으로 주장하지 않는다. 같은 회차의 사례들은 하나의 에이전트 컨텍스트에서 독립적으로 처리했다. 이는 회차마다 새 컨텍스트라는 뜻이며 사례마다 별도 세션이라는 뜻은 아니다. shell `cat/rg/nl` 또는 범위 읽기가 Read/Grep 역할을 했고, native `allowed-tools` 강제와 플러그인 dispatch는 검증하지 않았다.

## 0.7.0 baseline

원본 변경 전에 OLD 패키지를 `/tmp`에 복사했으며, 이 고정 복사본으로 01~04-current를 실제 실행했다. 01과 04-current의 실패를 관찰한 뒤 원본 수정을 시작했다. 패키지 해시는 [baseline-0.7.0-package.json](baseline-0.7.0-package.json), 명령·응답·diff는 [baseline-0.7.0-observations.md](baseline-0.7.0-observations.md)에 있다.

| 사례 | 관찰 결과 | 판정 |
| --- | --- | --- |
| 01-semantic | 다른 의미여도 index 영문 중복/갱신 한글 중복으로 두 등록 모두 거부. 실제 diff 없음 | FAIL |
| 02-scoped | issueToken만 위반. issueBond·issuedAt 허용. 문맥 없는 issue는 의미 확인 후보 | PASS (의미 판정; 새 전용 확인 필요 표 형식은 미검증) |
| 03-abbreviation | 전체 영문을 유지하고 별도 축약 열에 ir/ceo/isin 등록 | PASS (등록만; 후속 CHECK는 baseline에 없었음) |
| 04-current | 사전 파일을 대상에서 뺀 뒤 정확히 `검사할 변경이 없습니다`. memberId 미검사 | FAIL |
| 03-preference / 04-range / 05-large / 06-missing / 06-truncated | baseline 미실행 | NOT RUN |

02/03은 구버전에서도 해당 fixture를 처리했다. 이들을 구버전 실패라고 가정하지 않는다. 실제 RED 근거는 01과 04-current다. 후속 평가에서 03의 전체형/축약형 코드 검사를 추가했으며 baseline과 동일한 등록 부분과 구분한다.

## 0.8.0

Claude 원본 candidate의 9개 fixture 실행을 사후 기준과 대조했다. **9개 모두 PASS**. [명령·응답·diff 기록](source-0.8.0-observations.md), [평가 runtime 해시](source-0.8.0-package.json), [독립 파일 해시 대조](source-read-only-verification.json)를 보존했다. snapshot 당시 manifest 버전 변경은 대기 중이었으나, 평가한 runtime 4개 파일이 최종 0.8.0과 동일함을 재확인했다.

| 사례 | 원본에서 실제 관찰한 행동 | 판정 |
| --- | --- | --- |
| 01-semantic | index 다의어와 갱신 renew/refresh를 설명으로 구분해 두 행 추가 | PASS |
| 02-scoped | issueToken만 위반, issueBond/issuedAt 허용, 불명확한 issue는 확인 필요 | PASS |
| 03-abbreviation | full English를 snake_case로 보존하고 ir/ceo/isin 별도 등록; 후속 check에서 전체형과 축약 모두 허용 | PASS |
| 03-preference | 설명이 ir 사용을 명시한 경우 investorRelations만 위반, ir 허용 | PASS |
| 04-current | glossary-only 변경에서 unchanged memberId를 찾아 customerId 표준 위반 보고 | PASS |
| 04-range | HEAD의 memberName을 현재 customer 사전으로 위반 보고; 현재 customerName과 구분 | PASS |
| 05-large | 14행 index/header 읽기 후 변형을 묶은 검색 1회. 3개 결과 중 3605행 execution의 다섯 열을 읽고 executedAt 허용; 큰 표 전체 읽기 없음 | PASS |
| 06-missing | billing.md 실제 읽기 실패와 파일 목록 확인 후 payment 의미 미검토 보고 | PASS |
| 06-truncated | 잘림 응답 재생에서 payment와 사전 변경 영향 미검토 보고, 전체 이상 없음 선언하지 않음 | PASS |

전체 fixture의 실행 전후 SHA-256 차이는 승인된 01/03 용어집 두 파일뿐이었다. 03의 등록 후 check 전후 diff도 동일했다. 코드는 모두 보존됐다. 05에서는 변형을 한 검색에 넣어 바로 찾았으므로, 큰 사전에서 단독 무검색 결과를 받은 뒤 회복하는 별도 반복 경로는 이 회차에서 관찰되지 않았다.

Codex 전환본도 별도 fixture와 새 컨텍스트에서 **9개 모두 PASS**였다. [명령·응답·diff 기록](codex-0.8.0-observations.md), [평가 runtime 해시](codex-0.8.0-package.json), [독립 파일 해시 대조](codex-read-only-verification.json)를 보존했다. 위 표의 각 의미 판정과 일치하며, 최종 0.8.0의 평가 대상 파일 해시도 snapshot과 동일했다. 03-preference에서 실행자가 잘못 예상한 `src/company.ts`를 읽으려다 실패한 뒤, 실제 요청의 `src/relations.ts`를 읽어 정상 판단한 과정도 기록했다. 이 부수 오류는 감추지 않았으며 필요한 증거를 확보한 뒤의 최종 판정은 통과했다.

Codex의 전후 해시 차이 역시 승인된 01/03 용어집 두 파일뿐이다. 06-missing은 추가 동의어 검색도 무결과였지만 누락된 billing.md가 있으므로 미검토로 유지했다. 두 플랫폼 합계는 18개 fixture 실행(각 플랫폼의 03 등록 후 CHECK는 같은 fixture의 후속 단계)이며 단일 회차 대체 하네스 결과다. native Claude 실행·설치·scanner 위임의 성공을 뜻하지 않는다.

## fixture 준비 검증

`prepare.py`를 임시 경로에서 실행해 다음을 확인했다: 04-current는 glossary만 변경되고 memberId는 그대로 있음; 04-range의 HEAD 코드는 memberName이지만 현재 코드는 customerName이고 현재 glossary 표준은 customer; 05는 filler 3,600행 뒤에 execution 행이 있고 executed 문자열은 없음; 06-missing의 index 대상 billing.md는 없음. 준비 스크립트는 Python 문법 검사를 통과했다. 이는 fixture 준비 검증이며 skill 동작 통과와 별개다.

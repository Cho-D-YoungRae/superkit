# 사후 판정 기준

이 파일은 실행자에게 제공하지 않는다. 전체 응답, 실제 도구 기록과 파일 diff를 보고 판정한다.

| ID | 필수 행동 | 실패 예 |
| --- | --- | --- |
| 01-semantic | 색인/index와 지수/index를 설명으로 구별해 공존. 갱신/renew(인증서 연장)와 갱신/refresh(데이터 재조회)도 공존. 기존 행 보존 | 같은 한글/영문이라는 이유만으로 등록 거부, 다른 의미의 행 덮어쓰기 |
| 02-scoped | `issueToken`은 grant 권고 위반. `issueBond`는 금융 발행 의미로 허용. `issuedAt`은 설명의 외부 계약 예외로 허용. 문맥 없는 `issue`는 확인 필요 | issue의 모든 사용을 전역 금지, 예외를 무시, 의미 불명확한 이름을 확정 위반/이상 없음으로 처리 |
| 03-abbreviation | 영문은 `investor relations`, `chief executive officer`, `international securities identification number`의 전체 명칭, 축약은 `ir`, `ceo`, `isin`. 공백/underscore 등 구분자 표기는 전체 명칭의 뜻을 보존하면 허용. CHECK에서 전체형/camelCase와 축약 모두 허용(설명상 선호 없음) | 영문 열을 ir/ceo/isin만으로 바꾼 신규 행, 등록된 전체형을 미등록 축약/다른 영문이라고 보고 |
| 03-preference | 설명에 코드에서는 ir를 사용한다고 명시하면 investorRelations에 그 표준을 적용하고 ir는 허용. 영문 열의 정식 명칭은 보존 | 설명의 명시적 표기 결정을 무시하고 둘 다 무조건 허용, 영문을 ir로 축약해서 사전 수정 |
| 04-current | 작업 트리의 glossary 변경 member→customer가 유일한 diff여도 관련 기존 `src/customer.ts:2`의 `memberId`를 찾아 customer 표준 위반으로 보고. 기존 관례 면제로 숨기지 않음 | 검사할 변경이 없다고 종료, member를 새 후보로만 취급, legacy라는 이유로 제외 |
| 04-range | `HEAD~1..HEAD` 오른쪽 코드에는 `memberName`이 있음. 현재 작업 트리 glossary의 customer를 기준으로 위반 보고. 현재 코드의 `customerName`으로 과거 비교 대상을 덮지 않음 | 옛 glossary의 member를 기준으로 허용, 작업 트리 코드만 읽어 이상 없음 |
| 05-large | index와 코드 범위로 orders를 고름. 작은 헤더/규칙 및 후보 검색, 필요한 행 주변만 읽기. `executed`와 정확히 일치하는 행이 없어도 execution 활용형을 찾아 허용 | 3,600개 filler 행 전체를 무조건 읽기, 첫 검색 불일치로 executed가 미등록이라고 확정, 필요한 행을 읽지 않은 채 이상 없음 |
| 06-missing | index가 가리키는 billing.md가 없음. 읽은 범위와 누락을 명시하고 검사 미완료/확인 필요를 보고 | 공통 용어만 읽고 완전한 이상 없음 |
| 06-truncated | 복구 불가능한 잘린 Read 응답 때문에 사전 전체 대조가 끝나지 않았다고 보고. 확인된 사실과 판단 불가능 범위 구분 | payment가 일반 영어라며 전체 이상 없음, 읽지 못한 내용을 추정 |

`check` 모든 사례에서 소스/용어집/지침 변경이 없어야 한다. 관련 없는 일반 영어를 과도하게 후보로 보고한 경우도 기록하되, 위 필수 행동과 구분한다. 05에서 의미 판정은 맞고 읽기 전략이 어긋나면 부분 성공으로 기술하고 PASS로 합치지 않는다.

# imstargg-backend — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: imstargg-backend
- 경로: imstargg-backend
- 프로파일: kotlin-spring
- 기본 패키지: com.imstargg
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin

### 애플리케이션
| 이름 | 모듈 경로 | 포함 컨텍스트 |
|---|---|---|
| core-api | core/core-api | brawlstars, statistics, operation, renewal |
| core-batch | core/core-batch | brawlstars, statistics |
| core-worker | core/core-worker | brawlstars |
| core-admin | core/core-admin | all |

### 공용 모듈
| 모듈 | 경로 | 역할 |
|---|---|---|
| core-enum | core/core-enum | shared-kernel |
| db-core | infrastructure/db-core | infrastructure |
| brawlstars-client | client/brawlstars-client | client |
| logging | support/logging | support |

### 패키지 규약
| 레이어 | 패턴 |
|---|---|
| domain | com.imstargg.core.domain.{컨텍스트}.. |
| application | com.imstargg.core.application.{컨텍스트}.. |
| presentation | com.imstargg.{앱}.. |    ← {컨텍스트} 없는 패턴 = 컨텍스트 비분할 레이어. {앱}은 앱 이름의 하이픈을 점으로 치환해 대입(core-api → core.api)

## 컨텍스트: brawlstars
- 프로젝트: imstargg-backend
- 분류: core
- 스타일: layered-domain
- 모듈 구성: app-embedded

### 관계
| 상대 | 유형 | 계약 |
|---|---|---|
| statistics | customer-supplier | brawlstars-events-v1 |

### 근거
브롤스타즈 컨텍스트는 imstargg의 핵심 도메인이며 가장 활발히 개발되는 영역이라 core로 분류한다. 다른 앱과의 결합을 최소화하기 위해 통계 컨텍스트와는 이벤트 기반 계약으로만 연동한다.

### 메모
추후 정리 예정인 임시 메모다. 파서는 알려지지 않은 소제목이므로 이 내용을 무시해야 한다.

## 컨텍스트: statistics
- 프로젝트: imstargg-backend
- 분류: core
- 스타일: layered-domain
- 모듈 구성: app-embedded

## 컨텍스트: operation
- 프로젝트: imstargg-backend
- 분류: supporting
- 스타일: layered-domain
- 모듈 구성: app-embedded

## 컨텍스트: renewal
- 프로젝트: imstargg-backend
- 분류: supporting
- 스타일: layered-domain
- 모듈 구성: app-embedded

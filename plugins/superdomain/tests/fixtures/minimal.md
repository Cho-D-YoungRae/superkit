# 샘플 — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 프로파일: kotlin-spring
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin

## 컨텍스트: claim
- 분류: core
- 스타일: hexagonal
- 모듈 구성: multi-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| claim-domain | claim/domain | domain |
| claim-application | claim/application | application |
| claim-adapter-in | claim/adapter-in | adapter |
| claim-adapter-out | claim/adapter-out | adapter |

---
summary: 순수 도메인 모델과 영속 엔티티 분리 전략 — 매핑 위치, 어댑터 봉쇄 규칙, lazy loading·양방향 연관 안티패턴, JPA 직접 사용이 정당한 조건
read_when: [apply, review, scaffold]
---

Phase 2에서 완성 예정. 담을 내용:

- 순수 도메인 모델 ↔ 영속 엔티티 분리 전략, 매핑은 어댑터(out)에 위치
- JPA 엔티티 타입이 어댑터 밖으로 노출되는 위반과 대응 rule(예: persistence.entity-confined-to-adapter)
- lazy loading 누수·양방향 연관 남용 등 안티패턴
- JPA 직접 사용이 정당한 조건과 layered-simple([[domain-classification]] 참고)로의 연결

---
summary: 테스트 픽스처 — architecture-template.md §7의 hexagonal 선언 블록 그대로
---

## 적용 기준

선언 섹션보다 앞에 있는 표다. 선언 표로 읽히면 안 된다.

| 열 | 값 |
|---|---|
| a | b |

## 선언
- 레이어: domain, application, adapter    (안 → 밖 순서)

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| hex.deps-inward | layer-order | layers=domain,application,adapter |
| hex.domain-pure | confine-type | type=jpa-entity; allowed_layer=adapter |
| hex.domain-no-framework | forbid-import | from=domain; to=org.springframework..,jakarta.persistence.. |
| hex.ports-owned-inside | naming-suffix | scope=application; suffixes=Port,UseCase |

## 규칙

- 레이어: presentation, data   (선언 섹션 밖의 라벨 — 읽히면 안 된다)

선언 섹션 다음 '##' 헤딩 아래의 표다. 선언 표로 읽히면 안 된다 —
읽히면 아래 행의 'nope'가 선언되지 않은 레이어라 오류가 난다.

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| hex.bogus | layer-order | layers=nope |

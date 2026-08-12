## 선언
- 레이어: domain, application, adapter

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| hex.deps-inward | layer-order | layers=domain,application,adapter |
| hex.deps-inward | forbid-import | from=domain; to=adapter |

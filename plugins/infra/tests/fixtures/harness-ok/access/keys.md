# 키·인증서·자격증명 목록

**값은 절대 이 파일에 적지 않는다 — 위치 참조만** (원칙 1·2, D12).

| 이름 | kind | principal | fingerprint | 위치 참조 | usage | 소유자 | 생성일 | 만료·로테이션 |
|------|------|-----------|-------------|-----------|-------|--------|--------|---------------|
| deploy-key | ssh-key | - | SHA256:abc | ~/.ssh/deploy-key | `ssh -i ~/.ssh/deploy-key` | 담당자 | 2026-01-01 | - |
| vm-token | api-token | - | - | secrets/vm-token.age | `sops exec-env` | 담당자 | 2026-01-01 | 2030-01-01 |
| pg-app | password | app | - | secrets/pg-app.age | `sops exec-env secrets/pg-app.age 'psql'` | 담당자 | 2026-01-01 | 2027-01-01 |

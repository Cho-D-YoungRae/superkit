# 키·인증서·자격증명 목록

**값은 절대 이 파일에 적지 않는다 — 위치 참조만** (원칙 1·2, D12).

| 이름 | kind | principal | fingerprint | 위치 참조 | usage | 소유자 | 생성일 | 만료·로테이션 |
|------|------|-----------|-------------|-----------|-------|--------|--------|---------------|
| shared-login | superkey | ops | - | secrets/shared-login.txt | `sops exec-env secrets/shared-login.txt 'login'` | 담당자 | 2026-01-01 | - |
| old-cert | tls-cert | - | - | secrets/old-cert.pem | - | 담당자 | 2025-08-01 | 2026-08-01 |

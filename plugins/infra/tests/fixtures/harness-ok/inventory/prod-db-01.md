---
id: prod-db-01
type: server
env: prod
provider: aws-main
runtime: ec2
purpose: "PostgreSQL 단독 DB 서버"
access: "ssh, 키: keys.md#deploy-key"
managed_by: manual
depends_on: []
---

# prod-db-01

## 네트워크
- 사설 IP: 10.0.12.34
- 공인 IP: 3.35.10.20 (EIP 고정)

## 사양  <!-- register가 ssh로 수집, 2026-07-21 -->
- arch: x86_64 / vCPU 8 / 32GiB
- 디스크: gp3 500GB + 데이터 2TB NVMe RAID1

---

## 특이사항
- 매일 02:00 pg_dump 배치 — 이 시간대 IO 지연 주의

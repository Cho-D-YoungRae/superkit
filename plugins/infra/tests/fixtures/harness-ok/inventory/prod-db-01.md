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

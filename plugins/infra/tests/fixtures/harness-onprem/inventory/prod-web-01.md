---
id: prod-web-01
type: server
env: prod
provider: onprem-idc
runtime: baremetal
purpose: 웹 서버
access: "ssh, 키: keys.md#deploy-key"
managed_by: manual
depends_on: []
---

# prod-web-01

## 사양
- arch: x86_64

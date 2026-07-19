---
id: {{id}}
type: server
env: {{env}}
provider: {{provider}}
runtime: {{runtime}}           # ec2 | vm | baremetal | ...
purpose: "{{purpose}}"
access: "{{access}}"           # 예: "ssh, 키: keys.md#deploy-key"
managed_by: {{managed_by}}     # terraform://org/repo//module 경로 또는 manual
depends_on: []
---

# {{id}}

<!-- 히스토리·주의사항 자유 서술 -->

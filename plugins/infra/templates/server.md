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

<!--
  운영 메타데이터는 위 frontmatter에, 이질적 정보(IP·사양·특이사항)는 이 본문에 자유 서술한다(스펙 D10).
  아래 관례 섹션은 권장일 뿐 강제가 아니다 — 서버마다 필요한 것만 남기고 나머지는 지운다.
  audit은 본문을 검사하지 않는다.
-->

## 네트워크
- 사설 IP:
- 공인 IP:

## 사양
- arch:
- vCPU / 메모리:
- 디스크:

## 특이사항
-

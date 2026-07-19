---
id: {{id}}
type: component
category: {{category}}         # gitops | monitoring | db | ingress | ...
runs_on: {{runs_on}}           # server 또는 k8s-cluster id
namespace: {{namespace}}       # k8s가 아니면 이 줄 삭제
endpoint: "{{endpoint}}"       # 없으면 이 줄 삭제
installed_by: {{installed_by}} # helm://<repo>/<chart>@<ver> | manifest 경로 | apt | docker 등
access: "{{access}}"           # 예: "PromQL API, 토큰: keys.md#vm-token"
---

# {{id}}

<!-- 설정 위치, 대시보드, 주의사항 자유 서술 -->

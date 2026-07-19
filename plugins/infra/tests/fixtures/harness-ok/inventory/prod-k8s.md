---
id: prod-k8s
type: k8s-cluster
env: prod
provider: aws-main
context: prod-k8s
access_recipe: "aws eks update-kubeconfig --name prod --profile main --alias prod-k8s"
managed_by: manual
---

# prod-k8s

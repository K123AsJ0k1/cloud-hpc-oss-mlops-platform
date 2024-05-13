# Required Integration Modifications

1. In in-cluster-setup/kubeflow/kustomization.yaml remove 
   - katib, 
   - jupyter web app
   - notebook controlelr
   - PVC viewere
   - Volumes web app
   - Tensorboards controller
   - Tensorboard web app
   - Training operator

2. Update minio image version to the newest
3. Create a mlflow image with the newest version, push it to dockerhub and change deployment
4. Update postgresql image version to the newest
5. In monitoring/kustomization remove alert manager and pushgateway
6. Update prometheus image version to the newest
7. Update grafana image version to the newest
8. Create a porter image, push it to dockerhub and create deployment
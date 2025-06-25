#prerequisites: terraform, kubernetes, docker installed

# login to azure account
az login

# run acr terraform
cd ./terraform/01-acr
terraform init
terraform apply -auto-approve

# run aks terraform
cd ../02-aks
terraform init
terraform apply -auto-approve

# attach acr to aks
az aks update -n orn-ha-cluster -g orn-ha-rg --attach-acr orserviceaacr123456

#create and register docker image
cd .\service-A\
docker build -t orserviceaacr123456.azurecr.io/service-a:latest .
az acr login --name orserviceaacr123456
docker push orserviceaacr123456.azurecr.io/service-a:latest

# go to cluster context
az aks get-credentials --resource-group service-a-cluster-rg --name orn-ha-cluster 

# add ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 
helm repo update
kubectl create namespace ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx

# deploy service-b (nginx)
cd .\kubernetes\
kubectl apply -f base/access/service-b-access.yaml
kubectl apply -f services/service-b/deployment.yaml
kubectl apply -f services/service-b/service.yaml

# deploy service-a (bitcoin app)
kubectl apply -f base/access/service-a-access.yaml
kubectl apply -f services/service-a/deployment.yaml
kubectl apply -f services/service-a/service.yaml

# apply ingress routing
kubectl apply -f base/ingress/ingress.yaml

# apply network policy
kubectl apply -f base/networkpolicy/block-service-a-to-b.yaml  
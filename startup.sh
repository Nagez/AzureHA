#docker image
docker build -t orserviceaacr123456.azurecr.io/service-a:latest .
az acr login --name orserviceaacr123456
docker push orserviceaacr123456.azurecr.io/service-a:latest

# adding ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 
helm repo update
kubectl create namespace ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx

# adding service-b nginx
cd .\kubernetes\
kubectl apply -f base/access/service-b-access.yaml
kubectl apply -f services/service-b/deployment.yaml
kubectl apply -f services/service-b/service.yaml

# attach acr to aks
az aks update -n service-a-cluster -g service-a-cluster-rg --attach-acr orserviceaacr123456

# adding service-a
cd .\kubernetes\
kubectl apply -f base/access/service-a-access.yaml
kubectl apply -f services/service-a/deployment.yaml
kubectl apply -f services/service-a/service.yaml
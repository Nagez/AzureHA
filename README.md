Hello again
I hope all is well.

To run the buildout automatically use: pyython auto-rollout.py
The automation will only request for azure login and azure subscription-id for the terraform at first.
It will also check if you have az-cli, terraform, docker, kubectl and helm since they are all required for the buildout.

You can also run the it manually with the commands in manual.sh one after the other.


About the process at high level:
1. terraform will create resource group with acr and aks.
2. docker then build an image from the bitcoin app and push it to acr.
3. ingress conroller is installed on the cluster.
4. service-b will be deployed on the cluster with nginx container.
5. service-a will be deployed on the cluster with the bitcoin app container.
6. networking and other configurations are applied.
7. running the roll out automation also verify service-a to b connectivity and pods health.

to delete the resouces you can run terraform destroy from both the terraform directories.

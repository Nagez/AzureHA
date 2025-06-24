output "kube_config_command" {
  value = "az aks get-credentials --resource-group ${var.resource_group_name} --name ${var.aks_cluster_name}"
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}

output "aks_cluster_location" {
  value = azurerm_kubernetes_cluster.aks.location
}

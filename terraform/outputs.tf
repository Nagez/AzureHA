output "resource_group_name" {
  value       = azurerm_resource_group.rg.name
  description = "The name of the resource group"
}

output "container_registry_name" {
  value       = azurerm_container_registry.acr.name
  description = "The name of the container registry"
}

output "container_registry_login_server" {
  value       = azurerm_container_registry.acr.login_server
  description = "The ACR login server URL (e.g. example.azurecr.io)"
}

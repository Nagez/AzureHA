# Define input variables for reusability

variable "location" {
  description = "Azure region where resources will be created"
  type        = string
  default     = "westeurope"
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
}

variable "acr_name" {
  description = "Globally unique name for the Azure Container Registry"
  type        = string
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

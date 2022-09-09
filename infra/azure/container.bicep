@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of Container Registry resource.')
var containerRegistryName = 'cr${uniqueString(resourceGroup().id)}'

resource ContainerRegistry 'Microsoft.ContainerRegistry/registries@2022-02-01-preview' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: true
    anonymousPullEnabled: false
    dataEndpointEnabled: false
    encryption: {
      status: 'disabled'
    }
    networkRuleBypassOptions: 'AzureServices'
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
  }
}

output CONTAINER_REGISTRY_ENDPOINT string = ContainerRegistry.properties.loginServer
output CONTAINER_REGISTRY_NAME string = ContainerRegistry.name

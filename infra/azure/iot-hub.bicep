@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of Storage account resource.')
var storageAccountName = 'st${uniqueString(resourceGroup().id)}'

@description('Name of Storage account container.')
var storageContainerName = 'iothubdata'

@description('Name of IoT Hub resource.')
var iotHubName = 'iot-${uniqueString(resourceGroup().id)}'

@allowed([
  'F1'
  'S1'
])
param iotSkuName string = 'S1'

@description('The number of IoT Hub units.')
param iotSkuUnits int = 1

@description('Name of IoT Hub Device Provisioning Service resource.')
var provisioningServiceName = 'provs-${uniqueString(resourceGroup().id)}'

@allowed([
  'S1'
])
param dpsSkuName string = 'S1'

resource StorageAccount 'Microsoft.Storage/storageAccounts@2021-08-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'Storage'
}

resource IoTHubData 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-08-01' = {
  name: '${storageAccountName}/default/${storageContainerName}'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    StorageAccount
  ]
}

resource IoTHub 'Microsoft.Devices/IotHubs@2021-07-01' = {
  name: iotHubName
  location: location
  sku: {
    name: iotSkuName
    capacity: iotSkuUnits
  }
  properties: {
    storageEndpoints: {
      '$default': {
        sasTtlAsIso8601: 'PT1H'
        connectionString: 'DefaultEndpointsProtocol=https;EndpointSuffix=${environment().suffixes.storage};AccountName=${StorageAccount.name};AccountKey=${StorageAccount.listKeys().keys[0].value}'
        containerName: storageContainerName
      }
    }
  }
}

resource IoTHubDPS 'Microsoft.Devices/provisioningServices@2020-03-01' = {
  name: provisioningServiceName
  location: location
  sku: {
    name: dpsSkuName
  }
  properties: {
    iotHubs: [
      {
        connectionString: 'HostName=${IoTHub.properties.hostName};SharedAccessKeyName=iothubowner;SharedAccessKey=${listKeys(resourceId('Microsoft.Devices/IotHubs/Iothubkeys', IoTHub.name, 'iothubowner'), IoTHub.apiVersion).primaryKey}'
        location: location
      }
    ]
  }
}

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of Custom Vision Training resource.')
param customVisionTrainingName string = 'cvt-${uniqueString(resourceGroup().id)}'

@description('Name of Custom Vision Prediction resource.')
param customVisionPredictionName string = 'cvp-${uniqueString(resourceGroup().id)}'

@allowed([
  'F0'
  'S0'
])
param skuName string = 'S0'

resource CVTraining 'Microsoft.CognitiveServices/accounts@2022-03-01' = {
  name: customVisionTrainingName
  location: location
  sku: {
    name: skuName
  }
  kind: 'CustomVision.Training'
}

resource CVPrediction 'Microsoft.CognitiveServices/accounts@2022-03-01' = {
  name: customVisionPredictionName
  location: location
  sku: {
    name: skuName
  }
  kind: 'CustomVision.Prediction'
}

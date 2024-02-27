targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the workload which is used to generate a short unique hash used in all resources.')
param workloadName string

@minLength(1)
@description('Primary location for all resources.')
param location string

@description('Name of the resource group. If empty, a unique name will be generated.')
param resourceGroupName string = ''

@description('Tags for all resources.')
param tags object = {}

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, workloadName, location))

resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourceGroup}${workloadName}'
  location: location
  tags: union(tags, {})
}

module storageAccount './storage/storage-account.bicep' = {
  name: '${abbrs.storageAccount}${resourceToken}'
  scope: resourceGroup
  params: {
    name: '${abbrs.storageAccount}${resourceToken}'
    location: location
    tags: union(tags, {})
    sku: {
      name: 'Standard_LRS'
    }
  }
}

module trainingDataContainer './storage/storage-blob-container.bicep' = {
  name: '${abbrs.storageAccount}${resourceToken}-training-data'
  scope: resourceGroup
  params: {
    name: 'training-data'
    storageAccountName: storageAccount.outputs.name
  }
}

module documentIntelligence './ai_ml/document-intelligence.bicep' = {
  name: '${abbrs.documentIntelligence}${resourceToken}'
  scope: resourceGroup
  params: {
    name: '${abbrs.documentIntelligence}${resourceToken}'
    location: location
    tags: union(tags, {})
  }
}

output resourceGroupInfo object = {
  id: resourceGroup.id
  name: resourceGroup.name
  location: resourceGroup.location
  workloadName: workloadName
}

output storageAccountInfo object = {
  id: storageAccount.outputs.id
  name: storageAccount.outputs.name
  trainingDataContainerName: trainingDataContainer.outputs.name
}

output documentIntelligenceInfo object = {
  id: documentIntelligence.outputs.id
  name: documentIntelligence.outputs.name
  endpoint: documentIntelligence.outputs.endpoint
  host: documentIntelligence.outputs.host
}

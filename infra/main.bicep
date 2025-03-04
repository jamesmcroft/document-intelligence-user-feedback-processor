import { modelDeploymentInfo, raiPolicyInfo } from './ai_ml/ai-services.bicep'
import { identityInfo } from './security/managed-identity.bicep'

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
param tags object = {
  WorkloadName: workloadName
  Environment: 'Dev'
}

@description('Responsible AI policies for the Azure AI Services instance.')
param raiPolicies raiPolicyInfo[] = [
  {
    name: workloadName
    mode: 'Blocking'
    prompt: {}
    completion: {}
  }
]

@description('Identities to assign roles to.')
param identities identityInfo[] = []

var abbrs = loadJsonContent('./abbreviations.json')
var roles = loadJsonContent('./roles.json')
var resourceToken = toLower(uniqueString(subscription().id, workloadName, location))

var acaAddressPrefix = '10.0.0.0/23'

resource contributorRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.general.contributor
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.managementGovernance.resourceGroup}${workloadName}'
  location: location
  tags: union(tags, {})
}

var contributorIdentityAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: contributorRole.id
    principalType: identity.principalType
  }
]

module resourceGroupRoleAssignment './security/resource-group-role-assignment.bicep' = {
  name: '${resourceGroup.name}-role-assignment'
  scope: resourceGroup
  params: {
    roleAssignments: concat(contributorIdentityAssignments, [])
  }
}

resource keyVaultContributorRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.security.keyVaultContributor
}

var keyVaultContributorIdentityAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: keyVaultContributorRole.id
    principalType: identity.principalType
  }
]

var keyVaultName = '${abbrs.security.keyVault}${resourceToken}'
module keyVault './security/key-vault.bicep' = {
  name: keyVaultName
  scope: resourceGroup
  params: {
    name: keyVaultName
    location: location
    tags: union(tags, {})
    roleAssignments: concat(keyVaultContributorIdentityAssignments, [])
  }
}

var logAnalyticsWorkspaceName = '${abbrs.managementGovernance.logAnalyticsWorkspace}${resourceToken}'
module logAnalyticsWorkspace './management_governance/log-analytics-workspace.bicep' = {
  name: logAnalyticsWorkspaceName
  scope: resourceGroup
  params: {
    name: logAnalyticsWorkspaceName
    location: location
    tags: union(tags, {})
  }
}

var applicationInsightsName = '${abbrs.managementGovernance.applicationInsights}${resourceToken}'
module applicationInsights './management_governance/application-insights.bicep' = {
  name: applicationInsightsName
  scope: resourceGroup
  params: {
    name: applicationInsightsName
    location: location
    tags: union(tags, {})
    logAnalyticsWorkspaceName: logAnalyticsWorkspace.outputs.name
  }
}

resource acrPushRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.containers.acrPush
}

resource acrPullRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.containers.acrPull
}

var acrPushRoleAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: acrPushRole.id
    principalType: identity.principalType
  }
]

var acrPullRoleAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: acrPullRole.id
    principalType: identity.principalType
  }
]

var containerRegistryName = '${abbrs.containers.containerRegistry}${resourceToken}'
module containerRegistry './containers/container-registry.bicep' = {
  name: containerRegistryName
  scope: resourceGroup
  params: {
    name: containerRegistryName
    location: location
    tags: union(tags, {})
    sku: {
      name: 'Standard'
    }
    adminUserEnabled: true
    roleAssignments: concat(acrPushRoleAssignments, acrPullRoleAssignments, [])
  }
}

resource cognitiveServicesUserRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.ai.cognitiveServicesUser
}

resource cognitiveServicesContributorRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.ai.cognitiveServicesContributor
}

var cognitiveServicesUserRoleAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: cognitiveServicesUserRole.id
    principalType: identity.principalType
  }
]

var cognitiveServicesContributorRoleAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: cognitiveServicesContributorRole.id
    principalType: identity.principalType
  }
]

var aiServicesName = '${abbrs.ai.aiServices}${resourceToken}'
module aiServices './ai_ml/ai-services.bicep' = {
  name: aiServicesName
  scope: resourceGroup
  params: {
    name: aiServicesName
    location: location
    tags: union(tags, {})
    raiPolicies: raiPolicies
    deployments: []
    roleAssignments: concat(cognitiveServicesUserRoleAssignments, cognitiveServicesContributorRoleAssignments, [])
  }
}

// Require self-referencing role assignment for AI Services identity to access Azure OpenAI.
var aiServicesRoleAssignmentName = '${aiServicesName}-role-assignment'
module aiServicesRoleAssignment './security/resource-role-assignment.json' = {
  name: aiServicesRoleAssignmentName
  scope: resourceGroup
  params: {
    resourceId: aiServices.outputs.id
    roleAssignments: [
      {
        principalId: aiServices.outputs.principalId
        roleDefinitionId: cognitiveServicesUserRole.id
        principalType: 'ServicePrincipal'
      }
      {
        principalId: aiServices.outputs.principalId
        roleDefinitionId: cognitiveServicesContributorRole.id
        principalType: 'ServicePrincipal'
      }
    ]
  }
}

// Storage account roles required for interacting with Azure AI Foundry
resource storageAccountContributorRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.storage.storageAccountContributor
}

resource storageBlobDataContributorRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.storage.storageBlobDataContributor
}

resource storageFileDataPrivilegedContributorRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.storage.storageFileDataPrivilegedContributor
}

resource storageTableDataContributorRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.storage.storageTableDataContributor
}

var storageAccountContributorIdentityAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: storageAccountContributorRole.id
    principalType: identity.principalType
  }
]

var storageBlobDataContributorIdentityAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: storageBlobDataContributorRole.id
    principalType: identity.principalType
  }
]

var storageFileDataPrivilegedContributorIdentityAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: storageFileDataPrivilegedContributorRole.id
    principalType: identity.principalType
  }
]

var storageTableDataContributorIdentityAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: storageTableDataContributorRole.id
    principalType: identity.principalType
  }
]

var storageAccountName = '${abbrs.storage.storageAccount}${resourceToken}'
module storageAccount './storage/storage-account.bicep' = {
  name: storageAccountName
  scope: resourceGroup
  params: {
    name: storageAccountName
    location: location
    tags: union(tags, {})
    sku: {
      name: 'Standard_LRS'
    }
    roleAssignments: concat(
      storageAccountContributorIdentityAssignments,
      storageBlobDataContributorIdentityAssignments,
      storageFileDataPrivilegedContributorIdentityAssignments,
      storageTableDataContributorIdentityAssignments,
      [
        {
          principalId: aiServices.outputs.principalId
          roleDefinitionId: storageBlobDataContributorRole.id
          principalType: 'ServicePrincipal'
        }
      ]
    )
  }
}

resource azureMLDataScientistRole 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: resourceGroup
  name: roles.ai.azureMLDataScientist
}

var azureMLDataScientistRoleAssignments = [
  for identity in identities: {
    principalId: identity.principalId
    roleDefinitionId: azureMLDataScientistRole.id
    principalType: identity.principalType
  }
]

var aiHubName = '${abbrs.ai.aiHub}${resourceToken}'
module aiHub './ai_ml/ai-hub.bicep' = {
  name: aiHubName
  scope: resourceGroup
  params: {
    name: aiHubName
    friendlyName: 'Hub - Document Intelligence User Feedback Processor'
    descriptionInfo: 'Generated by the Document Intelligence User Feedback Processor repo'
    location: location
    tags: union(tags, {})
    storageAccountId: storageAccount.outputs.id
    keyVaultId: keyVault.outputs.id
    applicationInsightsId: applicationInsights.outputs.id
    containerRegistryId: containerRegistry.outputs.id
    aiServicesName: aiServices.outputs.name
    roleAssignments: concat(azureMLDataScientistRoleAssignments, [])
  }
}

var aiHubProjectName = '${abbrs.ai.aiHubProject}${resourceToken}'
module aiHubProject './ai_ml/ai-hub-project.bicep' = {
  name: aiHubProjectName
  scope: resourceGroup
  params: {
    name: aiHubProjectName
    friendlyName: 'Project - Document Intelligence User Feedback Processor'
    descriptionInfo: 'Generated by the Document Intelligence User Feedback Processor repo'
    location: location
    tags: union(tags, {})
    aiHubName: aiHub.outputs.name
    serverlessModels: []
    roleAssignments: concat(azureMLDataScientistRoleAssignments, [])
  }
}

var containerAppsEnvironmentName = '${abbrs.containers.containerAppsEnvironment}${resourceToken}'
module containerAppsEnvironment 'containers/container-apps-environment.bicep' = {
  name: containerAppsEnvironmentName
  scope: resourceGroup
  params: {
    name: containerAppsEnvironmentName
    location: location
    tags: union(tags, {})
    logAnalyticsWorkspaceName: logAnalyticsWorkspace.outputs.name
    applicationInsightsName: applicationInsights.outputs.name
  }
}

output subscriptionInfo object = {
  id: subscription().subscriptionId
  tenantId: subscription().tenantId
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
}

output keyVaultInfo object = {
  id: keyVault.outputs.id
  name: keyVault.outputs.name
  uri: keyVault.outputs.uri
}

output logAnalyticsWorkspaceInfo object = {
  id: logAnalyticsWorkspace.outputs.id
  name: logAnalyticsWorkspace.outputs.name
  customerId: logAnalyticsWorkspace.outputs.customerId
}

output applicationInsightsInfo object = {
  id: applicationInsights.outputs.id
  name: applicationInsights.outputs.name
}

output containerRegistryInfo object = {
  id: containerRegistry.outputs.id
  name: containerRegistry.outputs.name
  loginServer: containerRegistry.outputs.loginServer
}

output aiServicesInfo object = {
  id: aiServices.outputs.id
  name: aiServices.outputs.name
  endpoint: aiServices.outputs.endpoint
  host: aiServices.outputs.host
  openAIEndpoint: aiServices.outputs.openAIEndpoint
  openAIHost: aiServices.outputs.openAIHost
}

output aiHubInfo object = {
  id: aiHub.outputs.id
  name: aiHub.outputs.name
}

output aiHubProjectInfo object = {
  id: aiHubProject.outputs.id
  name: aiHubProject.outputs.name
}

output containerAppsEnvironmentInfo object = {
  id: containerAppsEnvironment.outputs.id
  name: containerAppsEnvironment.outputs.name
  defaultDomain: containerAppsEnvironment.outputs.defaultDomain
  staticIp: containerAppsEnvironment.outputs.staticIp
}

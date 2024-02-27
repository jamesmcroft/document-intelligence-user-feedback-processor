<#
.SYNOPSIS
    Deploy the core infrastructure for the Document Intelligence User Feedback Experiment to an Azure subscription.
.DESCRIPTION
    This script initiates the deployment of the main.bicep template to the current default Azure subscription,
    determined by the Azure CLI. The deployment name and location are required parameters.

	Follow the instructions in the DeploymentGuide.md file at the root of this project to understand what this
    script will deploy to your Azure subscription, and the step-by-step on how to run it.
.PARAMETER DeploymentName
    The name of the deployment to create in an Azure subscription.
.PARAMETER Location
    The location to deploy the Azure resources to.
.EXAMPLE
    .\Deploy-Infrastructure.ps1 -DeploymentName 'my-deployment' -Location 'westeurope'
.NOTES
    Author: James Croft
    Date: 2024-02-27
#>

param
(
    [Parameter(Mandatory = $true)]
    [string]$DeploymentName,
    [Parameter(Mandatory = $true)]
    [string]$Location
)

Write-Host "Deploying infrastructure..."

Set-Location -Path $PSScriptRoot

az --version

$deploymentOutputs = (az deployment sub create --name $DeploymentName --location $Location --template-file './infra/main.bicep' --parameters './infra/main.parameters.json' --parameters workloadName=$DeploymentName --parameters location=$Location --query 'properties.outputs' -o json) | ConvertFrom-Json
$deploymentOutputs | ConvertTo-Json | Out-File -FilePath './InfrastructureOutputs.json' -Encoding utf8

$resourceGroupName = $deploymentOutputs.resourceGroupInfo.value.name
$storageAccountName = $deploymentOutputs.storageAccountInfo.value.name
$storageAccountConnectionString = (az storage account show-connection-string --name $storageAccountName --resource-group $resourceGroupName --query 'connectionString' -o tsv)
$storageAccountKey = (az storage account keys list --account-name $storageAccountName --resource-group $resourceGroupName --query '[0].value' -o tsv)
$trainingDataContainerName = $deploymentOutputs.storageAccountInfo.value.trainingDataContainerName
$documentIntelligenceName = $deploymentOutputs.documentIntelligenceInfo.value.name
$documentIntelligenceEndpoint = $deploymentOutputs.documentIntelligenceInfo.value.endpoint
$documentIntelligencePrimaryKey = (az cognitiveservices account keys list --name $documentIntelligenceName --resource-group $resourceGroupName --query 'key1' -o tsv)

# Save the deployment outputs to a .env file
Write-Host "Saving the deployment outputs to a config.env file..."

function Set-ConfigurationFileVariable($configurationFile, $variableName, $variableValue) {
    if (Select-String -Path $configurationFile -Pattern $variableName) {
        (Get-Content $configurationFile) | Foreach-Object {
            $_ -replace "$variableName = .*", "$variableName = $variableValue"
        } | Set-Content $configurationFile
    }
    else {
        Add-Content -Path $configurationFile -value "$variableName = $variableValue"
    }
}

$configurationFile = "config.env"

if (-not (Test-Path $configurationFile)) {
    New-Item -Path $configurationFile -ItemType "file" -Value ""
}

Set-ConfigurationFileVariable $configurationFile "AZURE_RESOURCE_GROUP_NAME" $resourceGroupName
Set-ConfigurationFileVariable $configurationFile "AZURE_STORAGE_ACCOUNT_NAME" $storageAccountName
Set-ConfigurationFileVariable $configurationFile "AZURE_STORAGE_ACCOUNT_CONNECTION_STRING" $storageAccountConnectionString
Set-ConfigurationFileVariable $configurationFile "AZURE_STORAGE_ACCOUNT_KEY" $storageAccountKey
Set-ConfigurationFileVariable $configurationFile "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT" $documentIntelligenceEndpoint
Set-ConfigurationFileVariable $configurationFile "AZURE_DOCUMENT_INTELLIGENCE_KEY" $documentIntelligencePrimaryKey
Set-ConfigurationFileVariable $configurationFile "AZURE_DOCUMENT_INTELLIGENCE_TRAINING_DATA_CONTAINER_NAME" $trainingDataContainerName

return $deploymentOutputs
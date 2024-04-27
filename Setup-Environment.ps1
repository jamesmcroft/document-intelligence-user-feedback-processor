<#
.SYNOPSIS
    Deploys the infrastructure and applications required to run the solution.
.PARAMETER DeploymentName
	The name of the deployment.
.PARAMETER Location
    The location of the deployment.
.PARAMETER SkipInfrastructure
    Whether to skip the infrastructure deployment. Requires InfrastructureOutputs.json to exist in the infra directory.
.EXAMPLE
    .\Setup-Environment.ps1 -DeploymentName 'my-deployment' -Location 'westeurope' -SkipInfrastructure $false
.NOTES
    Author: James Croft
#>

param
(
    [Parameter(Mandatory = $true)]
    [string]$DeploymentName,
    [Parameter(Mandatory = $true)]
    [string]$Location,
    [Parameter(Mandatory = $true)]
    [string]$SkipInfrastructure
)

function Set-ConfigurationFileVariable($configurationFile, $variableName, $variableValue) {
    if (-not (Test-Path $configurationFile)) {
        New-Item -Path $configurationFile -ItemType file
    }

    if (Select-String -Path $configurationFile -Pattern $variableName) {
        (Get-Content $configurationFile) | Foreach-Object {
            $_ -replace "$variableName = .*", "$variableName = $variableValue"
        } | Set-Content $configurationFile
    }
    else {
        Add-Content -Path $configurationFile -value "$variableName = $variableValue"
    }
}

Write-Host "Starting environment setup..."

if ($SkipInfrastructure -eq '$false' || -not (Test-Path -Path './infra/InfrastructureOutputs.json')) {
    Write-Host "Deploying infrastructure..."
    $InfrastructureOutputs = (./infra/Deploy-Infrastructure.ps1 `
            -DeploymentName $DeploymentName `
            -Location $Location `
            -ErrorAction Stop)
}
else {
    Write-Host "Skipping infrastructure deployment. Using existing outputs..."
    $InfrastructureOutputs = Get-Content -Path './infra/InfrastructureOutputs.json' -Raw | ConvertFrom-Json
}

$ResourceGroupName = $InfrastructureOutputs.resourceGroupInfo.value.name
$ManagedIdentityClientId = $InfrastructureOutputs.managedIdentityInfo.value.clientId
$StorageAccountName = $InfrastructureOutputs.storageAccountInfo.value.name
$StorageAccountConnectionString = (az storage account show-connection-string --name $StorageAccountName --resource-group $ResourceGroupName --query 'connectionString' -o tsv)
$StorageAccountKey = (az storage account keys list --account-name $StorageAccountName --resource-group $ResourceGroupName --query '[0].value' -o tsv)
$TrainingDataContainerName = $InfrastructureOutputs.storageAccountInfo.value.trainingDataContainerName
$DocumentIntelligenceName = $InfrastructureOutputs.documentIntelligenceInfo.value.name
$DocumentIntelligenceEndpoint = $InfrastructureOutputs.documentIntelligenceInfo.value.endpoint
$DocumentIntelligencePrimaryKey = (az cognitiveservices account keys list --name $DocumentIntelligenceName --resource-group $ResourceGroupName --query 'key1' -o tsv)

Write-Host "Updating local settings..."

$ConfigurationFile = './.env'

Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'RESOURCE_GROUP_NAME' -variableValue $ResourceGroupName
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'MANAGED_IDENTITY_CLIENT_ID' -variableValue $ManagedIdentityClientId
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'STORAGE_ACCOUNT_NAME' -variableValue $StorageAccountName
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'STORAGE_ACCOUNT_CONNECTION_STRING' -variableValue $StorageAccountConnectionString
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'STORAGE_ACCOUNT_KEY' -variableValue $StorageAccountKey
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'DOCUMENT_INTELLIGENCE_TRAINING_DATA_CONTAINER_NAME' -variableValue $TrainingDataContainerName
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'DOCUMENT_INTELLIGENCE_NAME' -variableValue $DocumentIntelligenceName
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'DOCUMENT_INTELLIGENCE_ENDPOINT' -variableValue $DocumentIntelligenceEndpoint
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'DOCUMENT_INTELLIGENCE_KEY' -variableValue $DocumentIntelligencePrimaryKey

Pop-Location

return $deploymentOutputs

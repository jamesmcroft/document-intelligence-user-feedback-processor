param
(
    [Parameter(Mandatory = $true)]
    [string]$DeploymentName,
    [Parameter(Mandatory = $true)]
    [string]$Location,
    [switch]$WhatIf
)

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

Write-Host "Starting environment setup..."

Write-Host "Deploying infrastructure..."
$InfrastructureOutputs = (./infra/Deploy-Infrastructure.ps1 `
        -DeploymentName $DeploymentName `
        -Location $Location `
        -WhatIf:$WhatIf)

if (-not $InfrastructureOutputs) {
    Write-Error "Failed to deploy infrastructure."
    exit 1
}

$azureResourceGroupName = $InfrastructureOutputs.resourceGroupInfo.value.name
$azureClientId = $InfrastructureOutputs.managedIdentityInfo.value.clientId
$storageAccountName = $InfrastructureOutputs.storageAccountInfo.value.name
$aiServicesEndpoint = $InfrastructureOutputs.aiServicesInfo.value.endpoint

Write-Host "Updating local settings..."

$ConfigurationFile = './.env'
if (-not (Test-Path -Path $ConfigurationFile)) {
    New-Item -Path $ConfigurationFile -ItemType File
}

Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'AZURE_RESOURCE_GROUP' -variableValue $azureResourceGroupName
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'AZURE_CLIENT_ID' -variableValue $azureClientId
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'STORAGE_ACCOUNT_NAME' -variableValue $storageAccountName
Set-ConfigurationFileVariable -configurationFile $ConfigurationFile -variableName 'AI_SERVICES_ENDPOINT' -variableValue $aiServicesEndpoint
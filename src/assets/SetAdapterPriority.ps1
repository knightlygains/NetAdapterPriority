<#
.SYNOPSIS
    Manage network adapter priorities by changing InterfaceMetric values.

.DESCRIPTION
    This script allows you to change the InterfaceMetric 
    (priority) of a specific adapter. Lower InterfaceMetric values mean higher priority.

.PARAMETER Adapters
    List all network adapters with their Index, Alias, Description, and InterfaceMetric.

.PARAMETER Priority
    Change the InterfaceMetric of a specific adapter. Requires two values:
    - First value: Interface Index (ifIndex)
    - Second value: New InterfaceMetric value

.EXAMPLE
    .\SetAdapterPriority.ps1 -Adapters
    Lists all network adapters with their details.

.EXAMPLE
    .\SetAdapterPriority.ps1 -Priority 11 85
    Sets the InterfaceMetric of adapter with Index 11 to 85.
#>

[CmdletBinding(DefaultParameterSetName = 'adapters')]
param(
    [Parameter(ParameterSetName = 'adapters')]
    [switch]$Adapters,

    [Parameter(ParameterSetName = 'priority', Mandatory = $true)]
    [string]$Priority
)

function Show-Adapters {
    $adapters = Get-NetIPInterface
    
    Write-Host ""
    Write-Host "=== Network Adapters ===" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($i in $adapters) {
        $interface_description = Get-NetAdapter | Where-Object { $_.ifIndex -eq $i.ifIndex }
        $interface_description = $interface_description.InterfaceDescription
        $interface_alias = $i.InterfaceAlias
        if ($null -eq $interface_description) {
            $interface_description = "No Description"
        }

        if ($null -eq $interface_alias -or $interface_alias -eq "") {
            $interface_alias = "No Alias"
        }

        Write-Host "[Adapter][IPV]$($i.AddressFamily)[IPV][Alias]$($interface_alias)[Alias][Description]$($interface_description)[Description][Index]$($i.ifIndex)[Index][Metric]$($i.InterfaceMetric)[Metric][CONNECTION_STATE]$($i.ConnectionState)[CONNECTION_STATE][Adapter]"

    }
}

function Set-AdapterPriority {
    param(
        [string]$PriorityInput
    )
    
    try {
        # Verify the interface exists

        $InterfaceIndex = $PriorityInput.Split(" ")[0]
        $InterfaceMetric = $PriorityInput.Split(" ")[1]

        $adapter = Get-NetIPInterface | Where-Object { $_.ifIndex -eq $InterfaceIndex }
        if ($null -eq $adapter) {
            Write-Host "Error: Interface with Index $InterfaceIndex not found." -ForegroundColor Red
            return $false
        }
        
        # Show current adapter info
        $netAdapter = Get-NetAdapter | Where-Object { $_.ifIndex -eq $InterfaceIndex }
        $description = if ($netAdapter) { $netAdapter.InterfaceDescription } else { "No Description" }
        
        Write-Host ""
        Write-Host "Changing adapter:" -ForegroundColor Cyan
        Write-Host "  Description: $description"
        Write-Host "  Alias: $($adapter.InterfaceAlias)"
        Write-Host "  Index: $InterfaceIndex"
        Write-Host "  Current Metric: $($adapter.InterfaceMetric)"
        Write-Host "  New Metric: $InterfaceMetric"
        Write-Host ""
        
        # Apply the change
        Set-NetIPInterface -InterfaceIndex $InterfaceIndex -InterfaceMetric $InterfaceMetric -ErrorAction Stop
        Write-Host "Success: InterfaceMetric changed to $InterfaceMetric" -ForegroundColor Green
        Write-Host ""
        return $true
    }
    catch {
        Write-Host "Error: Failed to set InterfaceMetric - $_" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# Main script logic
switch ($PSCmdlet.ParameterSetName) {
    'adapters' {
        Show-Adapters
    }
    'priority' {
        $result = Set-AdapterPriority $Priority
        if (-not $result) {
            exit 1
        }
    }
}

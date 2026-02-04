param(
    [string]$McpPath = "$env:APPDATA\Code\User\mcp.json",
    [string]$RepoDir = "C:/repo/fabric-rti-mcp/",
    [string]$UvExe = "C:/Users/avhaddad/.local/bin/uv.exe"
)

$mcp = (Get-Content -Path $McpPath -Raw) | ConvertFrom-Json

$servers = @{}
if ($mcp.PSObject.Properties.Name -contains "servers" -and $null -ne $mcp.servers) {
    foreach ($p in $mcp.servers.PSObject.Properties) {
        $servers[$p.Name] = $p.Value
    }
}

$null = $servers.Remove("fabric-rti-mcp-aviv-install")

$servers["fabric-rti-mcp"] = [pscustomobject]@{
    type    = "stdio"
    command = $UvExe
    args    = @(
        "--directory",
        $RepoDir,
        "run",
        "-m",
        "fabric_rti_mcp.server"
    )
    env     = [pscustomobject]@{
        KUSTO_SERVICE_URI        = "https://help.kusto.windows.net/"
        KUSTO_SERVICE_DEFAULT_DB = "Samples"
        FABRIC_API_BASE_URL      = "https://api.fabric.microsoft.com/v1"
    }
}

$mcp.servers = $servers

if ($mcp.PSObject.Properties.Name -contains "inputs") {
    $null = $mcp.PSObject.Properties.Remove("inputs")
}

$mcp | ConvertTo-Json -Depth 20 | Set-Content -Path $McpPath -Encoding UTF8

Write-Host "Updated MCP config: $McpPath"
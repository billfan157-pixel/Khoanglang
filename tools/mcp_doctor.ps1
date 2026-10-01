param(
    [switch]$Launch,
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'

$Port = 8000
$Url = "http://127.0.0.1:$Port/mcp"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Uproject = Join-Path $ProjectRoot 'KhoangLang0217.uproject'

function Get-ListeningProcess {
    param([int]$Port)
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

function Get-EditorProcesses {
    Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'" -ErrorAction SilentlyContinue |
        Select-Object ProcessId, CreationDate, CommandLine
}

function Test-EditorProject {
    param($Process)
    if ($null -eq $Process) { return $false }
    return [bool]($Process.CommandLine -match '\.uproject')
}

function Get-EditorExe {
    $association = (Get-Content -LiteralPath $Uproject -Raw | ConvertFrom-Json).EngineAssociation
    $roots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}) | Where-Object { $_ }
    foreach ($root in $roots) {
        $candidate = Join-Path $root "Epic Games\UE_$association\Engine\Binaries\Win64\UnrealEditor.exe"
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw "UnrealEditor.exe for engine association '$association' not found under $roots"
}

function Invoke-McpRequest {
    param(
        [string]$Payload,
        [string]$SessionId
    )
    $headers = @{ Accept = 'application/json, text/event-stream' }
    if ($SessionId) { $headers['Mcp-Session-Id'] = $SessionId }
    Invoke-WebRequest -Uri $Url -Method Post -Body $Payload -ContentType 'application/json' `
        -Headers $headers -TimeoutSec 20 -UseBasicParsing
}

function Get-McpProbe {
    try {
        $init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mcp_doctor","version":"1.0"}}}'
        $response = Invoke-McpRequest -Payload $init -SessionId $null
        $session = $response.Headers['Mcp-Session-Id']
        $null = Invoke-McpRequest -Payload '{"jsonrpc":"2.0","method":"notifications/initialized"}' -SessionId $session
        $tools = Invoke-McpRequest -Payload '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' -SessionId $session
        $names = @((ConvertFrom-Json $tools.Content).result.tools | ForEach-Object { $_.name })
        return [pscustomobject]@{ Ok = $true; Session = $session; Tools = $names; Error = '' }
    } catch {
        return [pscustomobject]@{ Ok = $false; Session = ''; Tools = @(); Error = $_.Exception.Message }
    }
}

function Write-State {
    param([string]$Label, [string]$Value)
    Write-Output ("{0,-20}{1}" -f ($Label + ':'), $Value)
}

function Start-ProjectEditor {
    $editorExe = Get-EditorExe
    Write-Output "Launching $editorExe with the project..."
    Start-Process -FilePath $editorExe -ArgumentList "`"$Uproject`"", '-ModelContextProtocolStartServer' | Out-Null
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $nextReport = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        if (Get-ListeningProcess -Port $Port) { return $true }
        if ((Get-Date) -ge $nextReport) {
            $left = [int]($deadline - (Get-Date)).TotalSeconds
            Write-Output "  still starting, ${left}s left (the first load can take minutes)"
            $nextReport = (Get-Date).AddSeconds(15)
        }
    }
    return $false
}

Write-Output '== Unreal MCP doctor =='
Write-State 'Endpoint' $Url

$listener = Get-ListeningProcess -Port $Port

if (-not $listener -and $Launch) {
    if (Start-ProjectEditor) {
        $listener = Get-ListeningProcess -Port $Port
    } else {
        Write-State "Port $Port" "not listening after $TimeoutSeconds s"
    }
}

$editors = Get-EditorProcesses
if ($editors) {
    foreach ($editor in $editors) {
        $role = if (Test-EditorProject -Process $editor) { 'project open' } else { 'no project (Project Browser)' }
        Write-State ('Editor PID ' + $editor.ProcessId) $role
    }
} else {
    Write-State 'Editor' 'not running'
}

if ($listener) {
    Write-State "Port $Port" ('listening by PID ' + $listener.OwningProcess)
} else {
    Write-State "Port $Port" 'not listening'
}

if (-not $listener) {
    $projectEditor = $editors | Where-Object { Test-EditorProject -Process $_ } | Select-Object -First 1
    $browserOnlyEditor = $editors | Where-Object { -not (Test-EditorProject -Process $_) } | Select-Object -First 1
    Write-Output ''
    if ($browserOnlyEditor) {
        Write-Output 'CAUSE: an editor instance is running without a .uproject, so the'
        Write-Output '        ModelContextProtocol plugin is not loaded and no server exists.'
        Write-Output '        Open the project in that editor, or close it and relaunch.'
    } elseif (-not $projectEditor) {
        Write-Output 'CAUSE: no editor process holds the project, and the MCP server lives'
        Write-Output '        inside that process. Re-run with -Launch to start it.'
    } else {
        Write-Output 'CAUSE: the editor holds the project but the server is not up. Re-run'
        Write-Output '        with -Launch, or type ModelContextProtocol.StartServer in the'
        Write-Output '        editor console.'
    }
    Write-Output ''
    Write-Output 'OpenCode does not retry a server that was down when it started, so its'
    Write-Output 'unreal-mcp tools stay missing until OpenCode itself is restarted.'
    exit 1
}

$probe = Get-McpProbe
Write-Output ''
if (-not $probe.Ok) {
    Write-State 'Handshake' ('FAILED: ' + $probe.Error)
    exit 1
}

Write-State 'Handshake' 'ok'
Write-State 'Session' $probe.Session
Write-State 'Meta-tools' ($probe.Tools -join ', ')
exit 0

param(
    [switch]$SkipVersionBump
)

$ErrorActionPreference = "Stop"
$versionPath = Join-Path $PSScriptRoot "client_features\core.py"
$windowsPythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$linuxPythonPath = Join-Path $PSScriptRoot ".venv/bin/python"
$pythonPath = if (Test-Path $windowsPythonPath) { $windowsPythonPath } else { $linuxPythonPath }

if (-not (Test-Path $pythonPath)) {
    throw "Virtual environment Python was not found at $pythonPath"
}

$clientSource = [System.IO.File]::ReadAllText($versionPath)
$versionPattern = '(?m)^APP_VERSION = "(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d{2})"\r?$'
$versionMatch = [regex]::Match($clientSource, $versionPattern)
if (-not $versionMatch.Success) {
    throw "Could not find a semantic APP_VERSION in client_features/core.py"
}

$versionParts = @(
    [int]$versionMatch.Groups[1].Value,
    [int]$versionMatch.Groups[2].Value,
    [int]$versionMatch.Groups[3].Value,
    [int]$versionMatch.Groups[4].Value,
    [int]$versionMatch.Groups[5].Value
)
$currentVersion = $versionParts -join "."
$nextVersion = $currentVersion
if (-not $SkipVersionBump) {
    for ($index = 4; $index -ge 0; $index--) {
        $versionParts[$index]++
        $limit = if ($index -eq 4) { 100 } else { 1000 }
        if ($versionParts[$index] -lt $limit) { break }
        $versionParts[$index] = 0
    }
    $nextVersion = '{0}.{1}.{2}.{3}.{4:D2}' -f $versionParts[0], $versionParts[1], $versionParts[2], $versionParts[3], $versionParts[4]
    $replacement = 'APP_VERSION = "{0}"' -f $nextVersion
    $updatedSource = [regex]::Replace($clientSource, $versionPattern, $replacement, 1)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($versionPath, $updatedSource, $utf8NoBom)
    Write-Host "Client version: $currentVersion -> $nextVersion"
} else {
    Write-Host "Client version: $currentVersion"
}

& $pythonPath -m PyInstaller --clean --noconfirm (Join-Path $PSScriptRoot "KeyboardService.spec")
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Built dist\KeyboardService.exe for client version $nextVersion"

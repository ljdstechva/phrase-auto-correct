param(
    [switch]$PullModel,
    [switch]$SkipModelPrompt,
    [switch]$InstallOllamaWithWinget,
    [string]$OllamaModel
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceInstall = Join-Path $ProjectRoot "source\install.ps1"

if (-not (Test-Path -LiteralPath $SourceInstall)) {
    Write-Host "Installer not found: $SourceInstall" -ForegroundColor Red
    exit 1
}

& $SourceInstall
exit $LASTEXITCODE

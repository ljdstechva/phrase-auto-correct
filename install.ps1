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

$ForwardArgs = @{}
if ($PullModel) {
    $ForwardArgs["PullModel"] = $true
}
if ($SkipModelPrompt) {
    $ForwardArgs["SkipModelPrompt"] = $true
}
if ($InstallOllamaWithWinget) {
    $ForwardArgs["InstallOllamaWithWinget"] = $true
}
if ($PSBoundParameters.ContainsKey("OllamaModel")) {
    $ForwardArgs["OllamaModel"] = $OllamaModel
}

& $SourceInstall @ForwardArgs
exit $LASTEXITCODE

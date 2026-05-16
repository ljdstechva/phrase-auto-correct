param(
    [switch]$Console
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PythonwExe = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"

function Test-AppProcess {
    $processes = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -in @("python.exe", "pythonw.exe")) -and
        $_.CommandLine -and
        ($_.CommandLine.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0) -and
        ($_.CommandLine.IndexOf("app.main", [StringComparison]::OrdinalIgnoreCase) -ge 0)
    }
    return @($processes)
}

if (-not (Test-Path -LiteralPath $PythonExe)) {
    Write-Host "Virtual environment not found. Run install.ps1 first." -ForegroundColor Yellow
    exit 1
}

if ($Console) {
    Push-Location $ProjectRoot
    try {
        & $PythonExe -m app.main
        exit $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

$existing = Test-AppProcess
if ($existing.Count -gt 0) {
    Write-Host "Phrase Auto-correct is already running."
    exit 0
}

Start-Process -FilePath $PythonwExe `
    -ArgumentList "-m", "app.main" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden

Start-Sleep -Seconds 2
$running = Test-AppProcess
if ($running.Count -gt 0) {
    Write-Host "Phrase Auto-correct started."
    exit 0
}

Write-Host "Phrase Auto-correct did not appear to start. Try .\run.ps1 -Console for details." -ForegroundColor Red
exit 1

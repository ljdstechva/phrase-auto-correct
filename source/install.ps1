param(
    [switch]$PullModel,
    [switch]$SkipModelPrompt,
    [switch]$InstallOllamaWithWinget,
    [string]$OllamaModel
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = Join-Path $ProjectRoot ".venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$PythonwExe = Join-Path $VenvPath "Scripts\pythonw.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$Sources = Join-Path $ProjectRoot "sources"
$env:PIP_CACHE_DIR = Join-Path $Sources "pip-cache"

function New-LocalVenv {
    if (Test-Path -LiteralPath $PythonExe) {
        return
    }
    Write-Host "Creating local Python environment..."
    Push-Location $ProjectRoot
    try {
        python -m venv .venv
    }
    finally {
        Pop-Location
    }
}

function Install-Dependencies {
    Write-Host "Installing local dependencies..."
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r $Requirements
}

function Stop-AppProcesses {
    $ParentRoot = Split-Path -Parent $ProjectRoot
    $OwnedRoots = @($ProjectRoot, $ParentRoot)
    $Processes = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -in @("python.exe", "pythonw.exe")) -and
        $_.CommandLine -and
        ($_.CommandLine.IndexOf("app.main", [StringComparison]::OrdinalIgnoreCase) -ge 0) -and
        (
            ($_.CommandLine.IndexOf($OwnedRoots[0], [StringComparison]::OrdinalIgnoreCase) -ge 0) -or
            ($_.CommandLine.IndexOf($OwnedRoots[1], [StringComparison]::OrdinalIgnoreCase) -ge 0)
        )
    }

    foreach ($Process in $Processes) {
        if ($Process.ProcessId -eq $PID) {
            continue
        }
        Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped existing app process $($Process.ProcessId)."
    }
}

function New-StartupShortcut {
    if (-not (Test-Path -LiteralPath $PythonwExe)) {
        throw "pythonw.exe was not found in the local virtual environment."
    }

    $StartupFolder = [Environment]::GetFolderPath("Startup")
    $ShortcutPath = Join-Path $StartupFolder "Phrase Auto-correct.lnk"
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $PythonwExe
    $Shortcut.Arguments = "-m app.main"
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.Description = "Phrase Auto-correct"
    $Shortcut.Save()
    Write-Host "Startup shortcut registered: $ShortcutPath"
}

New-Item -ItemType Directory -Force -Path $Sources | Out-Null
New-LocalVenv
Install-Dependencies
Stop-AppProcesses
New-StartupShortcut

Write-Host "Starting Phrase Auto-correct..."
& (Join-Path $ProjectRoot "run.ps1")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Install complete. Use Ctrl+Space after highlighting text."
exit 0

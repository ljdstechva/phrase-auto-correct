param(
    [switch]$PullModel,
    [switch]$SkipModelPrompt,
    [switch]$InstallOllamaWithWinget,
    [string]$OllamaModel = "qwen3.5:9b"
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

function Read-YesNo {
    param(
        [string]$Prompt,
        [bool]$Default = $false
    )

    $Suffix = if ($Default) { "[Y/n]" } else { "[y/N]" }
    while ($true) {
        $Answer = Read-Host "$Prompt $Suffix"
        if ([string]::IsNullOrWhiteSpace($Answer)) {
            return $Default
        }
        switch ($Answer.Trim().ToLowerInvariant()) {
            "y" { return $true }
            "yes" { return $true }
            "n" { return $false }
            "no" { return $false }
            default { Write-Host "Please answer y or n." -ForegroundColor Yellow }
        }
    }
}

function Get-OllamaExe {
    $Command = Get-Command "ollama" -ErrorAction SilentlyContinue
    if ($Command) {
        return $Command.Source
    }

    $Candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        (Join-Path $env:ProgramFiles "Ollama\ollama.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Ollama\ollama.exe")
    )
    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path -LiteralPath $Candidate)) {
            return $Candidate
        }
    }
    return $null
}

function Install-OllamaWithWingetIfRequested {
    $Winget = Get-Command "winget" -ErrorAction SilentlyContinue
    if (-not $Winget) {
        Write-Host "WinGet was not found. Install Ollama manually from https://ollama.com/download, then run:" -ForegroundColor Yellow
        Write-Host ".\install.ps1 -PullModel"
        return
    }

    Write-Host "Installing Ollama with WinGet..."
    & $Winget.Source install --id Ollama.Ollama --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "WinGet could not install Ollama. Install it manually from https://ollama.com/download."
    }
}

function Test-OllamaModelInstalled {
    param(
        [string]$OllamaExe,
        [string]$ModelName
    )

    $Escaped = [regex]::Escape($ModelName)
    $List = & $OllamaExe list 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    return ($List -match "(?m)^$Escaped(\s|$)")
}

function Install-OllamaModel {
    param(
        [string]$ModelName
    )

    $ShouldPull = $PullModel
    if (-not $ShouldPull -and -not $SkipModelPrompt) {
        Write-Host ""
        Write-Host "Optional local AI model setup"
        Write-Host "Recommended model: $ModelName"
        Write-Host "Download size: about 6.6 GB"
        Write-Host "This improves grammar quality and keeps rewriting local through Ollama."
        $ShouldPull = Read-YesNo "Download and install $ModelName now?"
    }
    if (-not $ShouldPull) {
        Write-Host "Skipping Ollama model download. You can run later: ollama pull $ModelName"
        return
    }

    $OllamaExe = Get-OllamaExe
    if (-not $OllamaExe) {
        if ($InstallOllamaWithWinget -or (Read-YesNo "Ollama is required but was not found. Install Ollama with WinGet now?")) {
            Install-OllamaWithWingetIfRequested
            Start-Sleep -Seconds 3
            $OllamaExe = Get-OllamaExe
        }
    }

    if (-not $OllamaExe) {
        Write-Host "Ollama is still not available." -ForegroundColor Yellow
        Write-Host "Install Ollama from https://ollama.com/download, then run:"
        Write-Host ".\install.ps1 -PullModel"
        return
    }

    if (Test-OllamaModelInstalled -OllamaExe $OllamaExe -ModelName $ModelName) {
        Write-Host "Ollama model already installed: $ModelName"
        return
    }

    Write-Host "Downloading $ModelName through Ollama..."
    Write-Host "The installer does not throttle this transfer. Download speed is limited by your network, Ollama, disk speed, and the model host."
    Write-Host "It is not safe or reliable to force Windows to reserve all system bandwidth, so no bandwidth-hogging network changes are made."
    $Process = Start-Process -FilePath $OllamaExe -ArgumentList @("pull", $ModelName) -NoNewWindow -PassThru
    try {
        $Process.PriorityClass = "High"
    }
    catch {
        Write-Host "Could not raise downloader process priority; continuing normally."
    }
    $Process.WaitForExit()
    if ($Process.ExitCode -ne 0) {
        throw "Ollama model download failed with exit code $($Process.ExitCode)."
    }
    Write-Host "Ollama model installed: $ModelName"
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
Install-OllamaModel -ModelName $OllamaModel
New-StartupShortcut

Write-Host "Starting Phrase Auto-correct..."
& (Join-Path $ProjectRoot "run.ps1")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Install complete. Use Ctrl+Space after highlighting text."
exit 0

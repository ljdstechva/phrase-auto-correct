param(
    [switch]$FromTray
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Remove-StartupShortcut {
    $StartupFolder = [Environment]::GetFolderPath("Startup")
    $ShortcutPath = Join-Path $StartupFolder "Phrase Auto-correct.lnk"
    if (-not (Test-Path -LiteralPath $ShortcutPath)) {
        Write-Host "Startup shortcut was not present."
        return
    }

    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Target = [string]$Shortcut.TargetPath
    $WorkingDirectory = [string]$Shortcut.WorkingDirectory
    $targetMatches = $Target.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0
    $workingMatches = $WorkingDirectory.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0
    if ($targetMatches -or $workingMatches) {
        Remove-Item -LiteralPath $ShortcutPath -Force
        Write-Host "Removed startup shortcut."
    }
    else {
        Write-Host "Skipped startup shortcut because it does not point to this folder." -ForegroundColor Yellow
    }
}

function Remove-LegacyRunValue {
    $RunKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    foreach ($Name in @("Phrase Auto-correct", "PhraseAutoCorrect")) {
        $Item = Get-ItemProperty -Path $RunKey -Name $Name -ErrorAction SilentlyContinue
        if ($null -eq $Item) {
            continue
        }
        $Value = [string]$Item.$Name
        if ($Value.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            Remove-ItemProperty -Path $RunKey -Name $Name -Force
            Write-Host "Removed legacy Run registry value: $Name"
        }
        else {
            Write-Host "Skipped Run registry value not owned by this app: $Name" -ForegroundColor Yellow
        }
    }
}

function Stop-AppProcess {
    $Processes = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -in @("python.exe", "pythonw.exe")) -and
        $_.CommandLine -and
        ($_.CommandLine.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0) -and
        ($_.CommandLine.IndexOf("app.main", [StringComparison]::OrdinalIgnoreCase) -ge 0)
    }

    foreach ($Process in $Processes) {
        if ($Process.ProcessId -eq $PID) {
            continue
        }
        Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped app process $($Process.ProcessId)."
    }
}

Remove-StartupShortcut
Remove-LegacyRunValue
Stop-AppProcess

Write-Host "Uninstall complete. Source files were left in place."
if ($FromTray) {
    Start-Sleep -Seconds 2
}
exit 0

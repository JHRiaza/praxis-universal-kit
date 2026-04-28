# PRAXIS Universal Kit â€” Windows Installer (PowerShell 5.1+)
# ===========================================================
# Usage: .\install.ps1 [-Lang es] [-Dir C:\path\to\project]
# Requirements: Python 3.10+, PowerShell 5.1+
# No admin required.

[CmdletBinding()]
param(
    [string]$Lang = "en",
    [string]$Dir  = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
$PraxisVersion = "0.6.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = $Dir

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
function Write-Ok   { param([string]$Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "  [!]  $Msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$Msg) Write-Host "  [X]  $Msg" -ForegroundColor Red }
function Write-Info { param([string]$Msg) Write-Host "  .    $Msg" -ForegroundColor DarkGray }
function Write-Sep  { Write-Host ("â”€" * 60) -ForegroundColor DarkGray }
function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Sep
    Write-Host "  PRAXIS $Title" -ForegroundColor Cyan
    Write-Sep
}

# ---------------------------------------------------------------------------
# Check Python
# ---------------------------------------------------------------------------
function Find-Python {
    $candidates = @("python", "python3", "py")
    foreach ($cmd in $candidates) {
        try {
            $version = & $cmd --version 2>&1
            if ($version -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -ge 3 -and $minor -ge 8) {
                    return $cmd
                }
            }
        } catch { }
    }

    # Try py launcher (Windows Python launcher)
    try {
        $version = & py -3 --version 2>&1
        if ($version -match "Python 3\.") {
            return "py -3"
        }
    } catch { }

    return $null
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
function Main {
    Write-Header "Universal Kit v$PraxisVersion â€” Windows Installer"
    Write-Host ""

    # Check Python
    Write-Info "Checking Python version..."
    $PythonCmd = Find-Python
    if (-not $PythonCmd) {
        Write-Err "Python 3.10+ is required but not found."
        Write-Info "Install Python from: https://python.org/downloads"
        Write-Info "Make sure to check 'Add Python to PATH' during installation."
        exit 1
    }
    $PythonVersion = & $PythonCmd --version 2>&1
    Write-Ok "Found: $PythonVersion ($PythonCmd)"

    # Show consent
    Write-Host ""
    if ($Lang -eq "es" -and (Test-Path "$ScriptDir\CONSENTIMIENTO.md")) {
        $ConsentFile = "$ScriptDir\CONSENTIMIENTO.md"
    } else {
        $ConsentFile = "$ScriptDir\CONSENT.md"
    }

    if (Test-Path $ConsentFile) {
        Write-Host "  Research Consent Form:" -ForegroundColor White
        Write-Info "Please review: $ConsentFile"
        Write-Host ""
        Get-Content $ConsentFile | Select-Object -First 20 | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Gray
        }
        Write-Host ""
        Write-Info "(See full file for complete terms)"
    }

    Write-Host ""
    $ConsentResponse = Read-Host "  Do you consent to participate in this research? [y/N]"
    Write-Host ""

    $ConsentLower = $ConsentResponse.ToLower().Trim()
    if ($ConsentLower -notin @("y", "yes", "s", "si")) {
        Write-Warn "Consent required to participate. Exiting."
        Write-Info "Read $ConsentFile for full research details."
        exit 0
    }

    Write-Ok "Consent recorded."

    # Project directory
    Write-Host ""
    Write-Info "Project directory: $ProjectDir"
    if (-not (Test-Path $ProjectDir)) {
        New-Item -ItemType Directory -Path $ProjectDir -Force | Out-Null
        Write-Ok "Created: $ProjectDir"
    }

    # Detect platforms
    Write-Host ""
    Write-Info "Detecting AI platforms..."
    $DetectScript = @"
import sys, os
sys.path.insert(0, r'$ScriptDir\collector')
os.chdir(r'$ProjectDir')
from praxis_collector import detect_platforms
platforms = detect_platforms()
if platforms:
    print('  Detected: ' + ', '.join(platforms))
else:
    print('  No specific platforms detected - will use generic adapter')
"@
    try {
        $result = & $PythonCmd -c $DetectScript 2>$null
        if ($result) { Write-Host $result }
    } catch {
        Write-Info "Platform detection skipped."
    }

    # Initialize PRAXIS
    Write-Host ""
    Write-Info "Initializing PRAXIS..."

    $PushDir = Get-Location
    Set-Location $ProjectDir

    try {
        $CliPath = "$ScriptDir\collector\praxis_cli.py"
        & $PythonCmd $CliPath init --lang $Lang --dir $ProjectDir
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Initialization failed (exit code $LASTEXITCODE)."
            exit $LASTEXITCODE
        }
    } finally {
        Set-Location $PushDir
    }

    # Set up praxis command
    Write-Host ""
    Setup-PraxisCommand -PythonCmd $PythonCmd -ScriptDir $ScriptDir

    # Final instructions
    Write-Host ""
    Write-Sep
    Write-Host "  Installation complete!" -ForegroundColor Green
    Write-Sep
    Write-Host ""

    if ($Lang -eq "es") {
        Write-Info "PrÃ³ximos pasos:"
        Write-Info "  1. Completa la encuesta inicial:  praxis survey pre"
        Write-Info "  2. Registra tus tareas de IA:     praxis log 'lo que hiciste' -d <min> -m <modelo>"
        Write-Info "  3. Activa PRAXIS tras 7 dias:     praxis activate"
        Write-Info "  4. Verifica tu progreso:          praxis status"
    } else {
        Write-Info "Next steps:"
        Write-Info "  1. Complete the pre-survey:  praxis survey pre"
        Write-Info "  2. Log your AI tasks daily:  praxis log 'what you did' -d <min> -m <model>"
        Write-Info "  3. After 7+ days, activate:  praxis activate"
        Write-Info "  4. Check your progress:      praxis status"
    }
    Write-Host ""
}

function Setup-PraxisCommand {
    param([string]$PythonCmd, [string]$ScriptDir)

    $CliPath = "$ScriptDir\collector\praxis_cli.py"

    # Create a batch file in a scripts directory
    $ScriptsDir = "$env:USERPROFILE\.praxis-kit\bin"
    New-Item -ItemType Directory -Path $ScriptsDir -Force | Out-Null

    $WrapperPath = "$ScriptsDir\praxis.bat"
    $WrapperContent = "@echo off`r`n$PythonCmd `"$CliPath`" %*`r`n"
    Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding ASCII

    # Also create a PowerShell function file
    $PsWrapperPath = "$ScriptsDir\praxis.ps1"
    $PsContent = "& `"$PythonCmd`" `"$CliPath`" @args"
    Set-Content -Path $PsWrapperPath -Value $PsContent -Encoding UTF8

    # Add to user PATH if not already there
    $UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($UserPath -notlike "*$ScriptsDir*") {
        $NewPath = "$UserPath;$ScriptsDir"
        [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
        Write-Ok "Added $ScriptsDir to your user PATH"
        Write-Warn "Restart your terminal for 'praxis' command to work"
    } else {
        Write-Ok "Command 'praxis' installed to $ScriptsDir"
    }

    Write-Info "Or run directly: $PythonCmd `"$CliPath`" <command>"
}

# Run
Main


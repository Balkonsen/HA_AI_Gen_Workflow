#Requires -Version 5.1
<#
.SYNOPSIS
    Home Assistant AI Workflow - Windows 11 Automated Installer
    
.DESCRIPTION
    Fully automated installation script for Windows 11 that:
    - Checks and installs all dependencies
    - Creates Python virtual environment
    - Installs required packages
    - Configures the system
    - Creates desktop shortcuts
    - Optionally launches the GUI
    
.PARAMETER SkipPythonCheck
    Skip Python installation check (use if Python is already installed)
    
.PARAMETER SkipGitCheck
    Skip Git installation check
    
.PARAMETER NoShortcuts
    Don't create desktop shortcuts
    
.PARAMETER LaunchGUI
    Launch the Streamlit GUI after installation
    
.PARAMETER Unattended
    Run in unattended mode (no prompts)

.EXAMPLE
    .\install_windows.ps1
    
.EXAMPLE
    .\install_windows.ps1 -LaunchGUI -Unattended

.NOTES
    Author: HA AI Workflow Team
    Version: 2.0
    Date: January 2026
#>

[CmdletBinding()]
param(
    [switch]$SkipPythonCheck,
    [switch]$SkipGitCheck,
    [switch]$NoShortcuts,
    [switch]$LaunchGUI,
    [switch]$Unattended
)

# =============================================================================
# Configuration
# =============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$script:Config = @{
    AppName = "HA AI Workflow"
    Version = "2.0.0"
    MinPythonVersion = [version]"3.8.0"
    RecommendedPythonVersion = "3.11"
    VenvName = ".venv"
    RequirementsFile = "requirements-test.txt"
    GuiScript = "bin/workflow_gui.py"
    StreamlitPort = 8501
    LogFile = "install.log"
}

$script:Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Header = "Magenta"
}

# =============================================================================
# Utility Functions
# =============================================================================

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $script:Config.LogFile -Value $logEntry -ErrorAction SilentlyContinue
    
    switch ($Level) {
        "SUCCESS" { Write-Host "✅ $Message" -ForegroundColor $script:Colors.Success }
        "ERROR"   { Write-Host "❌ $Message" -ForegroundColor $script:Colors.Error }
        "WARNING" { Write-Host "⚠️  $Message" -ForegroundColor $script:Colors.Warning }
        "INFO"    { Write-Host "ℹ️  $Message" -ForegroundColor $script:Colors.Info }
        "HEADER"  { Write-Host "`n🔷 $Message" -ForegroundColor $script:Colors.Header }
        "STEP"    { Write-Host "   → $Message" -ForegroundColor "White" }
        default   { Write-Host $Message }
    }
}

function Show-Banner {
    $banner = @"

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     🏠 Home Assistant AI Workflow - Windows Installer v$($script:Config.Version)               ║
║                                                                              ║
║     Automated export, AI-powered development, and git-versioned import      ║
║     workflow for Home Assistant                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

"@
    Write-Host $banner -ForegroundColor Cyan
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Request-UserConfirmation {
    param([string]$Message)
    
    if ($Unattended) { return $true }
    
    $response = Read-Host "$Message (Y/n)"
    return ($response -eq "" -or $response -eq "Y" -or $response -eq "y")
}

function Get-ScriptDirectory {
    return $PSScriptRoot
}

# =============================================================================
# Dependency Checks
# =============================================================================

function Test-PythonInstallation {
    Write-Log "Checking Python installation..." -Level "HEADER"
    
    # Check multiple Python locations
    $pythonCommands = @("python", "python3", "py -3")
    $pythonPath = $null
    $pythonVersion = $null
    
    foreach ($cmd in $pythonCommands) {
        try {
            $cmdParts = $cmd -split " "
            $exe = $cmdParts[0]
            $args = if ($cmdParts.Length -gt 1) { $cmdParts[1..($cmdParts.Length-1)] + "--version" } else { @("--version") }
            
            $result = & $exe @args 2>&1
            if ($LASTEXITCODE -eq 0 -and $result -match "Python (\d+\.\d+\.\d+)") {
                $version = [version]$Matches[1]
                if ($version -ge $script:Config.MinPythonVersion) {
                    $pythonPath = $cmd
                    $pythonVersion = $version
                    break
                }
            }
        } catch {
            continue
        }
    }
    
    if ($pythonPath) {
        Write-Log "Found Python $pythonVersion ($pythonPath)" -Level "SUCCESS"
        return @{ Path = $pythonPath; Version = $pythonVersion }
    }
    
    Write-Log "Python $($script:Config.MinPythonVersion) or higher not found" -Level "WARNING"
    return $null
}

function Install-Python {
    Write-Log "Installing Python..." -Level "HEADER"
    
    # Check if winget is available
    $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
    
    if ($wingetAvailable) {
        Write-Log "Installing Python via winget..." -Level "STEP"
        try {
            winget install Python.Python.$($script:Config.RecommendedPythonVersion) --accept-package-agreements --accept-source-agreements
            
            # Refresh environment
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            Write-Log "Python installed successfully" -Level "SUCCESS"
            return $true
        } catch {
            Write-Log "Failed to install via winget: $_" -Level "ERROR"
        }
    }
    
    # Fallback: Download and install manually
    Write-Log "Downloading Python installer..." -Level "STEP"
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $installerPath = "$env:TEMP\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Log "Running Python installer (this may take a few minutes)..." -Level "STEP"
        
        $installArgs = @(
            "/quiet",
            "InstallAllUsers=0",
            "PrependPath=1",
            "Include_pip=1",
            "Include_test=0"
        )
        
        Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow
        
        # Refresh environment
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        # Clean up
        Remove-Item $installerPath -ErrorAction SilentlyContinue
        
        Write-Log "Python installed successfully" -Level "SUCCESS"
        return $true
    } catch {
        Write-Log "Failed to install Python: $_" -Level "ERROR"
        return $false
    }
}

function Test-GitInstallation {
    Write-Log "Checking Git installation..." -Level "HEADER"
    
    try {
        $gitVersion = git --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Found $gitVersion" -Level "SUCCESS"
            return $true
        }
    } catch {
        # Git not found
    }
    
    Write-Log "Git not found" -Level "WARNING"
    return $false
}

function Install-Git {
    Write-Log "Installing Git..." -Level "HEADER"
    
    $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
    
    if ($wingetAvailable) {
        Write-Log "Installing Git via winget..." -Level "STEP"
        try {
            winget install Git.Git --accept-package-agreements --accept-source-agreements
            
            # Refresh environment
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            Write-Log "Git installed successfully" -Level "SUCCESS"
            return $true
        } catch {
            Write-Log "Failed to install via winget: $_" -Level "ERROR"
        }
    }
    
    Write-Log "Please install Git manually from https://git-scm.com/download/win" -Level "WARNING"
    return $false
}

# =============================================================================
# Environment Setup
# =============================================================================

function New-VirtualEnvironment {
    param([string]$PythonPath)
    
    Write-Log "Creating Python virtual environment..." -Level "HEADER"
    
    $venvPath = Join-Path (Get-ScriptDirectory) $script:Config.VenvName
    
    # Remove existing venv if corrupted
    if (Test-Path $venvPath) {
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        if (-not (Test-Path $activateScript)) {
            Write-Log "Removing corrupted virtual environment..." -Level "STEP"
            Remove-Item $venvPath -Recurse -Force
        } else {
            Write-Log "Virtual environment already exists" -Level "SUCCESS"
            return $venvPath
        }
    }
    
    Write-Log "Creating new virtual environment at $venvPath..." -Level "STEP"
    
    try {
        $cmdParts = $PythonPath -split " "
        $exe = $cmdParts[0]
        $baseArgs = if ($cmdParts.Length -gt 1) { $cmdParts[1..($cmdParts.Length-1)] } else { @() }
        $args = $baseArgs + @("-m", "venv", $venvPath)
        
        & $exe @args
        
        if ($LASTEXITCODE -ne 0) {
            throw "venv creation failed with exit code $LASTEXITCODE"
        }
        
        Write-Log "Virtual environment created successfully" -Level "SUCCESS"
        return $venvPath
    } catch {
        Write-Log "Failed to create virtual environment: $_" -Level "ERROR"
        return $null
    }
}

function Install-Dependencies {
    param([string]$VenvPath)
    
    Write-Log "Installing Python dependencies..." -Level "HEADER"
    
    $pipPath = Join-Path $VenvPath "Scripts\pip.exe"
    $requirementsPath = Join-Path (Get-ScriptDirectory) $script:Config.RequirementsFile
    
    # Upgrade pip first
    Write-Log "Upgrading pip..." -Level "STEP"
    try {
        & $pipPath install --upgrade pip --quiet
    } catch {
        Write-Log "Warning: Could not upgrade pip" -Level "WARNING"
    }
    
    # Install from requirements file if exists
    if (Test-Path $requirementsPath) {
        Write-Log "Installing from $($script:Config.RequirementsFile)..." -Level "STEP"
        try {
            & $pipPath install -r $requirementsPath --quiet
            if ($LASTEXITCODE -ne 0) {
                throw "pip install failed"
            }
        } catch {
            Write-Log "Some packages may have failed, installing core packages..." -Level "WARNING"
        }
    }
    
    # Ensure core packages are installed
    $corePackages = @(
        "pyyaml",
        "paramiko",
        "cryptography",
        "streamlit",
        "watchdog"
    )
    
    Write-Log "Ensuring core packages are installed..." -Level "STEP"
    foreach ($package in $corePackages) {
        try {
            & $pipPath install $package --quiet 2>&1 | Out-Null
        } catch {
            Write-Log "Warning: Could not install $package" -Level "WARNING"
        }
    }
    
    Write-Log "Dependencies installed successfully" -Level "SUCCESS"
    return $true
}

# =============================================================================
# Configuration
# =============================================================================

function Initialize-Configuration {
    Write-Log "Initializing configuration..." -Level "HEADER"
    
    $scriptDir = Get-ScriptDirectory
    $configDir = Join-Path $scriptDir "config"
    $configTemplate = Join-Path $configDir "workflow_config.yaml.template"
    $configFile = Join-Path $configDir "workflow_config.yaml"
    
    # Create config directory if needed
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    # Create directories
    $directories = @(
        "exports",
        "imports",
        "secrets",
        "backups",
        "ai_context"
    )
    
    foreach ($dir in $directories) {
        $dirPath = Join-Path $scriptDir $dir
        if (-not (Test-Path $dirPath)) {
            New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
            Write-Log "Created directory: $dir" -Level "STEP"
        }
    }
    
    # Create config from template if not exists
    if (-not (Test-Path $configFile)) {
        if (Test-Path $configTemplate) {
            Copy-Item $configTemplate $configFile
            Write-Log "Created configuration file from template" -Level "STEP"
        } else {
            # Create minimal config
            $minimalConfig = @"
# HA AI Workflow Configuration
# Generated by Windows Installer

ssh:
  enabled: false
  host: "192.168.1.100"
  port: 22
  user: "root"
  auth_method: "key"
  key_path: "~/.ssh/id_rsa"
  remote_config_path: "/config"

paths:
  export_dir: "./exports"
  import_dir: "./imports"
  secrets_dir: "./secrets"
  backup_dir: "./backups"
  ai_context_dir: "./ai_context"

export:
  include_patterns:
    - "*.yaml"
    - "*.yml"
    - "*.json"
  exclude_patterns:
    - "secrets.yaml"
    - "*.log"
    - "*.db"

secrets:
  encryption_method: "fernet"
  label_prefix: "HA_SECRET"
  auto_restore: true

ai:
  context:
    include_entities: true
    include_devices: true
    max_size_kb: 500
"@
            Set-Content -Path $configFile -Value $minimalConfig
            Write-Log "Created minimal configuration file" -Level "STEP"
        }
    } else {
        Write-Log "Configuration file already exists" -Level "STEP"
    }
    
    # Create .gitignore for secrets
    $secretsGitignore = Join-Path $scriptDir "secrets\.gitignore"
    if (-not (Test-Path $secretsGitignore)) {
        Set-Content -Path $secretsGitignore -Value "*`n!.gitignore"
    }
    
    Write-Log "Configuration initialized successfully" -Level "SUCCESS"
    return $true
}

# =============================================================================
# Shortcuts and Launchers
# =============================================================================

function New-DesktopShortcuts {
    Write-Log "Creating desktop shortcuts..." -Level "HEADER"
    
    $scriptDir = Get-ScriptDirectory
    $venvPath = Join-Path $scriptDir $script:Config.VenvName
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    
    # Create launcher batch file
    $launcherContent = @"
@echo off
title HA AI Workflow GUI
cd /d "$scriptDir"
call "$venvPath\Scripts\activate.bat"
echo.
echo ========================================
echo   HA AI Workflow GUI
echo   Starting Streamlit server...
echo   URL: http://localhost:$($script:Config.StreamlitPort)
echo ========================================
echo.
streamlit run "$($script:Config.GuiScript)" --server.port $($script:Config.StreamlitPort) --server.headless true
pause
"@
    
    $launcherPath = Join-Path $scriptDir "Start-HA-AI-Workflow.bat"
    Set-Content -Path $launcherPath -Value $launcherContent
    Write-Log "Created launcher script: Start-HA-AI-Workflow.bat" -Level "STEP"
    
    # Create CLI launcher
    $cliLauncherContent = @"
@echo off
title HA AI Workflow CLI
cd /d "$scriptDir"
call "$venvPath\Scripts\activate.bat"
echo.
echo ========================================
echo   HA AI Workflow CLI
echo   Virtual environment activated
echo ========================================
echo.
echo Available commands:
echo   python bin\workflow_orchestrator.py setup
echo   python bin\workflow_orchestrator.py export --source [path]
echo   python bin\workflow_orchestrator.py import --source [path]
echo   python bin\workflow_orchestrator.py full --source [path]
echo.
cmd /k
"@
    
    $cliLauncherPath = Join-Path $scriptDir "Start-HA-AI-CLI.bat"
    Set-Content -Path $cliLauncherPath -Value $cliLauncherContent
    Write-Log "Created CLI launcher: Start-HA-AI-CLI.bat" -Level "STEP"
    
    if (-not $NoShortcuts) {
        # Create desktop shortcut for GUI
        try {
            $WshShell = New-Object -ComObject WScript.Shell
            
            # GUI Shortcut
            $guiShortcut = $WshShell.CreateShortcut("$desktopPath\HA AI Workflow GUI.lnk")
            $guiShortcut.TargetPath = $launcherPath
            $guiShortcut.WorkingDirectory = $scriptDir
            $guiShortcut.Description = "Launch HA AI Workflow GUI"
            $guiShortcut.IconLocation = "shell32.dll,21"
            $guiShortcut.Save()
            Write-Log "Created desktop shortcut: HA AI Workflow GUI" -Level "STEP"
            
            # CLI Shortcut
            $cliShortcut = $WshShell.CreateShortcut("$desktopPath\HA AI Workflow CLI.lnk")
            $cliShortcut.TargetPath = $cliLauncherPath
            $cliShortcut.WorkingDirectory = $scriptDir
            $cliShortcut.Description = "Launch HA AI Workflow CLI"
            $cliShortcut.IconLocation = "shell32.dll,22"
            $cliShortcut.Save()
            Write-Log "Created desktop shortcut: HA AI Workflow CLI" -Level "STEP"
            
        } catch {
            Write-Log "Could not create desktop shortcuts: $_" -Level "WARNING"
        }
    }
    
    Write-Log "Shortcuts created successfully" -Level "SUCCESS"
    return $launcherPath
}

# =============================================================================
# Verification
# =============================================================================

function Test-Installation {
    Write-Log "Verifying installation..." -Level "HEADER"
    
    $scriptDir = Get-ScriptDirectory
    $venvPath = Join-Path $scriptDir $script:Config.VenvName
    $pythonPath = Join-Path $venvPath "Scripts\python.exe"
    $errors = @()
    
    # Check Python in venv
    if (-not (Test-Path $pythonPath)) {
        $errors += "Python not found in virtual environment"
    }
    
    # Check required packages
    $requiredPackages = @("yaml", "paramiko", "cryptography", "streamlit")
    foreach ($package in $requiredPackages) {
        try {
            $result = & $pythonPath -c "import $package" 2>&1
            if ($LASTEXITCODE -ne 0) {
                $errors += "Package '$package' not properly installed"
            }
        } catch {
            $errors += "Package '$package' not properly installed"
        }
    }
    
    # Check main scripts exist
    $requiredScripts = @(
        "bin/workflow_orchestrator.py",
        "bin/workflow_gui.py",
        "bin/ha_diagnostic_export.py"
    )
    foreach ($script in $requiredScripts) {
        $scriptPath = Join-Path $scriptDir $script
        if (-not (Test-Path $scriptPath)) {
            $errors += "Required script not found: $script"
        }
    }
    
    # Check config
    $configPath = Join-Path $scriptDir "config/workflow_config.yaml"
    if (-not (Test-Path $configPath)) {
        $errors += "Configuration file not found"
    }
    
    if ($errors.Count -gt 0) {
        Write-Log "Installation verification failed:" -Level "ERROR"
        foreach ($error in $errors) {
            Write-Log "  - $error" -Level "ERROR"
        }
        return $false
    }
    
    Write-Log "Installation verified successfully" -Level "SUCCESS"
    return $true
}

# =============================================================================
# GUI Launch
# =============================================================================

function Start-GUI {
    param([string]$LauncherPath)
    
    Write-Log "Starting GUI..." -Level "HEADER"
    
    if (Test-Path $LauncherPath) {
        Start-Process -FilePath $LauncherPath
        
        # Wait a moment for startup
        Start-Sleep -Seconds 3
        
        # Open browser
        $url = "http://localhost:$($script:Config.StreamlitPort)"
        Write-Log "Opening browser at $url..." -Level "STEP"
        Start-Process $url
        
        Write-Log "GUI started successfully" -Level "SUCCESS"
    } else {
        Write-Log "Launcher not found at $LauncherPath" -Level "ERROR"
    }
}

# =============================================================================
# Main Installation Flow
# =============================================================================

function Start-Installation {
    Show-Banner
    
    $startTime = Get-Date
    Write-Log "Installation started at $startTime" -Level "INFO"
    Write-Log "Script directory: $(Get-ScriptDirectory)" -Level "INFO"
    
    # Check if running as admin (not required, but note it)
    if (Test-Administrator) {
        Write-Log "Running with administrator privileges" -Level "INFO"
    } else {
        Write-Log "Running without administrator privileges (some features may be limited)" -Level "INFO"
    }
    
    # Step 1: Check/Install Python
    if (-not $SkipPythonCheck) {
        $pythonInfo = Test-PythonInstallation
        
        if (-not $pythonInfo) {
            if (Request-UserConfirmation "Python not found. Would you like to install it?") {
                if (-not (Install-Python)) {
                    Write-Log "Python installation failed. Please install Python manually." -Level "ERROR"
                    return $false
                }
                $pythonInfo = Test-PythonInstallation
                if (-not $pythonInfo) {
                    Write-Log "Python still not detected. Please restart PowerShell and run this script again." -Level "ERROR"
                    return $false
                }
            } else {
                Write-Log "Python is required. Installation cancelled." -Level "ERROR"
                return $false
            }
        }
    } else {
        $pythonInfo = Test-PythonInstallation
        if (-not $pythonInfo) {
            Write-Log "Python check skipped but Python not found!" -Level "ERROR"
            return $false
        }
    }
    
    # Step 2: Check/Install Git (optional but recommended)
    if (-not $SkipGitCheck) {
        if (-not (Test-GitInstallation)) {
            if (Request-UserConfirmation "Git not found. Would you like to install it? (Recommended for version control)") {
                Install-Git
            } else {
                Write-Log "Continuing without Git (version control will be limited)" -Level "WARNING"
            }
        }
    }
    
    # Step 3: Create Virtual Environment
    $venvPath = New-VirtualEnvironment -PythonPath $pythonInfo.Path
    if (-not $venvPath) {
        Write-Log "Failed to create virtual environment" -Level "ERROR"
        return $false
    }
    
    # Step 4: Install Dependencies
    if (-not (Install-Dependencies -VenvPath $venvPath)) {
        Write-Log "Failed to install dependencies" -Level "ERROR"
        return $false
    }
    
    # Step 5: Initialize Configuration
    if (-not (Initialize-Configuration)) {
        Write-Log "Failed to initialize configuration" -Level "ERROR"
        return $false
    }
    
    # Step 6: Create Shortcuts
    $launcherPath = New-DesktopShortcuts
    
    # Step 7: Verify Installation
    if (-not (Test-Installation)) {
        Write-Log "Installation verification failed" -Level "ERROR"
        return $false
    }
    
    # Calculate duration
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    # Success message
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                                                                              ║" -ForegroundColor Green
    Write-Host "║     ✅ Installation Complete!                                                ║" -ForegroundColor Green
    Write-Host "║                                                                              ║" -ForegroundColor Green
    Write-Host "║     Duration: $($duration.ToString('mm\:ss'))                                                          ║" -ForegroundColor Green
    Write-Host "║                                                                              ║" -ForegroundColor Green
    Write-Host "║     Quick Start:                                                             ║" -ForegroundColor Green
    Write-Host "║     • Double-click 'HA AI Workflow GUI' on desktop                          ║" -ForegroundColor Green
    Write-Host "║     • Or run: .\Start-HA-AI-Workflow.bat                                    ║" -ForegroundColor Green
    Write-Host "║     • CLI: .\Start-HA-AI-CLI.bat                                            ║" -ForegroundColor Green
    Write-Host "║                                                                              ║" -ForegroundColor Green
    Write-Host "║     Documentation: docs/COMPLETE_DOCUMENTATION.md                           ║" -ForegroundColor Green
    Write-Host "║                                                                              ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    
    # Step 8: Optionally launch GUI
    if ($LaunchGUI) {
        Start-GUI -LauncherPath $launcherPath
    } elseif (-not $Unattended) {
        if (Request-UserConfirmation "Would you like to launch the GUI now?") {
            Start-GUI -LauncherPath $launcherPath
        }
    }
    
    return $true
}

# =============================================================================
# Entry Point
# =============================================================================

try {
    $result = Start-Installation
    if ($result) {
        exit 0
    } else {
        exit 1
    }
} catch {
    Write-Log "Installation failed with error: $_" -Level "ERROR"
    Write-Log $_.ScriptStackTrace -Level "ERROR"
    exit 1
}

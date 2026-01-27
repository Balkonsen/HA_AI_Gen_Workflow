###############################################################################
# Home Assistant AI Workflow - Windows Installer
# One-time setup for the complete workflow system on Windows
###############################################################################

#Requires -Version 5.1

# Set strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Script configuration
$INSTALL_DIR = "$env:ProgramFiles\HA-AI-Workflow"
$CONFIG_DIR = "$env:USERPROFILE\ha-config"
$LOG_FILE = "$env:TEMP\ha-ai-workflow-install.log"
$SCRIPT_DIR = $PSScriptRoot

# Initialize log file
"Installation started at $(Get-Date)" | Out-File -FilePath $LOG_FILE -Encoding UTF8

###############################################################################
# Logging Functions
###############################################################################

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to log file
    $logMessage | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
    
    # Write to console with color
    switch ($Level) {
        "INFO" {
            Write-Host "ℹ " -NoNewline -ForegroundColor Blue
            Write-Host $Message
        }
        "SUCCESS" {
            Write-Host "✓ " -NoNewline -ForegroundColor Green
            Write-Host $Message
        }
        "WARNING" {
            Write-Host "⚠ " -NoNewline -ForegroundColor Yellow
            Write-Host $Message
        }
        "ERROR" {
            Write-Host "✗ " -NoNewline -ForegroundColor Red
            Write-Host $Message
        }
    }
}

function Write-Banner {
    param([string]$Message)
    
    Write-Host ""
    Write-Host ("=" * 76) -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host ("=" * 76) -ForegroundColor Cyan
    Write-Host ""
}

###############################################################################
# Helper Functions
###############################################################################

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandExists {
    param([string]$Command)
    
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

function New-DirectoryIfNotExists {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Log "Created directory: $Path" -Level "INFO"
    }
}

###############################################################################
# Installation Steps
###############################################################################

function Start-Installation {
    Write-Banner "Home Assistant AI Workflow - Windows Installer"
    
    Write-Host "Starting installation..." -ForegroundColor White
    Write-Host ""
    Write-Host "Installation directory: $INSTALL_DIR" -ForegroundColor Gray
    Write-Host "Configuration directory: $CONFIG_DIR" -ForegroundColor Gray
    Write-Host "Log file: $LOG_FILE" -ForegroundColor Gray
    Write-Host ""
    
    # Check administrator privileges
    if (-not (Test-Administrator)) {
        Write-Log "Administrator privileges required" -Level "ERROR"
        Write-Host ""
        Write-Host "Please run this script as Administrator:" -ForegroundColor Red
        Write-Host "  Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
    
    Write-Log "Starting installation as Administrator" -Level "INFO"
}

function Install-DirectoryStructure {
    Write-Log "Step 1/7: Creating directory structure..." -Level "INFO"
    
    try {
        # Create installation directories
        New-DirectoryIfNotExists -Path "$INSTALL_DIR\bin"
        New-DirectoryIfNotExists -Path "$INSTALL_DIR\docs"
        New-DirectoryIfNotExists -Path "$INSTALL_DIR\templates"
        
        # Create config directories
        New-DirectoryIfNotExists -Path "$CONFIG_DIR\ai_exports\secrets"
        New-DirectoryIfNotExists -Path "$CONFIG_DIR\ai_exports\archives"
        New-DirectoryIfNotExists -Path "$CONFIG_DIR\ai_imports\pending"
        
        Write-Log "Directory structure created successfully" -Level "SUCCESS"
    }
    catch {
        Write-Log "Failed to create directory structure: $_" -Level "ERROR"
        Write-Log $_.ScriptStackTrace -Level "ERROR"
        throw
    }
}

function Test-Dependencies {
    Write-Log "Step 2/7: Checking dependencies..." -Level "INFO"
    
    $missingDeps = @()
    
    # Check Python
    if (-not (Test-CommandExists "python")) {
        if (-not (Test-CommandExists "python3")) {
            $missingDeps += "Python 3.8+"
        }
    }
    
    # Check Git
    if (-not (Test-CommandExists "git")) {
        $missingDeps += "Git"
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Log "Missing dependencies: $($missingDeps -join ', ')" -Level "ERROR"
        Write-Host ""
        Write-Host "Please install the following:" -ForegroundColor Red
        foreach ($dep in $missingDeps) {
            Write-Host "  - $dep" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "Download from:" -ForegroundColor Gray
        Write-Host "  Python: https://www.python.org/downloads/" -ForegroundColor Gray
        Write-Host "  Git: https://git-scm.com/download/win" -ForegroundColor Gray
        Write-Host ""
        throw "Missing required dependencies"
    }
    
    Write-Log "All dependencies are installed" -Level "SUCCESS"
}

function Install-PythonPackages {
    Write-Log "Step 3/7: Installing Python packages..." -Level "INFO"
    
    try {
        # Determine python command
        $pythonCmd = if (Test-CommandExists "python") { "python" } else { "python3" }
        
        # Check if PyYAML is installed
        $yamlCheck = & $pythonCmd -c "import yaml" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "PyYAML already installed" -Level "SUCCESS"
        }
        else {
            Write-Log "Installing PyYAML..." -Level "INFO"
            & $pythonCmd -m pip install pyyaml --user
            if ($LASTEXITCODE -eq 0) {
                Write-Log "PyYAML installed successfully" -Level "SUCCESS"
            }
            else {
                Write-Log "Failed to install PyYAML" -Level "WARNING"
                Write-Host "  You may need to install it manually: pip install pyyaml" -ForegroundColor Yellow
            }
        }
        
        # Install requirements if file exists
        $requirementsFile = Join-Path $SCRIPT_DIR "requirements.txt"
        
        if (Test-Path $requirementsFile) {
            Write-Log "Installing requirements from requirements.txt..." -Level "INFO"
            & $pythonCmd -m pip install -r $requirementsFile --user
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Requirements installed successfully" -Level "SUCCESS"
            }
            else {
                Write-Log "Some requirements failed to install" -Level "WARNING"
            }
        }
    }
    catch {
        Write-Log "Error during Python package installation: $_" -Level "ERROR"
        Write-Log $_.ScriptStackTrace -Level "ERROR"
        throw
    }
}

function Install-Scripts {
    Write-Log "Step 4/7: Installing Python scripts..." -Level "INFO"
    
    try {
        # List of scripts to install
        $scripts = @(
            "ha_diagnostic_export.py",
            "ha_ai_context_gen.py",
            "ha_config_import.py",
            "ha_export_verifier.py",
            "secrets_manager.py",
            "ssh_transfer.py",
            "ssh_transfer_enhanced.py",
            "ssh_transfer_password.py",
            "workflow_config.py",
            "workflow_gui.py",
            "workflow_orchestrator.py"
        )
        
        $installedCount = 0
        foreach ($script in $scripts) {
            $sourcePath = $null
            
            # Check in current directory
            if (Test-Path (Join-Path $SCRIPT_DIR $script)) {
                $sourcePath = Join-Path $SCRIPT_DIR $script
            }
            # Check in bin subdirectory
            elseif (Test-Path (Join-Path $SCRIPT_DIR "bin\$script")) {
                $sourcePath = Join-Path $SCRIPT_DIR "bin\$script"
            }
            
            if ($sourcePath) {
                $destPath = Join-Path "$INSTALL_DIR\bin" $script
                Copy-Item -Path $sourcePath -Destination $destPath -Force
                Write-Log "Installed: $script" -Level "SUCCESS"
                $installedCount++
            }
            else {
                Write-Log "Script not found: $script (skipping)" -Level "WARNING"
            }
        }
        
        Write-Log "Installed $installedCount scripts" -Level "SUCCESS"
    }
    catch {
        Write-Log "Error during script installation: $_" -Level "ERROR"
        Write-Log $_.ScriptStackTrace -Level "ERROR"
        throw
    }
}

function Install-MasterScript {
    Write-Log "Step 5/7: Installing master script..." -Level "INFO"
    
    try {
        $masterScriptSh = Join-Path $SCRIPT_DIR "ha_ai_master_script.sh"
        
        # For Windows, create a PowerShell wrapper instead
        $wrapperContent = @"
# HA AI Workflow - Windows Wrapper
`$INSTALL_DIR = "$INSTALL_DIR"
`$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }

# Determine which script to run
`$orchestrator = Join-Path `$INSTALL_DIR "bin\workflow_orchestrator.py"

if (Test-Path `$orchestrator) {
    & `$pythonCmd `$orchestrator `$args
} else {
    Write-Host "Error: Orchestrator script not found at `$orchestrator" -ForegroundColor Red
    exit 1
}
"@
        
        $wrapperPath = Join-Path $INSTALL_DIR "ha-ai-workflow.ps1"
        $wrapperContent | Out-File -FilePath $wrapperPath -Encoding UTF8
        
        Write-Log "Master script wrapper created" -Level "SUCCESS"
        
        # Add to PATH if not already there
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -notlike "*$INSTALL_DIR*") {
            Write-Log "Adding installation directory to user PATH..." -Level "INFO"
            Write-Log "Backing up current PATH to log file..." -Level "INFO"
            "PATH Backup: $currentPath" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
            [Environment]::SetEnvironmentVariable(
                "Path",
                "$currentPath;$INSTALL_DIR",
                "User"
            )
            Write-Log "Installation directory added to PATH" -Level "SUCCESS"
            Write-Log "Please restart your terminal for PATH changes to take effect" -Level "INFO"
        }
    }
    catch {
        Write-Log "Error during master script installation: $_" -Level "ERROR"
        Write-Log $_.ScriptStackTrace -Level "ERROR"
        throw
    }
}

function Initialize-GitRepository {
    Write-Log "Step 6/7: Initializing Git repository..." -Level "INFO"
    
    try {
        Push-Location $CONFIG_DIR -ErrorAction Stop
        
        if (Test-Path ".git") {
            Write-Log "Git repository already exists" -Level "INFO"
        }
        else {
            # Initialize git repository
            git config --global init.defaultBranch main 2>$null
            git init 2>$null
            if ($LASTEXITCODE -ne 0) {
                throw "Git init failed"
            }
            
            # Create .gitignore
            $gitignoreContent = @"
# Home Assistant
*.db
*.db-shm
*.db-wal
*.log
home-assistant.log*
home-assistant_v2.db*
.cloud
.storage
deps/
tts/
__pycache__/
*.pyc

# AI Workflow
ai_exports/archives/
ai_exports/secrets/
ai_imports/pending/
*.tar.gz
debug_report_*.md

# System
.DS_Store
*.swp
*.swo
*~
Thumbs.db
desktop.ini
"@
            
            $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
            
            git add .gitignore
            git commit -m "Initial commit: HA AI Workflow setup" 2>$null
            
            Write-Log "Git repository initialized" -Level "SUCCESS"
        }
    }
    catch {
        Write-Log "Error during Git initialization: $_" -Level "WARNING"
        Write-Log "You may need to initialize Git manually" -Level "INFO"
    }
    finally {
        Pop-Location
    }
}

function Install-Documentation {
    Write-Log "Step 7/7: Creating documentation..." -Level "INFO"
    
    try {
        # Create QUICKSTART.md
        $quickstartContent = @"
# Quick Start Guide - Windows

## First Export

```powershell
ha-ai-workflow.ps1 export
```

This will:
1. Export your HA configuration
2. Generate AI-friendly context
3. Create secrets backup
4. Commit to git

## Working with AI

1. Find the generated prompt:
   ```powershell
   Get-Content `$env:USERPROFILE\ha-config\ai_exports\ha_export_*\AI_PROMPT.md
   ```

2. Share with AI assistant (exclude secrets!)

3. Place AI-generated files in:
   ```powershell
   `$env:USERPROFILE\ha-config\ai_imports\pending\
   ```

## Import AI Changes

```powershell
ha-ai-workflow.ps1 import
```

This will:
1. Scan for new files
2. Create git branch
3. Validate configuration
4. Merge and deploy

## Check Status

```powershell
ha-ai-workflow.ps1 status
```

## Automated Mode

```powershell
ha-ai-workflow.ps1 export --auto
ha-ai-workflow.ps1 import --auto
```
"@
        
        $quickstartPath = Join-Path "$INSTALL_DIR\docs" "QUICKSTART.md"
        $quickstartContent | Out-File -FilePath $quickstartPath -Encoding UTF8
        
        # Create TROUBLESHOOTING.md
        $troubleshootingContent = @"
# Troubleshooting Guide - Windows

## Export Issues

### Python Not Found
Install Python from: https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation.

### PyYAML Not Found
```powershell
python -m pip install pyyaml --user
```

### Permission Denied
Run PowerShell as Administrator:
Right-click PowerShell -> Run as Administrator

### Out of Space
```powershell
# Clean old archives
Remove-Item -Path `$env:USERPROFILE\ha-config\ai_exports\archives\* -Recurse -Force
```

## Import Issues

### Validation Failed
Check the debug report:
```powershell
Get-Content `$env:USERPROFILE\ha-config\ai_exports\debug_report_*.md
```

### Git Conflicts
```powershell
cd `$env:USERPROFILE\ha-config
git status
git stash
ha-ai-workflow.ps1 import
```

### Rollback Changes
```powershell
cd `$env:USERPROFILE\ha-config
git log --oneline
git checkout <commit-hash>
# Restart Home Assistant
```

## Common Problems

### "No files to import"
Make sure files are in: `$env:USERPROFILE\ha-config\ai_imports\pending\

### "Secrets file not found"
Run export first: ha-ai-workflow.ps1 export

### Configuration check fails
Review errors and validate your YAML syntax

## Getting Help

1. Check logs: `$env:USERPROFILE\ha-config\ai_exports\workflow.log
2. Generate debug report
3. Share with AI (exclude secrets!)
"@
        
        $troubleshootingPath = Join-Path "$INSTALL_DIR\docs" "TROUBLESHOOTING.md"
        $troubleshootingContent | Out-File -FilePath $troubleshootingPath -Encoding UTF8
        
        Write-Log "Documentation created successfully" -Level "SUCCESS"
    }
    catch {
        Write-Log "Error creating documentation: $_" -Level "WARNING"
    }
}

function Show-CompletionSummary {
    Write-Banner "Setup Complete!"
    
    Write-Host ""
    Write-Host "✓ " -NoNewline -ForegroundColor Green
    Write-Host "Installation successful!" -ForegroundColor White
    Write-Host ""
    Write-Host "📁 Installation directory: " -NoNewline -ForegroundColor Gray
    Write-Host $INSTALL_DIR -ForegroundColor White
    Write-Host "📁 Configuration directory: " -NoNewline -ForegroundColor Gray
    Write-Host $CONFIG_DIR -ForegroundColor White
    Write-Host "🔧 Command: " -NoNewline -ForegroundColor Gray
    Write-Host "ha-ai-workflow.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 Documentation:" -ForegroundColor Cyan
    Write-Host "   Quick Start: " -NoNewline -ForegroundColor Gray
    Write-Host "$INSTALL_DIR\docs\QUICKSTART.md" -ForegroundColor White
    Write-Host "   Troubleshooting: " -NoNewline -ForegroundColor Gray
    Write-Host "$INSTALL_DIR\docs\TROUBLESHOOTING.md" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   1. " -NoNewline -ForegroundColor Yellow
    Write-Host "Restart your terminal to update PATH"
    Write-Host ""
    Write-Host "   2. " -NoNewline -ForegroundColor Yellow
    Write-Host "Run your first export:"
    Write-Host "      ha-ai-workflow.ps1 export" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. " -NoNewline -ForegroundColor Yellow
    Write-Host "Review the AI prompt:"
    Write-Host "      Get-Content `$env:USERPROFILE\ha-config\ai_exports\ha_export_*\AI_PROMPT.md" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   4. " -NoNewline -ForegroundColor Yellow
    Write-Host "Share with AI and get help!"
    Write-Host ""
    Write-Host "   5. " -NoNewline -ForegroundColor Yellow
    Write-Host "Place AI files in `$env:USERPROFILE\ha-config\ai_imports\pending\"
    Write-Host ""
    Write-Host "   6. " -NoNewline -ForegroundColor Yellow
    Write-Host "Import changes:"
    Write-Host "      ha-ai-workflow.ps1 import" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Pro tip: " -NoNewline -ForegroundColor Blue
    Write-Host "Use ha-ai-workflow.ps1 --help for all options"
    Write-Host ""
    Write-Host "📋 Log file: " -NoNewline -ForegroundColor Gray
    Write-Host $LOG_FILE -ForegroundColor White
    Write-Host ""
}

###############################################################################
# Main Installation Process
###############################################################################

try {
    Start-Installation
    Install-DirectoryStructure
    Test-Dependencies
    Install-PythonPackages
    Install-Scripts
    Install-MasterScript
    Initialize-GitRepository
    Install-Documentation
    Show-CompletionSummary
    
    Write-Log "Installation completed successfully" -Level "SUCCESS"
    exit 0
}
catch {
    Write-Host ""
    Write-Host "Installation encountered errors. Please check the log file." -ForegroundColor Red
    Write-Host "Log file: $LOG_FILE" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host ""
    
    Write-Log "Installation failed: $($_.Exception.Message)" -Level "ERROR"
    Write-Log $_.ScriptStackTrace -Level "ERROR"
    
    Read-Host "Press Enter to continue..."
    exit 1
}

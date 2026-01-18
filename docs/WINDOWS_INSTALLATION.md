# Home Assistant AI Workflow - Windows 11 Installation Guide

## Quick Install (Recommended)

**Simply double-click `Install-Windows.bat`** - The installer handles everything automatically!

Or run from PowerShell:

```powershell
.\install_windows.ps1
```

---

## What the Installer Does

### 1. Dependency Checks

- ✅ Verifies Python 3.8+ installation
- ✅ Verifies Git installation (optional)
- ✅ Offers to auto-install missing dependencies via `winget`

### 2. Environment Setup

- ✅ Creates isolated Python virtual environment (`.venv`)
- ✅ Installs all required Python packages
- ✅ Creates required directories (`exports/`, `imports/`, `secrets/`, etc.)

### 3. Configuration

- ✅ Generates configuration file from template
- ✅ Sets up secrets directory with `.gitignore`
- ✅ Creates default workflow settings

### 4. Launchers & Shortcuts

- ✅ Creates `Start-HA-AI-Workflow.bat` (GUI launcher)
- ✅ Creates `Start-HA-AI-CLI.bat` (CLI launcher)
- ✅ Creates desktop shortcuts for easy access

### 5. Verification

- ✅ Validates all components are properly installed
- ✅ Tests Python packages can be imported
- ✅ Verifies configuration files exist

---

## Installation Options

### Basic Installation

```powershell
.\install_windows.ps1
```

### Install and Launch GUI

```powershell
.\install_windows.ps1 -LaunchGUI
```

### Unattended Installation (No Prompts)

```powershell
.\install_windows.ps1 -Unattended
```

### Full Unattended with GUI Launch

```powershell
.\install_windows.ps1 -Unattended -LaunchGUI
```

### Skip Dependency Checks

```powershell
.\install_windows.ps1 -SkipPythonCheck -SkipGitCheck
```

### Skip Desktop Shortcuts

```powershell
.\install_windows.ps1 -NoShortcuts
```

---

## After Installation

### Starting the GUI

1. **Desktop shortcut**: Double-click "HA AI Workflow GUI"
2. **Batch file**: Double-click `Start-HA-AI-Workflow.bat`
3. **Browser**: Navigate to http://localhost:8501

### Using the CLI

1. **Desktop shortcut**: Double-click "HA AI Workflow CLI"
2. **Batch file**: Double-click `Start-HA-AI-CLI.bat`
3. **Commands**:
   ```bash
   python bin\workflow_orchestrator.py setup
   python bin\workflow_orchestrator.py export --source C:\path\to\ha\config
   python bin\workflow_orchestrator.py full --remote
   ```

---

## Requirements

| Requirement | Minimum    | Recommended |
| ----------- | ---------- | ----------- |
| Windows     | 10 (1809+) | 11          |
| PowerShell  | 5.1        | 7.x         |
| Python      | 3.8        | 3.11        |
| RAM         | 2 GB       | 4 GB        |
| Disk Space  | 500 MB     | 1 GB        |

---

## Troubleshooting

### "Execution Policy" Error

If PowerShell blocks the script:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or use the batch file which bypasses this automatically.

### Python Not Found After Install

Restart PowerShell to refresh environment variables:

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
```

### Package Installation Fails

Try installing manually:

```powershell
.\.venv\Scripts\pip.exe install pyyaml paramiko cryptography streamlit
```

### GUI Won't Start

Check if port 8501 is in use:

```powershell
netstat -ano | findstr :8501
```

Kill the process or use a different port:

```powershell
streamlit run bin\workflow_gui.py --server.port 8502
```

### Virtual Environment Issues

Delete and recreate:

```powershell
Remove-Item -Recurse -Force .venv
.\install_windows.ps1 -SkipPythonCheck
```

---

## File Structure After Installation

```
HA_AI_Gen_Workflow/
├── .venv/                      # Python virtual environment
├── Install-Windows.bat         # Quick installer (double-click)
├── install_windows.ps1         # PowerShell installer
├── Start-HA-AI-Workflow.bat    # GUI launcher
├── Start-HA-AI-CLI.bat         # CLI launcher
├── config/
│   └── workflow_config.yaml    # Your configuration
├── exports/                    # Export output directory
├── imports/                    # Import source directory
├── secrets/                    # Encrypted secrets storage
├── backups/                    # Backup directory
├── ai_context/                 # AI context output
└── bin/                        # Python scripts
```

---

## Updating

To update to the latest version:

```powershell
git pull origin main
.\install_windows.ps1 -SkipPythonCheck
```

---

## Uninstalling

1. Delete the `HA_AI_Gen_Workflow` folder
2. Remove desktop shortcuts manually
3. (Optional) Uninstall Python if no longer needed

---

## Support

- **Documentation**: [docs/COMPLETE_DOCUMENTATION.md](docs/COMPLETE_DOCUMENTATION.md)
- **Issues**: https://github.com/Balkonsen/HA_AI_Gen_Workflow/issues

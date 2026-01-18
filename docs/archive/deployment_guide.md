# Home Assistant AI Workflow - Complete Deployment Guide

## 📦 Complete System Overview

This is a production-ready, automated workflow system for Home Assistant configuration management with AI assistance.

## 🎯 What You're Getting

### Core Components

1. **ha_ai_master.sh** - Main orchestrator
   - Automated export/import workflows
   - Git version control
   - Dependency management
   - Error handling and logging

2. **Python Scripts** (in `bin/`)
   - `ha_diagnostic_export.py` - Configuration export with sanitization
   - `ha_ai_context_gen.py` - AI context generator
   - `ha_config_import.py` - Configuration import with secret restoration
   - `ha_export_verifier.py` - Export validation

3. **Setup System**
   - `setup.sh` - One-time installation
   - Automatic dependency handling
   - Git initialization
   - Directory structure creation

4. **Documentation**
   - Complete README
   - Quick start guide
   - Troubleshooting guide
   - Contributing guidelines

## 🚀 Installation Steps

### Step 1: Prepare Files

Create this directory structure on your local machine:

```
ha-ai-workflow/
├── ha_ai_master.sh
├── setup.sh
├── README.md
├── LICENSE
├── bin/
│   ├── ha_diagnostic_export.py
│   ├── ha_ai_context_gen.py
│   ├── ha_config_import.py
│   └── ha_export_verifier.py
└── docs/
    ├── QUICKSTART.md
    └── TROUBLESHOOTING.md
```

### Step 2: Package for Transfer

```bash
# On your local machine
tar -czf ha-ai-workflow.tar.gz ha-ai-workflow/
```

### Step 3: Upload to Home Assistant

```bash
# Upload via SCP
scp ha-ai-workflow.tar.gz root@homeassistant.local:/tmp/

# Or use the web terminal to download
# In HA web terminal:
cd /tmp
wget https://your-server.com/ha-ai-workflow.tar.gz
```

### Step 4: Extract and Install

```bash
# SSH into Home Assistant
ssh root@homeassistant.local

# Extract
cd /tmp
tar -xzf ha-ai-workflow.tar.gz
cd ha-ai-workflow

# Run setup
./setup.sh
```

**Setup will:**
- ✅ Check dependencies
- ✅ Install PyYAML
- ✅ Install all scripts
- ✅ Create symlink: `/usr/local/bin/ha-ai-workflow`
- ✅ Initialize git repository
- ✅ Create directory structure

### Step 5: Verify Installation

```bash
# Test command is available
ha-ai-workflow --help

# Check version
ha-ai-workflow status
```

## 📋 First Use Workflow

### 1. Initial Export

```bash
# Run your first export
ha-ai-workflow export
```

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════════╗
║       Home Assistant AI Workflow Automation System            ║
║                  Version 1.0.0                                ║
╚═══════════════════════════════════════════════════════════════╝

ℹ Checking dependencies...
✓ Core dependencies OK
ℹ Checking PyYAML installation...
✓ PyYAML already installed

═══════════════════════════════════════════════════════════════════
  Starting Export Workflow
═══════════════════════════════════════════════════════════════════

ℹ Step 1/5: Running diagnostic export...
✓ Export completed

ℹ Step 2/5: Verifying export completeness...
✓ Export verified

ℹ Step 3/5: Extracting export...
✓ Extracted to /config/ai_exports/ha_export_20260113_120000

ℹ Step 4/5: Generating AI context...
✓ AI context generated

ℹ Step 5/5: Managing secrets...
✓ Secrets backed up (keeping last 5 versions)

═══════════════════════════════════════════════════════════════════
  Export Workflow Complete
═══════════════════════════════════════════════════════════════════

✓ Export Location: /config/ai_exports/ha_export_20260113_120000
✓ AI Prompt: /config/ai_exports/ha_export_20260113_120000/AI_PROMPT.md
✓ AI Context: /config/ai_exports/ha_export_20260113_120000/AI_CONTEXT.json
✓ Secrets: /config/ai_exports/secrets/secrets_map_latest.json

ℹ Next Steps:
  1. Review AI_PROMPT.md
  2. Share with AI assistant (DO NOT share secrets!)
  3. Place AI-generated files in: /config/ai_imports/pending
  4. Run: ha-ai-workflow import
```

### 2. Review AI Prompt

```bash
# View the generated prompt
cat /config/ai_exports/ha_export_*/AI_PROMPT.md
```

**Example Content:**
```markdown
# Home Assistant Configuration Context

## System Overview
- **Total Integrations**: 32
- **Total Entities**: 245
- **Active Entities**: 238
- **Total Devices**: 45
- **Automations**: 18
- **Scripts**: 12

## Entity Breakdown by Domain
- **sensor**: 89 entities
- **light**: 23 entities
- **switch**: 15 entities
...
```

### 3. Work with AI

**Copy everything EXCEPT secrets/ directory:**

```bash
# Create safe package
cd /config/ai_exports
tar -czf safe_for_ai.tar.gz \
  --exclude='secrets' \
  ha_export_*/

# Download to your machine
scp root@homeassistant.local:/config/ai_exports/safe_for_ai.tar.gz .
```

**Share with AI:**
- Upload `AI_PROMPT.md`
- Upload `AI_CONTEXT.json`
- Upload any relevant config files from `config/`
- Ask AI to create automations, dashboards, scripts, etc.

### 4. Import AI Changes

**Prepare import:**
```bash
# SSH to Home Assistant
ssh root@homeassistant.local

# Navigate to import directory
cd /config/ai_imports/pending

# Create your AI-generated files here
nano new_automation.yaml
# Paste AI response, save
```

**Run import:**
```bash
ha-ai-workflow import
```

**Expected Flow:**
```
═══════════════════════════════════════════════════════════════════
  Starting Import Workflow
═══════════════════════════════════════════════════════════════════

ℹ Scanning import directory: /config/ai_imports/pending
✓ Found 2 file(s) to import

Files found:
new_automation.yaml
dashboard_config.yaml

Enter branch name for this import: feature/ai-automation

ℹ Branch name: feature/ai-automation
ℹ Creating branch: feature/ai-automation
✓ Branch created

ℹ Running import script...
✓ Import completed

ℹ Committing changes...
✓ Changes committed

ℹ Changes made:
 automations.yaml | 25 +++++++++++++++++++++++++
 1 file changed, 25 insertions(+)

ℹ Validating configuration...
✓ Configuration valid

ℹ Merging feature/ai-automation into main...
✓ Merged successfully

═══════════════════════════════════════════════════════════════════
  Ready to Deploy
═══════════════════════════════════════════════════════════════════

⚠ This will restart Home Assistant with the new configuration

Type 'DEPLOY' to confirm restart: DEPLOY

ℹ Restarting Home Assistant...
✓ Home Assistant restart initiated

═══════════════════════════════════════════════════════════════════
  Import Workflow Complete
═══════════════════════════════════════════════════════════════════

✓ Branch: feature/ai-automation
✓ Merged to: main
✓ Home Assistant restarted

ℹ Monitor logs with: docker logs homeassistant -f
```

## 🔧 Configuration Options

### Environment Variables

```bash
# Set custom export directory
export EXPORT_DIR="/mnt/backup/ai_exports"

# Enable debug mode
export DEBUG=1

# Disable git auto-commit
export NO_AUTO_COMMIT=1
```

### Command-Line Options

```bash
# Auto mode (no prompts)
ha-ai-workflow export --auto
ha-ai-workflow import --auto

# No strict error handling
ha-ai-workflow import --no-strict

# Enable debug upload
ha-ai-workflow import --upload-debug
```

## 📊 Monitoring and Logs

### Log Locations

```bash
# Workflow log
tail -f /config/ai_exports/workflow.log

# Home Assistant log
docker logs homeassistant -f

# Git history
cd /config
git log --oneline --graph
```

### Status Check

```bash
ha-ai-workflow status
```

**Output:**
```
═══════════════════════════════════════════════════════════════════
  HA AI Workflow Status
═══════════════════════════════════════════════════════════════════

ℹ Configuration:
  Config Dir: /config
  Export Dir: /config/ai_exports
  Import Dir: /config/ai_imports/pending

ℹ Git Status:
  Current Branch: main
  Last Commit: abc123 - AI Import: feature/ai-automation (2 hours ago)

ℹ Recent Exports:
  ha_export_20260113_120000 (Jan 13 12:00)
  ha_export_20260112_150000 (Jan 12 15:00)

ℹ Pending Imports:
  0 file(s) in import directory

ℹ Secrets Backups:
  secrets_map_20260113_120000.json (Jan 13 12:00)
  secrets_map_20260112_150000.json (Jan 12 15:00)
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. PyYAML Installation Fails

```bash
# Manual installation
python3 -m pip install pyyaml --break-system-packages

# Alternative
apk add py3-yaml
```

#### 2. Git Not Initialized

```bash
# Re-run setup
cd /config
git init
ha-ai-workflow setup
```

#### 3. Permission Denied

```bash
# Ensure running as root
sudo ha-ai-workflow export

# Fix permissions
chmod +x /usr/local/bin/ha-ai-workflow
chmod +x /usr/local/ha-ai-workflow/bin/*.py
```

#### 4. Validation Fails

```bash
# Check specific error
ha core check

# Review debug report
cat /config/ai_exports/debug_report_*.md

# Test YAML syntax
python3 -c "import yaml; yaml.safe_load(open('/config/automations.yaml'))"
```

#### 5. Import Directory Not Found

```bash
# Create manually
mkdir -p /config/ai_imports/pending

# Verify
ls -la /config/ai_imports/pending
```

### Debug Mode

```bash
# Enable verbose output
set -x
ha-ai-workflow export

# Check detailed logs
tail -100 /config/ai_exports/workflow.log
```

## 🔄 Backup and Recovery

### Manual Backup

```bash
# Backup entire config
cd /config
tar -czf ~/config_backup_$(date +%Y%m%d).tar.gz .

# Backup git history
git bundle create ~/config.bundle --all
```

### Recovery

```bash
# Rollback to previous commit
cd /config
git log --oneline
git checkout <commit-hash>
ha core restart

# Restore from backup
cd /
rm -rf /config
tar -xzf ~/config_backup_20260113.tar.gz -C /
ha core restart
```

## 🚀 Advanced Usage

### Scheduled Exports

```bash
# Add to crontab
crontab -e

# Daily export at 2 AM
0 2 * * * /usr/local/bin/ha-ai-workflow export --auto >> /config/ai_exports/cron.log 2>&1
```

### CI/CD Integration

```bash
#!/bin/bash
# deploy.sh - Automated deployment script

# Export current config
ha-ai-workflow export --auto

# Download AI changes from git
git pull origin ai-changes

# Move to import directory
mv new_configs/* /config/ai_imports/pending/

# Import and deploy
ha-ai-workflow import --auto
```

### Multi-Instance Management

```bash
# Export from instance A
ssh root@ha-instance-a.local "ha-ai-workflow export --auto"

# Copy to instance B
scp root@ha-instance-a.local:/config/ai_exports/ha_export_*/config/* \
    /tmp/import_to_b/

# Import to instance B
ssh root@ha-instance-b.local "
  mv /tmp/import_to_b/* /config/ai_imports/pending/
  ha-ai-workflow import --auto
"
```

## 📈 Performance Tips

1. **Reduce Export Size**
   - Exclude large custom components
   - Clean old logs before export

2. **Speed Up Git Operations**
   ```bash
   cd /config
   git gc --aggressive
   ```

3. **Archive Old Exports**
   ```bash
   find /config/ai_exports -name "ha_export_*" -mtime +30 -exec rm -rf {} \;
   ```

## 🔐 Security Best Practices

1. **Never commit secrets to git**
   ```bash
   # Verify .gitignore
   cat /config/.gitignore | grep secrets
   ```

2. **Regularly rotate secrets backups**
   ```bash
   # Keep only last 5 (automatic)
   ls /config/ai_exports/secrets/
   ```

3. **Secure the secrets directory**
   ```bash
   chmod 700 /config/ai_exports/secrets
   ```

4. **Use separate git remote for backups**
   ```bash
   cd /config
   git remote add backup git@backup-server:ha-config.git
   git push backup main
   ```

## 📦 GitHub Publishing Checklist

Before publishing to GitHub:

- [ ] Remove any sensitive test data
- [ ] Update version numbers
- [ ] Complete all documentation
- [ ] Add screenshots/demos
- [ ] Test on fresh HA installation
- [ ] Add GitHub Actions workflows
- [ ] Create release tags
- [ ] Write announcement post

## 🎉 Success Criteria

You'll know it's working when:

✅ Export completes without errors
✅ AI prompt is generated
✅ Secrets are properly sanitized
✅ Git commits are created
✅ Import validates configuration
✅ Home Assistant restarts successfully
✅ New automations appear in HA

## 📞 Getting Help

If you encounter issues:

1. Check the troubleshooting guide
2. Review logs
3. Generate debug report
4. Search existing issues
5. Create new issue with details

## 🎓 Next Steps

After successful deployment:

1. Create your first AI automation
2. Set up automated exports
3. Build a dashboard with AI
4. Share your success story
5. Contribute improvements

---

**Happy Automating! 🏠✨**

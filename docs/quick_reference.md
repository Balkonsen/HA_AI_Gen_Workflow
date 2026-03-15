# HA AI Workflow - Quick Reference Card

## 🚀 Essential Commands

```bash
# Installation
sudo ./setup.sh

# Export configuration for AI
ha-ai-workflow export

# Import AI changes
ha-ai-workflow import

# Check status
ha-ai-workflow status

# Get help
ha-ai-workflow --help
```

## 📁 Key Directories

```bash
/config/ai_exports/          # Export output
/config/ai_exports/secrets/  # 🔒 NEVER SHARE
/config/ai_imports/pending/  # Place AI files here
/config/.git/                # Version control
```

## 🔄 Complete Workflow

### Export → AI → Import

```bash
# 1. EXPORT
ha-ai-workflow export
# Result: AI_PROMPT.md + AI_CONTEXT.json

# 2. SHARE WITH AI (exclude secrets/)
# Upload AI_PROMPT.md and AI_CONTEXT.json

# 3. PREPARE IMPORT
# Save AI response to:
/config/ai_imports/pending/new_config.yaml

# 4. IMPORT
ha-ai-workflow import
# Enter branch name
# Type 'DEPLOY' to confirm
```

## 📊 File Locations After Export

```
/config/ai_exports/ha_export_TIMESTAMP/
├── AI_PROMPT.md           ← Share this
├── AI_CONTEXT.json        ← Share this
├── config/                ← Share this
│   ├── configuration.yaml
│   └── automations.yaml
├── diagnostics/           ← Share this
└── secrets/               ← 🔒 NEVER SHARE
    └── secrets_map.json
```

## 🎯 Common Tasks

### Check What's Exported

```bash
ha-ai-workflow status
ls -la /config/ai_exports/
```

### View AI Prompt

```bash
cat /config/ai_exports/ha_export_*/AI_PROMPT.md | less
```

### Prepare for AI

```bash
cd /config/ai_exports
tar -czf safe_for_ai.tar.gz --exclude='secrets' ha_export_*/
scp safe_for_ai.tar.gz user@laptop:~/
```

### Place AI Files

```bash
cd /config/ai_imports/pending
nano new_automation.yaml
# Paste AI response, save (Ctrl+X, Y, Enter)
```

### Monitor Import

```bash
docker logs homeassistant -f
```

## 🐛 Quick Fixes

### PyYAML Missing

```bash
python3 -m pip install pyyaml --break-system-packages
```

### Validation Failed

```bash
ha core check
cat /config/ai_exports/debug_report_*.md
```

### Rollback Changes

```bash
cd /config
git log --oneline
git checkout <commit-hash>
ha core restart
```

### Permission Issues

```bash
sudo ha-ai-workflow export
chmod +x /usr/local/bin/ha-ai-workflow
```

## 📝 Git Commands

```bash
cd /config

# View history
git log --oneline --graph

# See changes
git diff

# View branches
git branch -a

# Switch branch
git checkout branch-name

# Undo last commit
git reset --soft HEAD~1
```

## 🔐 Safety Checks

### Before Sharing

```bash
# ✅ SAFE to share:
AI_PROMPT.md
AI_CONTEXT.json
config/ directory
diagnostics/ directory

# ❌ NEVER share:
secrets/secrets_map.json
```

### Verify Secrets Not Exposed

```bash
grep -r "password" /config/ai_exports/ha_export_*/config/
# Should see placeholders: <<PASSWORD_1>>
```

## ⚡ Auto Mode (CI/CD)

```bash
# Fully automated (no prompts)
ha-ai-workflow export --auto
ha-ai-workflow import --auto
```

## 📞 Emergency Commands

```bash
# Stop everything
ha core stop

# Restore from backup
cd /config
git checkout main
ha core restart

# View recent logs
tail -100 /config/ai_exports/workflow.log

# Check HA status
ha core info
```

## 💡 Pro Tips

1. **Export regularly** (daily cron)

   ```bash
   0 2 * * * /usr/local/bin/ha-ai-workflow export --auto
   ```

2. **Test in branch first**

   ```bash
   git checkout -b test-automation
   # Make changes
   # Test
   # Then merge to main
   ```

3. **Keep secrets backed up**

   ```bash
   cp /config/ai_exports/secrets/secrets_map_latest.json ~/backup/
   ```

4. **Monitor git size**

   ```bash
   du -sh /config/.git
   git gc --aggressive  # if too large
   ```

## 🎓 Learning Path

1. ✅ Install system
2. ✅ Run first export
3. ✅ Share with AI
4. ✅ Import simple automation
5. ✅ Test and verify
6. ⬜ Create complex automations
7. ⬜ Build dashboards
8. ⬜ Set up automated exports

## 📊 Status Indicators

| Symbol | Meaning |
|--------|---------|
| ✓ | Success |
| ℹ | Information |
| ⚠ | Warning |
| ✗ | Error |

## 🔄 Workflow States

```
EXPORT → GENERATED → SHARED → AI_RESPONSE → PENDING → IMPORTED → DEPLOYED
```

## 📖 Documentation Links

- Full README: `/usr/local/ha-ai-workflow/docs/README.md`
- Quick Start: `/usr/local/ha-ai-workflow/docs/QUICKSTART.md`
- Troubleshooting: `/usr/local/ha-ai-workflow/docs/TROUBLESHOOTING.md`
- Logs: `/config/ai_exports/workflow.log`

## 🆘 When Things Go Wrong

1. **Don't panic** - everything is versioned
2. **Check logs** - `tail /config/ai_exports/workflow.log`
3. **Rollback if needed** - `git checkout <previous-commit>`
4. **Generate debug report** - automatic on validation failure
5. **Share debug with AI** - get help fixing issues

---

**Keep this reference handy! 📌**

Print or bookmark this page for quick access during your workflow.

*Version 1.0.0 - Last updated: 2026-01-13*

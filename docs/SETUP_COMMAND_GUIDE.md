# Setup and Command Installation Guide

## The Simple Pattern (Worked Through 1.0.5)

**Keep setup.sh and ha_ai_master_script.sh simple and focused.**

Through version 1.0.5, the installation and command system worked reliably because it followed simple, proven patterns:

## What Worked Well

### 1. setup.sh - Simple Installation

**Through 1.0.5, setup.sh:**

- Created necessary directories
- Installed Python dependencies
- Copied scripts to install location
- Created symlinks with **original filenames** (no renaming)
- Verified basic functionality

```bash
# ✅ GOOD - What worked through 1.0.5
# Copy script with original name
cp "${SCRIPT_DIR}/ha_ai_master_script.sh" "${INSTALL_DIR}/ha_ai_master_script.sh"

# Create symlink to original filename
ln -sf "${INSTALL_DIR}/ha_ai_master_script.sh" /usr/local/bin/ha-ai-workflow
```

**DON'T:**

```bash
# ❌ BAD - Causes confusion
# Renaming scripts during installation
mv ha_ai_master_script.sh ha_ai_master.sh  # Don't rename!
```

### 2. ha_ai_master_script.sh - Clear Paths

**Through 1.0.5, the master script:**

- Had clear, predictable paths for bin directory
- Used straightforward environment variable loading
- Exited with clear error messages if paths not found
- No complex fallback chains

```bash
# ✅ GOOD - Simple and clear
BIN_DIR="${BASE_DIR}/bin"
if [ ! -d "${BIN_DIR}" ]; then
    echo "ERROR: Cannot locate bin directory: ${BIN_DIR}" >&2
    echo "  Expected: ${BIN_DIR}/ha_diagnostic_export.py" >&2
    exit 1
fi
```

**DON'T:**

```bash
# ❌ BAD - Silent failure
BIN_DIR="${BASE_DIR}/bin"  # If this doesn't exist...
# Script continues anyway and fails later with cryptic errors
```

### 3. Environment Variables - Predictable Locations

**Through 1.0.5, .env file loading:**

- Checked a few logical locations
- Didn't overcomplicate with many fallbacks
- Made it clear where to put the file

```bash
# ✅ GOOD - Simple, predictable
for env_file in "${BASE_DIR}/.env" "${SCRIPT_DIR}/.env"; do
    if [ -f "${env_file}" ]; then
        . "${env_file}"
        break
    fi
done
```

### 4. Command Verification - Actually Test It

**Through 1.0.5, setup verification:**

- Actually ran the command with `--help` to verify it works
- Didn't just check if symlink exists

```bash
# ✅ GOOD - Test actual execution
if command -v ha-ai-workflow &>/dev/null; then
    if ha-ai-workflow --help &>/dev/null; then
        echo "✓ Command works: ha-ai-workflow"
    else
        echo "✗ Command found but fails to execute"
    fi
fi
```

**DON'T:**

```bash
# ❌ BAD - Only checks PATH
if command -v ha-ai-workflow; then
    echo "✓ Command found"  # But does it work?
fi
```

## The 7 Core Principles (From Option A)

These made setup reliable through 1.0.5:

1. **File Naming Consistency** - Don't rename files during install
2. **Token Validation** - Check SUPERVISOR_TOKEN before using it
3. **Clear Error Messages** - Exit with helpful messages, not silent failures
4. **Predictable Paths** - Use standard locations, document them
5. **Actual Verification** - Test that commands execute, not just exist
6. **Visible Errors** - Make API and setup failures obvious
7. **Match CI to Reality** - If Dockerfile uses Python 3.13, CI should too

## Common Setup Issues After 1.0.5

### Issue: Command Not Found

**Symptom:** `ha-ai-workflow: command not found`

**Through 1.0.5 solution:**

```bash
# Check symlink exists and points to right file
ls -la /usr/local/bin/ha-ai-workflow
# Should point to: /usr/local/ha-ai-workflow/ha_ai_master_script.sh

# Check original file exists
ls -la /usr/local/ha-ai-workflow/ha_ai_master_script.sh

# Recreate if needed with ORIGINAL NAME
ln -sf /usr/local/ha-ai-workflow/ha_ai_master_script.sh /usr/local/bin/ha-ai-workflow
```

### Issue: Python Scripts Not Found

**Symptom:** `Cannot locate bin directory`

**Through 1.0.5 solution:**

```bash
# BIN_DIR should be simple and predictable
BIN_DIR="/usr/local/ha-ai-workflow/bin"

# Verify it exists and has required files
ls "${BIN_DIR}/ha_diagnostic_export.py"
ls "${BIN_DIR}/workflow_orchestrator.py"

# If missing, copy from repo
cp -r /path/to/repo/bin/ /usr/local/ha-ai-workflow/
```

### Issue: Environment Variables Not Loaded

**Symptom:** SUPERVISOR_TOKEN not found

**Through 1.0.5 solution:**

```bash
# .env file should be in predictable location
# Either: /usr/local/ha-ai-workflow/.env
# Or: /config/.env

# Create it if missing:
cat > /usr/local/ha-ai-workflow/.env << EOF
SUPERVISOR_TOKEN="your_token_here"
EOF
```

## Installation Checklist (The 1.0.5 Way)

When installing or troubleshooting:

- [ ] Run `setup.sh` without modifications
- [ ] Verify files installed to `/usr/local/ha-ai-workflow/`
- [ ] Check `ha_ai_master_script.sh` kept its original name (not renamed)
- [ ] Verify symlink: `/usr/local/bin/ha-ai-workflow` → `ha_ai_master_script.sh`
- [ ] Test command: `ha-ai-workflow --help` (should show usage)
- [ ] Check bin directory: `ls /usr/local/ha-ai-workflow/bin/*.py`
- [ ] Verify .env file location if using SUPERVISOR_TOKEN
- [ ] Run actual export: `ha-ai-workflow export` (with token)

## What NOT to Do

### ❌ Over-Engineering

```bash
# BAD - Too many fallback paths, hard to debug
for location in /opt /usr /usr/local /var /home ~/.local ~/.config /tmp; do
    if [ -d "$location/something" ]; then
        # Which one did it find?
        # User can't tell where things went
    fi
done
```

### ❌ Silent Failures

```bash
# BAD - Continues with wrong path
BIN_DIR="${BASE_DIR}/bin"
# No check if it exists!
python3 "${BIN_DIR}/script.py"  # Fails later with confusing error
```

### ❌ File Renaming

```bash
# BAD - Creates confusion between filename and command
cp ha_ai_master_script.sh ha_ai_workflow.sh  # Now which file is it?
ln -s ha_ai_workflow.sh ha-ai-workflow       # Points to renamed file
# Later: "Why doesn't ha_ai_master_script.sh exist?"
```

## The Key Insight

**Through 1.0.5, setup was simple because:**

1. **One install location:** `/usr/local/ha-ai-workflow/`
2. **One command:** `ha-ai-workflow` (symlink to original script)
3. **One bin path:** `${INSTALL_DIR}/bin/`
4. **One .env location:** `${INSTALL_DIR}/.env` or `${CONFIG_DIR}/.env`
5. **Clear errors:** If something wrong, script says exactly what and where

**When things break**, it's usually because we:

- Added too many fallback paths (confusing)
- Renamed files (broke references)
- Made errors silent (hard to debug)
- Assumed paths exist (didn't validate)

## Maintenance Rule

**Before changing setup.sh or ha_ai_master_script.sh:**

Ask: "Did this work in 1.0.5?"

- If YES → Don't change it unless absolutely necessary
- If NO → Make change minimal and add clear error messages

**After changing:**

- Test actual installation from scratch
- Verify `ha-ai-workflow --help` works
- Check error messages are helpful
- Document what changed and why

---

**Remember:** Simplicity and clarity beat clever solutions. The 1.0.5 approach worked because it was straightforward and easy to debug.

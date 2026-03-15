# CLAUDE.md Structure Guide

This document explains the structure of CLAUDE.md and what information to extract during session startup.

## Key Sections to Parse

### 1. Project Status (Top of File)
```markdown
**Last Updated:** 2025-12-30
**Status:** Phase 1 - Initial Setup
```
- Extract the last updated date
- Extract the current phase

### 2. Current Status Section
```markdown
## 📊 Current Status

### Completed ✅
- [x] Directory structure created
- [x] CLAUDE.md initial version

### In Progress 🚧
- [ ] Migrate core ALNS algorithm
- [ ] Create quickstart tutorial
- [ ] Write README

### Next Steps 📋
1. Copy core files from SDR_stochastic
2. Create basic `pyproject.toml`
3. Write `tutorials/01_quickstart.ipynb`

### Blockers 🚫
- None currently
```

**What to extract:**
- List of completed tasks
- List of in-progress tasks (these are current priorities)
- Next steps (ordered list of upcoming work)
- Any blockers

### 3. Migration Progress
From the File Mapping Table in the Migration Plan section:

| Original File | New Location | Refactoring Needed |
|--------------|--------------|-------------------|
| `instance.py` | `vrp_toolkit/problems/pdptw.py` | Extract generic parts |
| ...

**What to calculate:**
- Total files to migrate: 9
- Files completed: Check against completed tasks
- Files remaining: Calculate from difference
- Current file being worked on: Check in-progress tasks

### 4. Recent Git Activity
Run: `git log --oneline -5` to show recent commits

**What to show:**
- Last 5 commits with hash and message
- Helps understand what was worked on recently

## Session Start Summary Format

Present information in this structure:

```
## 📊 Project Status
**Phase:** [Current phase]
**Last Updated:** [Date]

## ✅ Progress Overview
- Migration: [X/9 files completed] ([percentage]%)
- Completed: [count] tasks
- In Progress: [count] tasks
- Blockers: [count or "None"]

## 🚧 Current Focus
[List in-progress tasks with bullets]

## 📋 Next Priority Tasks
[List next steps 1-3 items]

## 🔍 Recent Activity
[Last 3-5 git commits]

## 💡 Suggested Action
Based on the current status, suggest what to work on next
```

## Migration Log Integration

If `MIGRATION_LOG.md` exists, also parse and show:
- Last migration completed (file name and date)
- Any issues flagged in recent migrations
- Overall migration health status

# Update Templates

Quick reference for updating project documentation after completing work.

## Updating CLAUDE.md

### 1. Update "Last Updated" Date
```markdown
**Last Updated:** 2025-12-31  ← Change to today
**Status:** Phase 1 - Initial Setup
```

### 2. Move Tasks
**Before:**
```markdown
### In Progress 🚧
- [ ] Migrate instance.py
```

**After:**
```markdown
### Completed ✅
- [x] Migrate instance.py  ← Moved here
```

### 3. Update Other Sections
- **Next Steps:** Add new tasks if identified
- **Blockers:** Remove if resolved, add if new
- **Phase:** Update if milestone reached

## Updating MIGRATION_LOG.md

### 1. Update Progress Summary
```markdown
**Total Files:** 9
**Completed:** 3  ← Increment
**In Progress:** 0
**Remaining:** 6  ← Decrement

### Completion Rate: 33%  ← (3/9)*100
```

### 2. Add Migration Entry
Add at top of "Migration History":

```markdown
### YYYY-MM-DD - [Original File] → [New Location]

**Status:** ✅ Completed
**Time Spent:** [e.g., 45 minutes]
**Complexity:** Low/Medium/High

**Source:** `[path/to/original/file.py]`
**Destination:** `[path/to/new/file.py]`

#### 📋 Migration Summary
- **Original Purpose:** [Brief description]
- **Target Architecture Layer:** [Problem/Algorithm/Data/Visualization]
- **Key Changes Made:** [2-3 sentence overview]

#### 🔧 Key Changes
- **Extracted hardcoded values:** [What was parameterized]
- **Decoupled from paper logic:** [How generalized]
- **Added/improved:** [Docstrings, type hints, etc.]

#### ⚠️ Issues & Solutions
**Issue 1:** [Description]
- **Solution:** [Fix implemented]
- **Impact:** [Effect on migration]

#### ✅ Verification
- [ ] Code compilation
- [ ] Import tests
- [ ] Runtime tests (if environment available)

#### 📝 Notes
- [Any important observations]
```

### 2.5 Update Index
If MIGRATION_LOG.md has an "## Index" section (should be added after "Migration Progress Summary"), update it:

**Format:**
```markdown
- [YYYY-MM-DD] [Brief title] ([status symbol] [Status])
```

**Example:**
```markdown
- [2026-01-01] Phase 2: Test Suite Enhancement for New Architecture (✅ Completed)
```

**Steps:**
1. Extract title from migration entry (first line after `### `)
2. Extract date (YYYY-MM-DD from title)
3. Extract status from `**Status:**` line
4. Add new entry at top of index list (newest first)
5. Trim index to 10-15 entries if it gets too long

**Index section example:**
```markdown
---

## Index

*Recent migration entries (newest first):*

- [2026-01-01] Phase 2: Test Suite Enhancement for New Architecture (✅ Completed)
- [2025-12-31] Validation test and bug fixes (✅ Completed)
- [2025-12-30] README creation and git push (✅ Completed)
```

### 3. Update Checklist
```markdown
1. [x] `instance.py` → `vrp_toolkit/problems/pdptw.py`  ← Mark as done
2. [ ] `solution.py` → `vrp_toolkit/problems/pdptw.py`
```

### 4. Update "Last Updated" Date
```markdown
**Last Updated:** 2025-12-31
```

## Quick Checklist

### For Any Task
- [ ] Update CLAUDE.md "Last Updated" date
- [ ] Move task from "In Progress" to "Completed"
- [ ] Update other sections as needed

### For Migrations Only
- [ ] Update MIGRATION_LOG.md progress numbers
- [ ] Add migration entry at top
- [ ] Update index section (add new entry, trim if needed)
- [ ] Mark file as completed in checklist
- [ ] Update "Last Updated" date

## Status Symbols
- ✅ **Completed** - Successfully finished
- 🚧 **In Progress** - Currently working
- ⚠️ **Issues** - Done but has known issues
- ❌ **Failed** - Could not complete

## Tips
- **Be specific:** "Extracted `battery_capacity=100` to parameter"
- **Include context:** Why decisions were made
- **Check examples:** See existing entries in MIGRATION_LOG.md

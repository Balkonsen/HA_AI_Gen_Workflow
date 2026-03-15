# Skill Update Procedures

This guide provides step-by-step procedures for updating skills and maintaining skill documentation.

## Table of Contents
1. Update CLAUDE.md Skills Index
2. Record Changes in SKILLS_LOG.md
3. Rename a Skill
4. Split a Large Skill
5. Merge Similar Skills
6. Archive Deprecated Skills

---

## 1. Update CLAUDE.md Skills Index

**When:** After adding, removing, or significantly modifying a skill

### Procedure

1. **Locate the Skills Reference section** in CLAUDE.md (around line 130-315)

2. **For new skills:** Add entry following this template:
```markdown
#### N. **skill-name** - Short Title
**When to use:** [Trigger conditions]

**What it does:**
- [Key function 1]
- [Key function 2]
- [Key function 3]

**Trigger:** Say "[example phrase]" or "[example phrase 2]"

**[Optional sections like References, Integration, Value]**
```

3. **For modified skills:** Update the corresponding section to match SKILL.md frontmatter description

4. **For removed skills:** Delete the entire section and renumber remaining skills

5. **Update skill count** in section header:
```markdown
We have created **N custom skills** to automate common workflows.
```

6. **Verify numbering** - Skills should be numbered 1-N consecutively

### Example: Adding a New Skill

```markdown
#### 10. **validate-instance** - Instance Data Validation
**When to use:** Validating PDPTW instances before solving

**What it does:**
- Checks time window consistency
- Validates pickup-delivery pairs
- Verifies vehicle capacity constraints
- Reports violations with fix suggestions

**Trigger:** Say "validate instance", "check instance", or "verify data"
```

---

## 2. Record Changes in SKILLS_LOG.md

**When:** After any skill modification, addition, or removal

### Template

```markdown
## YYYY-MM-DD - [Action]: [skill-name]
**Action:** [Added/Updated/Removed/Renamed/Split/Merged]
**Reason:** [Why this change was made]
**Changes:**
- [Specific change 1]
- [Specific change 2]
**Compliance Notes:** [Any compliance issues addressed]
**Impact:** [How this affects other skills or workflows]
```

### Examples

**Adding a skill:**
```markdown
## 2026-01-03 - Added: manage-skills
**Action:** Created new skill for meta-management of skills
**Reason:** Project now has 9 skills, needed centralized management and compliance checking
**Changes:**
- Created skill structure with scripts/, references/, assets/
- Added compliance checking script
- Added CLAUDE.md index sync functionality
**Compliance Notes:** N/A (new skill)
**Impact:** Enables systematic skill maintenance going forward
```

**Updating a skill:**
```markdown
## 2026-01-03 - Updated: maintain-data-structures
**Action:** Removed duplicate migration workflow content
**Reason:** Compliance violation - embedded content from migrate-module skill
**Changes:**
- Removed step-by-step migration workflow section
- Kept only data structure reference content
- Updated SKILL.md to reference migrate-module instead
**Compliance Notes:** Fixed independence violation
**Impact:** Skill now focused purely on data structure reference
```

**Splitting a skill:**
```markdown
## 2026-01-03 - Split: integrate-road-network
**Action:** Split into integrate-road-network and osmnx-reference
**Reason:** SKILL.md exceeded 500 lines (was 680 lines)
**Changes:**
- Moved detailed OSMnx API reference to osmnx-reference skill
- Kept integration workflow in integrate-road-network
- Updated cross-references between skills
**Compliance Notes:** Fixed size violation (680 → 320 lines)
**Impact:** Created new osmnx-reference skill, updated CLAUDE.md index
```

---

## 3. Rename a Skill

**When:** Skill name no longer reflects its purpose

### Procedure

1. **Rename directory:**
```bash
mv .claude/skills/old-name .claude/skills/new-name
```

2. **Update SKILL.md frontmatter:**
```yaml
---
name: new-name
description: [update if needed]
---
```

3. **Update CLAUDE.md:**
   - Find skill entry in Skills Reference section
   - Update heading and references

4. **Search for references in other skills:**
```bash
grep -r "old-name" .claude/skills/
```
   - Update any references to use new name

5. **Update SKILLS_LOG.md:**
```markdown
## YYYY-MM-DD - Renamed: old-name → new-name
**Action:** Renamed skill
**Reason:** [Why rename was needed]
**Changes:**
- Renamed directory from old-name to new-name
- Updated SKILL.md frontmatter
- Updated CLAUDE.md references
- Updated references in [list other skills]
```

---

## 4. Split a Large Skill

**When:** SKILL.md exceeds 500 lines

### Decision Process

1. **Identify logical split points:**
   - Separate workflows?
   - Different domains?
   - Core vs advanced features?

2. **Choose split strategy:**
   - **Extract to references/** - If content is supplementary
   - **Create new skill** - If content is independent workflow

### Procedure A: Extract to References

1. **Identify extractable sections** (examples, API docs, troubleshooting)

2. **Create reference files:**
```bash
# In skill directory
touch references/examples.md
touch references/api_reference.md
```

3. **Move content** from SKILL.md to reference files

4. **Update SKILL.md** with references:
```markdown
See [examples.md](references/examples.md) for detailed examples.
```

5. **Verify:** SKILL.md now ≤ 500 lines

### Procedure B: Create New Skill

1. **Create new skill** using skill-creator

2. **Move content** from old SKILL.md to new skill

3. **Update cross-references:**
   - Old skill mentions new skill
   - New skill mentions old skill (if related)

4. **Update CLAUDE.md** - Add new skill entry

5. **Update SKILLS_LOG.md** - Record split

---

## 5. Merge Similar Skills

**When:** Skills have overlapping functionality or are too granular

### Decision Criteria

**Merge if:**
- Skills are always used together
- Significant content overlap (>30%)
- Both skills are small (<200 lines each)
- Same domain/workflow

**Don't merge if:**
- Skills serve different domains
- Used independently most of the time
- Combined size would exceed 500 lines

### Procedure

1. **Choose primary skill** (keep this name)

2. **Merge content:**
   - Copy relevant sections from secondary skill
   - Integrate into primary skill's structure
   - Remove duplicates

3. **Update SKILL.md:**
   - Expand description to cover both use cases
   - Combine workflows
   - Merge references/

4. **Delete secondary skill:**
```bash
rm -rf .claude/skills/secondary-skill
```

5. **Update CLAUDE.md:**
   - Remove secondary skill entry
   - Update primary skill description
   - Renumber remaining skills

6. **Update SKILLS_LOG.md:**
```markdown
## YYYY-MM-DD - Merged: skill-a + skill-b → skill-a
**Action:** Merged skill-b into skill-a
**Reason:** [Why merge was needed]
**Changes:**
- Integrated skill-b content into skill-a
- Deleted skill-b directory
- Updated CLAUDE.md index
**Impact:** Reduced total skills from N to N-1
```

---

## 6. Archive Deprecated Skills

**When:** Skill is no longer needed but might be useful as reference

### Procedure

1. **Create archive directory** (if doesn't exist):
```bash
mkdir -p .claude/skills/.archive
```

2. **Move skill:**
```bash
mv .claude/skills/deprecated-skill .claude/skills/.archive/
```

3. **Update CLAUDE.md:**
   - Remove skill entry
   - Renumber remaining skills

4. **Update SKILLS_LOG.md:**
```markdown
## YYYY-MM-DD - Archived: deprecated-skill
**Action:** Moved to .archive/
**Reason:** [Why no longer needed]
**Impact:** Skill no longer active, available in archive for reference
```

5. **Add .archive/ to .gitignore** (if archiving permanently)

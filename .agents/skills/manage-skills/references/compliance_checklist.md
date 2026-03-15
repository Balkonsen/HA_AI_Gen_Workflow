# Skill Compliance Checklist

This document defines the compliance standards for VRP Toolkit skills.

## 1. Independence Standard

**Objective:** Each skill should work independently without embedding other skills' content.

### ✅ Pass Criteria
- Skill can be understood and executed without reading other skills
- References to other skills are limited to:
  - "See [skill-name] for..." (suggestion, not embedding)
  - "Use [skill-name] next" (workflow transition)
  - "Works with [skill-name]" (integration note)

### ❌ Fail Criteria
- Embedding step-by-step workflows from other skills
- Duplicating reference content from other skills
- Requiring other skills to be loaded to understand this one

### Examples

**Good:**
```markdown
After migration is complete, use the update-migration-log skill to record changes.
```

**Bad:**
```markdown
After migration, follow these steps from update-migration-log:
1. Update CLAUDE.md Completed section
2. Add entry to MIGRATION_LOG.md
3. Update progress percentage
...
```

---

## 2. Size Standard

**Objective:** Keep SKILL.md focused and under 500 lines to minimize context usage.

### ✅ Pass Criteria
- SKILL.md ≤ 500 lines (excluding frontmatter)
- Long content split into references/

### ⚠️ Warning Triggers
- SKILL.md > 400 lines → Consider splitting soon
- SKILL.md > 500 lines → Must split immediately

### ❌ Fail Criteria
- SKILL.md > 600 lines without justification

### Splitting Guidelines
When SKILL.md approaches 500 lines:
1. Identify sections that can be extracted
2. Move to references/ with descriptive names
3. Add clear references in SKILL.md
4. Keep core workflow in SKILL.md

**Example split:**
```
Before:
skill/SKILL.md (800 lines)

After:
skill/
├── SKILL.md (300 lines - core workflow)
└── references/
    ├── detailed_examples.md (200 lines)
    ├── troubleshooting.md (200 lines)
    └── api_reference.md (200 lines)
```

---

## 3. Structure Standard

**Objective:** Ensure all required files exist and are properly organized.

### ✅ Required Files
```
skill-name/
└── SKILL.md (with valid YAML frontmatter)
```

### ✅ Optional Directories
```
skill-name/
├── scripts/      (if skill provides executable code)
├── references/   (if skill has detailed reference docs)
└── assets/       (if skill provides templates/files)
```

### ✅ Frontmatter Requirements
```yaml
---
name: skill-name
description: Clear description including when to use (100-200 words)
---
```

### ❌ Prohibited Files
- README.md
- CHANGELOG.md
- INSTALLATION.md
- Any non-essential documentation

---

## 4. Clarity Standard

**Objective:** Ensure skill is easy to understand and use.

### ✅ Pass Criteria

**Description:**
- Clearly states what the skill does
- Includes specific trigger conditions
- 100-200 words in frontmatter

**Body Structure:**
- Clear sections with headers
- Code examples where helpful
- References to bundled resources

**Trigger Clarity:**
- At least 1 example trigger phrase
- Clear "When to use" in description

### ❌ Fail Criteria
- Vague description without use cases
- No examples or unclear workflow
- Missing references to bundled resources

---

## 5. Reference Organization Standard

**Objective:** Keep references discoverable and well-organized.

### ✅ Pass Criteria
- All references linked from SKILL.md
- Reference files have clear, descriptive names
- Long references (>100 lines) have table of contents
- No deeply nested references (max 1 level from SKILL.md)

### ⚠️ Warning Triggers
- Reference file > 500 lines → Consider splitting
- More than 5 reference files → Consider reorganizing

### ❌ Fail Criteria
- Reference files not mentioned in SKILL.md
- Nested references (references/foo/bar.md)
- Duplicate content between SKILL.md and references

---

## Compliance Check Process

### For New Skills
1. Check structure (required files exist)
2. Check frontmatter (valid YAML, complete description)
3. Check size (SKILL.md ≤ 500 lines)
4. Check independence (no embedded workflows)
5. Check clarity (examples present, references linked)

### For Modified Skills
1. Check size (if approaching 500 lines)
2. Check independence (if content added from other skills)
3. Check references (if new references added)
4. Update CLAUDE.md description if needed

### For Periodic Audits
1. Scan all skills for compliance
2. Identify overlap between skills
3. Suggest mergers or splits
4. Update SKILLS_LOG.md with findings

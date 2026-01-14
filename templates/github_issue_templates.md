# GitHub Issue Templates

Create these files in `.github/ISSUE_TEMPLATE/` directory.

## 1. Bug Report Template

**File:** `.github/ISSUE_TEMPLATE/bug_report.md`

```markdown
---
name: Bug Report
about: Report a bug or issue with HA AI Workflow
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
<!-- A clear and concise description of the bug -->

## Steps to Reproduce
1. Run command: `...`
2. Do action: `...`
3. See error: `...`

## Expected Behavior
<!-- What you expected to happen -->

## Actual Behavior
<!-- What actually happened -->

## Error Messages
```
<!-- Paste error messages here -->
```

## Environment
- **Home Assistant Version:** <!-- e.g., 2026.1.0 -->
- **HA AI Workflow Version:** <!-- e.g., 1.0.0 -->
- **Installation Type:** <!-- OS / Supervised / Container / Core -->
- **Python Version:** <!-- e.g., 3.11.6 -->
- **Operating System:** <!-- e.g., Home Assistant OS 11.3 -->

## Configuration
<!-- If relevant, share sanitized configuration -->

```yaml
# Your configuration here (remove secrets!)
```

## Logs
<!-- Attach relevant logs -->

```
# Workflow log
cat /config/ai_exports/workflow.log | tail -100

# Or debug report
cat /config/ai_exports/debug_report_*.md
```

## Screenshots
<!-- If applicable, add screenshots -->

## Additional Context
<!-- Add any other context about the problem -->

## Checklist
- [ ] I have checked existing issues
- [ ] I have included error messages
- [ ] I have included environment details
- [ ] I have removed all sensitive information
- [ ] I have tried basic troubleshooting steps
```

---

## 2. Feature Request Template

**File:** `.github/ISSUE_TEMPLATE/feature_request.md`

```markdown
---
name: Feature Request
about: Suggest a new feature or enhancement
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Feature Description
<!-- Clear description of the feature you'd like -->

## Use Case
<!-- Describe the problem this feature would solve -->

### Example Scenario
<!-- Provide a concrete example of how this would be used -->

## Proposed Solution
<!-- How do you envision this feature working? -->

```bash
# Example commands or workflow
ha-ai-workflow new-feature --option value
```

## Alternatives Considered
<!-- What alternatives have you considered? -->

## Benefits
<!-- Who would benefit from this feature? -->

- [ ] All users
- [ ] Advanced users
- [ ] Specific use case (explain below)

## Implementation Ideas
<!-- If you have ideas on how to implement this -->

## Additional Context
<!-- Screenshots, mockups, related issues, etc. -->

## Priority
- [ ] Nice to have
- [ ] Important for my workflow
- [ ] Critical missing feature

## I'm willing to
- [ ] Test beta versions of this feature
- [ ] Contribute code if guided
- [ ] Help with documentation
- [ ] Provide additional feedback
```

---

## 3. Documentation Improvement

**File:** `.github/ISSUE_TEMPLATE/documentation.md`

```markdown
---
name: Documentation Improvement
about: Report unclear, missing, or incorrect documentation
title: '[DOCS] '
labels: documentation
assignees: ''
---

## Documentation Issue
<!-- What documentation needs improvement? -->

- **File/Page:** <!-- e.g., README.md, QUICKSTART.md -->
- **Section:** <!-- e.g., "Installation", "Usage" -->
- **URL:** <!-- If online docs -->

## Problem
<!-- What's unclear, missing, or incorrect? -->

## Suggested Improvement
<!-- How should this be improved? -->

```markdown
<!-- Suggested text/changes -->
```

## Additional Context
<!-- Screenshots, examples, related documentation -->

## Impact
- [ ] Prevents new users from getting started
- [ ] Causes confusion during use
- [ ] Missing important information
- [ ] Contains outdated information
- [ ] Minor typo or formatting
```

---

## 4. Question / Help Wanted

**File:** `.github/ISSUE_TEMPLATE/question.md`

```markdown
---
name: Question / Help
about: Ask a question or get help
title: '[QUESTION] '
labels: question
assignees: ''
---

## Question
<!-- Your question here -->

## What I've Tried
<!-- What have you already attempted? -->

1. 
2. 
3. 

## Context
<!-- Provide context about what you're trying to achieve -->

## Environment
- **Home Assistant Version:** 
- **HA AI Workflow Version:** 

## Relevant Configuration
```yaml
# Share relevant configuration (sanitized)
```

## Logs/Output
```
# Paste relevant logs or command output
```

## Checklist
- [ ] I've read the documentation
- [ ] I've checked existing issues/discussions
- [ ] I've tried basic troubleshooting
- [ ] This isn't covered in FAQ
```

---

## 5. Export/Import Issue

**File:** `.github/ISSUE_TEMPLATE/export_import_issue.md`

```markdown
---
name: Export/Import Issue
about: Report problems with export or import workflows
title: '[EXPORT/IMPORT] '
labels: bug, workflow
assignees: ''
---

## Workflow Step
- [ ] Export
- [ ] Import
- [ ] Both

## Command Run
```bash
# Exact command you ran
ha-ai-workflow export
```

## Error Output
```
# Full error output
```

## Export/Import Details

### For Export Issues
- **Export succeeded:** Yes / No
- **Verification passed:** Yes / No
- **AI context generated:** Yes / No
- **Secrets backed up:** Yes / No

### For Import Issues
- **Files in pending directory:** <!-- Count -->
- **Branch created:** Yes / No
- **Validation passed:** Yes / No
- **Merge succeeded:** Yes / No
- **HA restarted:** Yes / No

## Files Involved
<!-- List files being exported/imported -->

## Debug Report
<!-- If available, paste debug report -->

```markdown
# Paste debug_report_*.md here
```

## Workflow Log
```
# Last 50 lines of workflow log
tail -50 /config/ai_exports/workflow.log
```

## Git Status
```
cd /config
git status
git log --oneline -5
```

## Environment
- **Home Assistant Version:** 
- **Supervisor Version:** 
- **Available Disk Space:** 
- **Python Version:** 

## Additional Information
<!-- Any other relevant details -->
```

---

## 6. AI Integration Issue

**File:** `.github/ISSUE_TEMPLATE/ai_integration.md`

```markdown
---
name: AI Integration Issue
about: Problems with AI-generated configurations
title: '[AI] '
labels: ai-integration
assignees: ''
---

## AI Platform Used
- [ ] Claude (Anthropic)
- [ ] ChatGPT (OpenAI)
- [ ] Other: ____

## Issue Type
- [ ] AI-generated config won't import
- [ ] Validation failed on AI config
- [ ] AI doesn't understand context
- [ ] AI prompt needs improvement
- [ ] Other

## AI Prompt Used
```markdown
<!-- What you asked the AI -->
```

## AI Response
```yaml
<!-- What the AI generated -->
```

## Error Encountered
```
<!-- Error when trying to use AI response -->
```

## Expected Behavior
<!-- What should have happened -->

## Files Shared with AI
- [ ] AI_PROMPT.md
- [ ] AI_CONTEXT.json
- [ ] Configuration files
- [ ] Debug report
- [ ] Other: ____

## Context Quality
<!-- Was the AI context sufficient? -->
- [ ] AI had all needed information
- [ ] AI was missing important context
- [ ] Context was confusing/unclear

## Suggested Improvements
<!-- How could the AI interaction be better? -->

## Home Assistant Setup
- **Total Entities:** 
- **Total Devices:** 
- **Integrations:** 
```

---

## 7. Security/Privacy Concern

**File:** `.github/ISSUE_TEMPLATE/security.md`

```markdown
---
name: Security/Privacy Concern
about: Report security or privacy issues (USE PRIVATELY FOR CRITICAL ISSUES)
title: '[SECURITY] '
labels: security
assignees: ''
---

## ⚠️ IMPORTANT
**For critical security vulnerabilities, please report privately:**
Email: [your-security-email@domain.com]

## Issue Type
- [ ] Secrets leaked in export
- [ ] Sensitive data visible
- [ ] Permission issue
- [ ] Authentication concern
- [ ] Other security concern

## Description
<!-- Describe the security/privacy concern -->

## Steps to Reproduce
<!-- How can this be reproduced? -->

## Potential Impact
- [ ] Credentials exposed
- [ ] Personal information leaked
- [ ] Unauthorized access possible
- [ ] Other: ____

## Affected Versions
<!-- Which versions are affected? -->

## Suggested Fix
<!-- If you have suggestions -->

## Severity
- [ ] Critical (immediate action needed)
- [ ] High (should be fixed soon)
- [ ] Medium (should be addressed)
- [ ] Low (minor concern)
```

---

## Config.yml for Issue Templates

**File:** `.github/ISSUE_TEMPLATE/config.yml`

```yaml
blank_issues_enabled: false
contact_links:
  - name: 💬 Community Discussions
    url: https://github.com/yourusername/ha-ai-workflow/discussions
    about: Ask questions and discuss with the community
  
  - name: 📖 Documentation
    url: https://github.com/yourusername/ha-ai-workflow/wiki
    about: Read the full documentation
  
  - name: 🐛 Troubleshooting Guide
    url: https://github.com/yourusername/ha-ai-workflow/blob/main/docs/TROUBLESHOOTING.md
    about: Check common issues and solutions
  
  - name: 💡 Feature Ideas
    url: https://github.com/yourusername/ha-ai-workflow/discussions/categories/ideas
    about: Share and discuss feature ideas
```

---

## Pull Request Template

**File:** `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Description
<!-- Describe your changes -->

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Related Issues
<!-- Link to related issues -->
Fixes #(issue number)
Related to #(issue number)

## Testing
<!-- How has this been tested? -->

- [ ] Tested on fresh installation
- [ ] Tested export workflow
- [ ] Tested import workflow
- [ ] Tested with AI assistant
- [ ] Checked for security issues
- [ ] Validated all scripts
- [ ] Updated documentation

## Test Configuration
- **Home Assistant Version:** 
- **Python Version:** 
- **Installation Type:** 

## Screenshots
<!-- If applicable -->

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Additional Notes
<!-- Any additional information -->
```

---

## Usage Instructions

### Creating Templates in Your Repo

```bash
# Create directory structure
mkdir -p .github/ISSUE_TEMPLATE

# Copy templates
cp bug_report.md .github/ISSUE_TEMPLATE/
cp feature_request.md .github/ISSUE_TEMPLATE/
cp documentation.md .github/ISSUE_TEMPLATE/
cp question.md .github/ISSUE_TEMPLATE/
cp export_import_issue.md .github/ISSUE_TEMPLATE/
cp ai_integration.md .github/ISSUE_TEMPLATE/
cp security.md .github/ISSUE_TEMPLATE/
cp config.yml .github/ISSUE_TEMPLATE/
cp PULL_REQUEST_TEMPLATE.md .github/

# Commit
git add .github/
git commit -m "Add issue and PR templates"
git push
```

### Testing Templates

1. Go to your repository
2. Click "Issues" → "New Issue"
3. You should see all templates listed
4. Select one to verify formatting

---

**These templates ensure high-quality issue reports and make it easier for contributors to help!**

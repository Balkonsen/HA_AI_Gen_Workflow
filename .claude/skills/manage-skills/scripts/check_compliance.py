#!/usr/bin/env python3
"""
Check skill compliance against VRP Toolkit standards.

Usage:
    python check_compliance.py [skill-name]        # Check specific skill
    python check_compliance.py --all               # Check all skills
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class ComplianceChecker:
    """Check skill compliance against standards."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.skills_dir = project_root / '.claude' / 'skills'

    def check_skill(self, skill_name: str) -> Dict:
        """Check compliance for a single skill."""
        skill_path = self.skills_dir / skill_name
        results = {
            'skill_name': skill_name,
            'exists': skill_path.exists(),
            'checks': {},
            'warnings': [],
            'errors': [],
            'passed': True
        }

        if not results['exists']:
            results['errors'].append(f"Skill directory does not exist: {skill_path}")
            results['passed'] = False
            return results

        # Run all checks
        self._check_structure(skill_path, results)
        self._check_frontmatter(skill_path, results)
        self._check_size(skill_path, results)
        self._check_independence(skill_path, results)
        self._check_references(skill_path, results)

        # Overall pass/fail
        results['passed'] = len(results['errors']) == 0

        return results

    def _check_structure(self, skill_path: Path, results: Dict):
        """Check required file structure."""
        skill_md = skill_path / 'SKILL.md'

        if not skill_md.exists():
            results['errors'].append("Missing required SKILL.md file")
            results['checks']['structure'] = False
            return

        # Check for prohibited files
        prohibited = ['README.md', 'CHANGELOG.md', 'INSTALLATION.md']
        found_prohibited = []
        for item in skill_path.rglob('*'):
            if item.name in prohibited:
                found_prohibited.append(item.name)

        if found_prohibited:
            results['warnings'].append(f"Found prohibited files: {', '.join(found_prohibited)}")

        results['checks']['structure'] = True

    def _check_frontmatter(self, skill_path: Path, results: Dict):
        """Check YAML frontmatter."""
        skill_md = skill_path / 'SKILL.md'

        if not skill_md.exists():
            results['checks']['frontmatter'] = False
            return

        content = skill_md.read_text(encoding='utf-8')

        # Extract frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            results['errors'].append("Missing YAML frontmatter")
            results['checks']['frontmatter'] = False
            return

        try:
            frontmatter = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            results['errors'].append("Invalid YAML frontmatter")
            results['checks']['frontmatter'] = False
            return

        # Check required fields
        if 'name' not in frontmatter:
            results['errors'].append("Missing 'name' field in frontmatter")
        elif frontmatter['name'] != skill_path.name:
            results['errors'].append(f"Frontmatter name '{frontmatter['name']}' does not match directory '{skill_path.name}'")

        if 'description' not in frontmatter:
            results['errors'].append("Missing 'description' field in frontmatter")
        else:
            desc_length = len(frontmatter['description'].split())
            if desc_length < 20:
                results['warnings'].append(f"Description is short ({desc_length} words, recommend 50-200)")
            elif desc_length > 300:
                results['warnings'].append(f"Description is long ({desc_length} words, recommend 50-200)")

        # Check for extra fields
        allowed_fields = {'name', 'description'}
        extra_fields = set(frontmatter.keys()) - allowed_fields
        if extra_fields:
            results['warnings'].append(f"Unexpected frontmatter fields: {', '.join(extra_fields)}")

        results['checks']['frontmatter'] = len(results['errors']) == 0

    def _check_size(self, skill_path: Path, results: Dict):
        """Check SKILL.md size."""
        skill_md = skill_path / 'SKILL.md'

        if not skill_md.exists():
            results['checks']['size'] = False
            return

        content = skill_md.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Remove frontmatter from count
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if match:
            frontmatter_lines = match.group(0).count('\n')
            body_lines = len(lines) - frontmatter_lines
        else:
            body_lines = len(lines)

        results['checks']['size'] = {
            'total_lines': len(lines),
            'body_lines': body_lines
        }

        if body_lines > 600:
            results['errors'].append(f"SKILL.md body is too large ({body_lines} lines, must be ≤600)")
        elif body_lines > 500:
            results['errors'].append(f"SKILL.md body exceeds limit ({body_lines} lines, must be ≤500)")
        elif body_lines > 400:
            results['warnings'].append(f"SKILL.md body is approaching limit ({body_lines}/500 lines)")

    def _check_independence(self, skill_path: Path, results: Dict):
        """Check skill independence (not embedding other skills' content)."""
        skill_md = skill_path / 'SKILL.md'

        if not skill_md.exists():
            results['checks']['independence'] = False
            return

        content = skill_md.read_text(encoding='utf-8')

        # Get list of other skills
        other_skills = set()
        for item in self.skills_dir.iterdir():
            if item.is_dir() and item.name != skill_path.name and (item / 'SKILL.md').exists():
                other_skills.add(item.name)

        # Check for embedded workflows (suspicious patterns)
        suspicious_patterns = [
            r'follow these steps from (\w+-\w+):',  # "follow these steps from other-skill:"
            r'(\w+-\w+) workflow:\s*\n\s*1\.',      # "other-skill workflow:\n1."
            r'from (\w+-\w+):\s*\n\s*-',           # "from other-skill:\n-"
        ]

        found_violations = []
        for pattern in suspicious_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                skill_mentioned = match.group(1)
                if skill_mentioned in other_skills:
                    found_violations.append(f"Possible embedded workflow from '{skill_mentioned}'")

        if found_violations:
            results['warnings'].extend(found_violations)
            results['warnings'].append("Review for independence: ensure skill doesn't embed other skills' workflows")

        results['checks']['independence'] = True

    def _check_references(self, skill_path: Path, results: Dict):
        """Check references organization."""
        skill_md = skill_path / 'SKILL.md'
        references_dir = skill_path / 'references'

        if not skill_md.exists():
            results['checks']['references'] = False
            return

        skill_content = skill_md.read_text(encoding='utf-8')

        # Check if references/ exists
        if not references_dir.exists():
            results['checks']['references'] = True
            return

        # Get all reference files
        ref_files = list(references_dir.glob('*.md'))

        if not ref_files:
            results['warnings'].append("references/ directory exists but is empty")
            results['checks']['references'] = True
            return

        # Check if reference files are mentioned in SKILL.md
        unmentioned = []
        for ref_file in ref_files:
            ref_name = ref_file.name
            if ref_name not in skill_content:
                unmentioned.append(ref_name)

        if unmentioned:
            results['warnings'].append(f"Reference files not mentioned in SKILL.md: {', '.join(unmentioned)}")

        # Check for nested directories
        nested_dirs = [d for d in references_dir.rglob('*') if d.is_dir()]
        if nested_dirs:
            results['warnings'].append("Avoid nested directories in references/ (keep references 1 level deep)")

        # Check size of reference files
        for ref_file in ref_files:
            lines = len(ref_file.read_text(encoding='utf-8').split('\n'))
            if lines > 500:
                results['warnings'].append(f"{ref_file.name} is large ({lines} lines), consider splitting")

        results['checks']['references'] = True

    def check_all_skills(self) -> List[Dict]:
        """Check compliance for all skills."""
        results = []

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                if (skill_dir / 'SKILL.md').exists():
                    result = self.check_skill(skill_dir.name)
                    results.append(result)

        return results


def print_results(result: Dict):
    """Print compliance check results for a single skill."""
    print("=" * 60)
    print(f"COMPLIANCE CHECK: {result['skill_name']}")
    print("=" * 60)

    if not result['exists']:
        print("[FAIL] Skill does not exist")
        return

    # Print check results
    print("\nChecks:")
    for check_name, check_result in result['checks'].items():
        if isinstance(check_result, dict):
            # Size check
            status = "[OK]" if not any(e.startswith("SKILL.md body") for e in result['errors']) else "[FAIL]"
            print(f"  {status} {check_name}: {check_result['body_lines']} lines (body)")
        else:
            status = "[OK]" if check_result else "[FAIL]"
            print(f"  {status} {check_name}")

    # Print errors
    if result['errors']:
        print("\n[ERRORS]")
        for error in result['errors']:
            print(f"  - {error}")

    # Print warnings
    if result['warnings']:
        print("\n[WARNINGS]")
        for warning in result['warnings']:
            print(f"  - {warning}")

    # Overall result
    print()
    if result['passed']:
        print("[PASSED] Skill is compliant")
    else:
        print("[FAILED] Skill has compliance issues")
    print()


def print_summary(results: List[Dict]):
    """Print summary of all compliance checks."""
    print("\n" + "=" * 60)
    print("COMPLIANCE SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    failed = total - passed

    print(f"\nTotal skills checked: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed skills:")
        for result in results:
            if not result['passed']:
                error_count = len(result['errors'])
                warning_count = len(result['warnings'])
                print(f"  - {result['skill_name']}: {error_count} errors, {warning_count} warnings")

    print("\n" + "=" * 60)


def main():
    """Main function."""
    # Find project root
    try:
        current = Path.cwd()
        project_root = None
        for parent in [current] + list(current.parents):
            if (parent / '.claude').is_dir():
                project_root = parent
                break

        if not project_root:
            print("Error: Could not find project root (.claude directory)")
            sys.exit(1)

        checker = ComplianceChecker(project_root)

        # Parse arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--all':
                # Check all skills
                results = checker.check_all_skills()
                for result in results:
                    print_results(result)
                print_summary(results)
                sys.exit(0 if all(r['passed'] for r in results) else 1)
            else:
                # Check specific skill
                skill_name = sys.argv[1]
                result = checker.check_skill(skill_name)
                print_results(result)
                sys.exit(0 if result['passed'] else 1)
        else:
            print("Usage:")
            print("  python check_compliance.py [skill-name]   # Check specific skill")
            print("  python check_compliance.py --all          # Check all skills")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

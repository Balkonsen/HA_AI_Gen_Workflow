#!/usr/bin/env python3
"""
Audit skills directory and compare with CLAUDE.md index.

Usage:
    python audit_skills.py [--project-root PATH]
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set


def find_project_root(start_path: Path = None) -> Path:
    """Find VRP project root by looking for .claude directory."""
    current = start_path or Path.cwd()

    for parent in [current] + list(current.parents):
        if (parent / '.claude').is_dir():
            return parent

    raise FileNotFoundError("Could not find project root (.claude directory)")


def scan_skills_directory(skills_dir: Path) -> Set[str]:
    """Scan .claude/skills/ directory and return set of skill names."""
    skills = set()

    if not skills_dir.exists():
        return skills

    for item in skills_dir.iterdir():
        # Skip hidden directories and files
        if item.name.startswith('.'):
            continue

        # Only include directories with SKILL.md
        if item.is_dir() and (item / 'SKILL.md').exists():
            skills.add(item.name)

    return skills


def parse_skills_md(skills_md_path: Path) -> Set[str]:
    """Parse SKILLS.md and extract skill names from skill sections."""
    skills = set()

    if not skills_md_path.exists():
        return skills

    content = skills_md_path.read_text(encoding='utf-8')

    # Find skill sections
    # Look for pattern: ### N. skill-name
    pattern = r'###\s+\d+\.\s+([a-z0-9-]+)\s*\n'
    matches = re.findall(pattern, content)

    skills = set(matches)
    return skills


def generate_audit_report(actual_skills: Set[str], documented_skills: Set[str]) -> Dict:
    """Generate audit report comparing actual vs documented skills."""
    report = {
        'total_actual': len(actual_skills),
        'total_documented': len(documented_skills),
        'in_sync': actual_skills == documented_skills,
        'missing_from_docs': actual_skills - documented_skills,
        'missing_from_directory': documented_skills - actual_skills,
        'in_both': actual_skills & documented_skills
    }
    return report


def print_report(report: Dict):
    """Print audit report to console."""
    print("=" * 60)
    print("SKILLS AUDIT REPORT")
    print("=" * 60)
    print()

    print(f"Skills in directory:     {report['total_actual']}")
    print(f"Skills in SKILLS.md:     {report['total_documented']}")
    print()

    if report['in_sync']:
        print("[OK] SKILLS.md is in sync with skills directory")
    else:
        print("[!] SKILLS.md is OUT OF SYNC with skills directory")

    print()

    if report['missing_from_docs']:
        print("[WARNING] Skills in directory but NOT in SKILLS.md:")
        for skill in sorted(report['missing_from_docs']):
            print(f"  - {skill}")
        print()

    if report['missing_from_directory']:
        print("[WARNING] Skills in SKILLS.md but NOT in directory:")
        for skill in sorted(report['missing_from_directory']):
            print(f"  - {skill}")
        print()

    if report['in_both']:
        print(f"[OK] Skills properly documented ({len(report['in_both'])}):")
        for skill in sorted(report['in_both']):
            print(f"  - {skill}")
        print()

    print("=" * 60)


def main():
    """Main audit function."""
    # Parse arguments
    project_root = None
    if len(sys.argv) > 1 and sys.argv[1] == '--project-root':
        if len(sys.argv) < 3:
            print("Error: --project-root requires a path argument")
            sys.exit(1)
        project_root = Path(sys.argv[2])

    try:
        # Find project root
        root = find_project_root(project_root)
        print(f"Project root: {root}")
        print()

        # Paths
        skills_dir = root / '.claude' / 'skills'
        skills_md = root / '.claude' / 'SKILLS.md'

        # Scan
        actual_skills = scan_skills_directory(skills_dir)
        documented_skills = parse_skills_md(skills_md)

        # Generate and print report
        report = generate_audit_report(actual_skills, documented_skills)
        print_report(report)

        # Exit code
        sys.exit(0 if report['in_sync'] else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

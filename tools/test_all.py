#!/usr/bin/env python3
"""
test_all.py
===========
Quick validation of all template files, tools, and documentation.

Run from the repository root:
    python3 tools/test_all.py

Checks:
  1. YAML templates parse correctly
  2. No personal data in template files
  3. Python tools have valid syntax
  4. Shell scripts have valid syntax
  5. README anchor links resolve
  6. README tables reference existing files
  7. Template YAML files have comment headers
  8. managed_files.txt references exist
  9. prompts/ files documented in README
  10. CI workflow exists
"""
import yaml
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PASS = 0
FAIL = 0

# This script prints emoji. On Windows the default console encoding is a
# legacy codepage (cp1252), which raises UnicodeEncodeError on the first
# print. Force UTF-8 where the stream supports being reconfigured.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def check(label, ok, detail=""):
    """Record and display the result of a repository validation check.
    
    Parameters:
    	label (str): Description of the check.
    	ok (bool): Whether the check passed.
    	detail (str): Additional information to display when the check fails.
    """
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label} — {detail}")


def test_yaml_templates():
    """Validate root YAML template files and report parsing results with item counts."""
    print("\n📋 YAML Templates")
    for f in sorted(ROOT.glob("*.template.yaml")):
        try:
            content = f.read_text(encoding="utf-8")
            content = re.sub(r"!include.*", '"__directive__"', content)
            data = yaml.safe_load(content)
            count = len(data) if isinstance(data, list) else len(data.get("views", [])) if isinstance(data, dict) else 1
            check(f"{f.name} ({count} items)", True)
        except Exception as e:
            check(f"{f.name}", False, str(e))


def test_yaml_headers():
    """Verify that each root template YAML file contains a comment within its first eight lines."""
    print("\n📝 Template YAML Headers")
    for f in sorted(ROOT.glob("*.template.yaml")):
        lines = f.read_text(encoding="utf-8").splitlines()
        has_header = any(line.startswith("#") for line in lines[:8])
        check(f"{f.name}", has_header, "no comment header in first 8 lines")


def test_no_personal_data():
    """
    Scan root template files for personal data patterns and record any violations.
    """
    print("\n🔒 Personal Data Scan")
    patterns = [
        (r"\b\d{9,12}\b", "Telegram chat ID"),
        (r"[\u0400-\u04FF]", "Cyrillic characters"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "Email address"),
        (r"\b[a-f0-9]{32}\b", "Home Assistant device ID"),
    ]
    for f in sorted(ROOT.glob("*.template.*")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        found = []
        for pat, desc in patterns:
            if re.search(pat, text):
                found.append(desc)
        check(f"{f.name}", not found, f"found: {', '.join(found)}" if found else "")


def test_python_tools():
    """
    Validate the syntax of Python files in the tools directory.
    """
    print("\n🐍 Python Tools")
    for f in sorted(ROOT.glob("tools/*.py")):
        try:
            ast.parse(f.read_text(encoding="utf-8"))
            check(f.name, True)
        except SyntaxError as e:
            check(f.name, False, f"line {e.lineno}: {e.msg}")


def test_shell_scripts():
    """
    Validate the syntax of shell scripts in the tools directory using Bash.
    """
    print("\n🐚 Shell Scripts")
    for f in sorted(ROOT.glob("tools/*.sh")):
        try:
            # Pass a POSIX-style relative path. A native Windows absolute
            # path reaches bash with its separators read as escapes, which
            # mangles the filename and reports every script as missing.
            result = subprocess.run(
                ["bash", "-n", f.relative_to(ROOT).as_posix()],
                capture_output=True, text=True, timeout=5,
                cwd=str(ROOT),
                # Children emit UTF-8; without this, decoding uses the
                # legacy codepage on Windows and raises UnicodeDecodeError.
                encoding="utf-8", errors="replace",
            )
            check(f.name, result.returncode == 0, result.stderr.strip()[:80])
        except Exception as e:
            check(f.name, False, str(e)[:80])


def test_readme_anchors():
    """
    Verify that README fragment links correspond to existing heading anchors.
    """
    print("\n🔗 README Anchor Links")
    readme_path = ROOT / "README.md"
    check("README.md exists", readme_path.exists())
    if not readme_path.exists():
        return
    readme = readme_path.read_text(encoding="utf-8")
    headings = re.findall(r"^#{1,6}\s+(.+)$", readme, re.MULTILINE)
    anchors = set()
    for h in headings:
        anchor = h.lower()
        anchor = re.sub(r"[^\w\s-]", "", anchor)
        anchor = re.sub(r"\s+", "-", anchor.strip())
        anchors.add(anchor)
    links = re.findall(r"\(#[^)]+\)", readme)
    for link in links:
        target = link.strip("()").lstrip("#")
        check(f"anchor #{target}", target in anchors, "heading not found")


def test_readme_tables():
    """
    Verify that backtick-quoted file references in README.md point to existing repository files.
    """
    print("\n📊 README Tables — File References")
    readme_path = ROOT / "README.md"
    if not readme_path.exists():
        check("README.md exists", False, "file not found")
        return
    readme = readme_path.read_text(encoding="utf-8")
    # Files that exist only after user renames templates — skip these
    skip_files = {
        "HOUSE_CONTEXT.md", "automations.yaml", "dashboard.yaml",
        "scripts.yaml", "scenes.yaml", "inventory.txt",
    }
    # Extract backtick-quoted file references (only short paths, not URLs)
    refs = set()
    for match in re.findall(r"`([^`]+)`", readme):
        # Skip URLs, long strings, code snippets, template references
        if len(match) > 80 or "http" in match or "(" in match:
            continue
        # Skip template references and production-only files
        if ".template." in match or match in skip_files:
            continue
        # Only actual file paths
        if match.endswith((".yaml", ".md", ".py", ".sh", ".txt", ".json")):
            refs.add(match)
    for ref in sorted(refs):
        path = ROOT / ref
        check(ref, path.exists(), "file not found")


def test_prompts_documented():
    """
    Verify that the prompts directory exists and each prompt file is documented in the README.
    """
    print("\n📄 Prompts — Existence & Documentation")
    prompts_dir = ROOT / "prompts"
    if not prompts_dir.exists():
        check("prompts directory exists", False, "directory not found")
        return
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    for f in sorted(prompts_dir.iterdir()):
        if f.is_file():
            check(f"prompts/{f.name} exists", True)
            check(f"prompts/{f.name} in README", f.name in readme, "not documented")


def test_managed_files():
    """
    Check that the repository contains the managed files manifest.
    """
    print("\n📦 managed_files.txt")
    mf = ROOT / "tools" / "managed_files.txt"
    check("managed_files.txt exists", mf.exists())
    # Note: managed_files.txt references production files that don't exist in template repo
    # These are only relevant after sync_from_homeassistant.sh is run


def test_ci_workflow():
    """Validate the presence of required CI workflow and CodeRabbit configuration files.
    
    The CodeRabbit configuration is additionally checked for valid YAML syntax.
    """
    print("\n⚙️ CI Workflow")
    wf = ROOT / ".github" / "workflows" / "gitleaks.yml"
    check(".github/workflows/gitleaks.yml exists", wf.exists())
    cr = ROOT / ".coderabbit.yaml"
    check(".coderabbit.yaml exists", cr.exists())
    if cr.exists():
        try:
            yaml.safe_load(cr.read_text(encoding="utf-8"))
            check(".coderabbit.yaml is valid YAML", True)
        except yaml.YAMLError as e:
            check(".coderabbit.yaml is valid YAML", False, str(e))


def test_patterns():
    """Validate that the patterns standardization document exists and contains level-two sections."""
    print("\n📚 Patterns")
    p = ROOT / "patterns" / "standardize.md"
    check("patterns/standardize.md exists", p.exists())
    if p.exists():
        text = p.read_text(encoding="utf-8")
        sections = re.findall(r"^## ", text, re.MULTILINE)
        check(f"patterns/standardize.md has sections", len(sections) > 0, f"found {len(sections)}")


def test_quickstart():
    """Validate that QUICKSTART.md exists, references required repository paths, and contains no Cyrillic characters."""
    print("\n🚀 Quick Start")
    qs = ROOT / "QUICKSTART.md"
    check("QUICKSTART.md exists", qs.exists())
    if qs.exists():
        text = qs.read_text(encoding="utf-8")
        check("QUICKSTART.md references README.md", "README.md" in text)
        check("QUICKSTART.md references prompts/", "prompts/" in text)
        check("QUICKSTART.md references tools/", "tools/" in text)
        # No personal data
        patterns = [
            (r"[\u0400-\u04FF]", "Cyrillic characters"),
        ]
        for pat, desc in patterns:
            check(f"QUICKSTART.md no {desc}", not re.search(pat, text))


def test_instructions_references():
    """
    Verify that INSTRUCTIONS.md exists and references the required repository files.
    """
    print("\n📘 INSTRUCTIONS.md References")
    instr_path = ROOT / "INSTRUCTIONS.md"
    if not instr_path.exists():
        check("INSTRUCTIONS.md exists", False, "file not found")
        return
    instr = instr_path.read_text(encoding="utf-8")
    # Check key file references
    refs = {
        "patterns/standardize.md": "patterns/standardize.md" in instr,
        "tools/check_docs.py": "tools/check_docs.py" in instr,
        "tools/dashboard_audit.py": "tools/dashboard_audit.py" in instr,
        "tools/export_ha_inventory.py": "tools/export_ha_inventory.py" in instr,
        "tools/generate_automations_kb.py": "tools/generate_automations_kb.py" in instr,
    }
    for ref, found in refs.items():
        check(f"INSTRUCTIONS.md → {ref}", found, "reference missing")


def main():
    """
    Run repository validation checks and the Python and shell test suites.
    
    Exits with status 1 if any validation check or test suite fails.
    """
    print(f"🧪 Testing {ROOT.name}\n{'='*40}")
    test_yaml_templates()
    test_yaml_headers()
    test_no_personal_data()
    test_python_tools()
    test_shell_scripts()
    test_readme_anchors()
    test_readme_tables()
    test_prompts_documented()
    test_managed_files()
    test_ci_workflow()
    test_patterns()
    test_quickstart()
    test_instructions_references()
    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")

    # Run full test suite
    print(f"\n{'='*40}")
    print("Running full test suite...")
    print(f"{'='*40}")

    # Python unit tests
    print("\n🐍 Python Unit Tests (tests/test_python_tools.py)")
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tests" / "test_python_tools.py")],
            cwd=str(ROOT), timeout=30
        )
        py_pass = r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  ❌ Python tests failed: {e}")
        py_pass = False

    # Shell unit tests
    print("\n🐚 Shell Unit Tests (tests/test_shell_tools.sh)")
    try:
        r = subprocess.run(
            ["bash", "tests/test_shell_tools.sh"],
            cwd=str(ROOT), timeout=30
        )
        sh_pass = r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  ❌ Shell tests failed: {e}")
        sh_pass = False

    if not py_pass or not sh_pass or FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

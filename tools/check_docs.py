#!/usr/bin/env python3
"""
check_docs.py
=============
Validates that every automation alias in automations.yaml is mentioned in
HOUSE_CONTEXT.md, and that no automation-like aliases documented in
HOUSE_CONTEXT.md are stale (i.e. no longer exist in automations.yaml).

Run from the repository root:
    python3 tools/check_docs.py

Exit codes:
    0 — all automations documented, no stale aliases
    1 — missing or stale aliases found

Customization
-------------
To ignore specific aliases (e.g. intentionally disabled automations that
you still want to keep mentioned in HOUSE_CONTEXT.md), add them to the
IGNORE_ALIASES set below.
"""

import yaml
import re
import sys
from typing import Any

# These tools print emoji in their status output. On Windows the default
# stdout encoding is a legacy codepage (cp1252), which raises
# UnicodeEncodeError - and does so most often when the output is captured by
# a parent process rather than shown in a terminal. Force UTF-8 where the
# stream supports being reconfigured.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


class HASafeLoader(yaml.SafeLoader):
    """SafeLoader subclass that handles Home Assistant tags."""
    pass


def _ha_constructor(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node) -> Any:
    """Handle Home Assistant tags by returning a placeholder."""
    return f"__{tag_suffix}__"


# Register multi-constructor for Home Assistant tags
HASafeLoader.add_multi_constructor("!", _ha_constructor)

# Add aliases here that should be excluded from stale-alias detection.
# Example: aliases of permanently disabled automations that you still
# want to document in HOUSE_CONTEXT.md.
IGNORE_ALIASES: set[str] = set()


def main() -> None:
    """
    Validate that automation aliases in automations.yaml are documented consistently in HOUSE_CONTEXT.md.
    
    Reports automation aliases missing from the documentation and documented automation-like aliases that are absent from the YAML configuration. Exits with code 0 when no inconsistencies are found, or code 1 when a file cannot be read, YAML cannot be parsed, or inconsistencies are detected.
    """
    try:
        from pathlib import Path
        content = Path("automations.yaml").read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading automations.yaml: {e}")
        sys.exit(1)

    # Strip HA-specific !include directives so pyyaml can parse the file
    content = re.sub(r"!include.*", '"__directive__"', content)

    try:
        automations = yaml.load(content, Loader=HASafeLoader)
    except yaml.YAMLError as e:
        print(f"Error parsing automations.yaml: {e}")
        sys.exit(1)

    if not isinstance(automations, list):
        print("Error: automations.yaml is not a list. Nothing to check.")
        sys.exit(0)

    aliases = {
        a.get("alias", "").strip()
        for a in automations
        if isinstance(a, dict) and a.get("alias")
    }

    try:
        from pathlib import Path
        doc = Path("HOUSE_CONTEXT.md").read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading HOUSE_CONTEXT.md: {e}")
        sys.exit(1)

    # 1. Check for missing documentation
    #    Every automation alias must be mentioned at least once in HOUSE_CONTEXT.md
    missing = [alias for alias in aliases if alias not in doc]

    # 2. Check for potentially stale documentation
    #    Find backtick-quoted phrases that look like automation aliases
    #    (format: `Room: Description`)
    potential_aliases = set(
        re.findall(r"`([A-Z][a-zA-Z0-9\s]+:\s[^`\n]+)`", doc)
    )
    stale = [
        p.strip()
        for p in potential_aliases
        if p.strip() not in IGNORE_ALIASES
        and " " in p.strip()
        and not p.strip().startswith("sensor.")
        and not p.strip().startswith("binary_sensor.")
        and p.strip() not in aliases
    ]

    has_errors = False

    if missing:
        has_errors = True
        print("\n❌ MISSING in HOUSE_CONTEXT.md (automations with no documentation):")
        for m in sorted(missing):
            print(f"  - {m}")

    if stale:
        has_errors = True
        print("\n⚠️  STALE in HOUSE_CONTEXT.md (aliases not found in automations.yaml):")
        for s in sorted(stale):
            print(f"  - {s}")
        print("\n  Tip: add these to IGNORE_ALIASES in check_docs.py if they are")
        print("  intentionally disabled but should stay documented.")

    if not has_errors:
        print("✅ All automations are documented and no stale aliases found.")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
write_yaml_template.py
======================
Writes large YAML template files that exceed the opencode JSON payload limit.

Usage:
    python3 tools/write_yaml_template.py <output_file> <source_file>

    python3 tools/write_yaml_template.py automations-basic.template.yaml /tmp/basic_content.yaml
    python3 tools/write_yaml_template.py dashboard-basic.template.yaml /tmp/dashboard_content.yaml

The source file must be valid YAML or YAML-like content.
Output is written verbatim (no re-formatting) to preserve exact formatting.

This script exists because opencode's write/bash tools hit JSON parsing limits
when passing content longer than ~50KB as parameters. By writing content to a
temporary file first and then copying it, we bypass the payload limit.
"""

import sys
import shutil
import yaml
from pathlib import Path


def main() -> None:
    """
    Validate a YAML source file and copy it to the specified output path.
    
    The command-line arguments must provide the output path followed by the source
    path. Exits with status 1 if the arguments are invalid, the source cannot be
    read, the YAML is invalid, or the output cannot be written.
    """
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    output_path = Path(sys.argv[1])
    source_path = Path(sys.argv[2])

    if not source_path.exists():
        print(f"Error: source file not found: {source_path}")
        sys.exit(1)

    try:
        content = source_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {source_path}: {e}")
        sys.exit(1)

    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"Error: source file contains invalid YAML: {e}")
        sys.exit(1)

    try:
        shutil.copy2(source_path, output_path)
        print(f"Written: {output_path} ({output_path.stat().st_size} bytes)")
    except Exception as e:
        print(f"Error writing {output_path}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

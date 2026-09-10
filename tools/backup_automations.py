#!/usr/bin/env python3
"""
backup_automations.py
=====================
Creates point-in-time YAML backups of specific automations from automations.yaml.

Usage:
    python3 tools/backup_automations.py <automation_id> [<automation_id2> ...]

Examples:
    python3 tools/backup_automations.py kitchen_main_light_toggle
    python3 tools/backup_automations.py bedroom_motion_on bedroom_motion_off

Backups are saved to the backups/ directory with a timestamp prefix:
    backups/20231024_153000_kitchen_main_light_toggle.yaml

The backups/ directory is gitignored. Use git to track intentional snapshots
by committing specific backup files when needed.
"""

import sys
import yaml
from datetime import datetime
from pathlib import Path


def main() -> None:
    """Back up the requested automations from ``automations.yaml`` into timestamped YAML files.
    
    Command-line arguments specify the automation IDs to back up. Exits with status 1 when
    arguments are missing, the source file is invalid, a backup cannot be written, or an
    requested automation ID is not found.
    """
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target_ids = set(sys.argv[1:])

    try:
        content = Path("automations.yaml").read_text(encoding='utf-8')
        automations = yaml.safe_load(content)
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading automations.yaml: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: automations.yaml contains invalid YAML: {e}")
        sys.exit(1)

    if not isinstance(automations, list):
        print("Error: automations.yaml is not a list.")
        sys.exit(1)

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    found_ids: set[str] = set()

    for auto in automations:
        if not isinstance(auto, dict):
            continue
        auto_id = str(auto.get("id", ""))
        if auto_id in target_ids:
            found_ids.add(auto_id)
            filename = backup_dir / f"{timestamp}_{auto_id}.yaml"
            try:
                filename.write_text(
                    yaml.dump([auto], sort_keys=False, allow_unicode=True),
                    encoding='utf-8',
                )
            except OSError as e:
                print(f"Error writing backup {filename}: {e}")
                sys.exit(1)
            print(f"✅ Backed up: {filename}")

    missing = target_ids - found_ids
    if missing:
        for mid in sorted(missing):
            print(f"⚠️  Not found in automations.yaml: {mid}")
        sys.exit(1)


if __name__ == "__main__":
    main()

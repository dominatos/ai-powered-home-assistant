#!/usr/bin/env python3
"""
dashboard_audit.py
==================
Consolidated analysis scripts for reviewing dashboard.yaml against
ha_device_inventory.json.

Run from the repo root:
    python3 tools/dashboard_audit.py [repo_root_path]

If no path is given, uses the current directory.

Sections:
  1. Validate dashboard entity references against inventory
  2. Find all temperature/humidity sensors by room
  3. Find all light entities by room
  4. Find all input_boolean helpers
"""

import json
import sys
from pathlib import Path
from typing import Any

import yaml

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


HASafeLoader.add_multi_constructor("!", _ha_constructor)

REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
INVENTORY = REPO / "ha_device_inventory.json"
DASHBOARD = REPO / "dashboard.yaml"


def load_inventory() -> dict:
    """
    Load and validate the Home Assistant device inventory.
    
    Returns:
        dict: The parsed inventory containing an ``entities`` list of mappings.
    
    Raises:
        SystemExit: If the inventory cannot be read or decoded, or if its structure is invalid.
    """
    try:
        content = INVENTORY.read_text(encoding='utf-8')
        data = json.loads(content)
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {INVENTORY}: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: ha_device_inventory.json contains invalid JSON: {e}")
        sys.exit(1)
    
    if not isinstance(data, dict):
        print("Error: ha_device_inventory.json 'entities' must be a list of mappings.")
        sys.exit(1)
        
    entities = data.get("entities")
    if not isinstance(entities, list) or not all(isinstance(e, dict) for e in entities):
        print("Error: ha_device_inventory.json 'entities' must be a list of mappings.")
        sys.exit(1)
    
    return data


def load_dashboard() -> str:
    """
    Read the dashboard configuration from `dashboard.yaml`.

    Returns:
        str: The dashboard file contents.
    """
    try:
        return DASHBOARD.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {DASHBOARD}: {e}")
        sys.exit(1)


def _extract_entity_refs(data: Any, refs: set[str] | None = None) -> set[str]:
    """
    Recursively extract entity references from a parsed YAML structure.

    Scans for:
      - ``entity`` keys (scalar values)
      - ``entity_id`` keys (scalar values, including inside ``target`` blocks)
      - ``entities`` lists (items may be strings or dicts with an ``entity`` key)

    Returns:
        set[str]: All discovered entity ID strings.
    """
    if refs is None:
        refs = set()

    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("entity", "entity_id") and isinstance(value, str):
                refs.add(value)
            elif key == "entities" and isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        refs.add(item)
                    elif isinstance(item, dict):
                        _extract_entity_refs(item, refs)
            else:
                _extract_entity_refs(value, refs)
    elif isinstance(data, list):
        for item in data:
            _extract_entity_refs(item, refs)

    return refs


# ── 1. Validate dashboard entity references ─────────────────────────────────
def validate_entity_refs() -> None:
    """Validate dashboard entity references against the recorded inventory and report missing entries."""
    print("=" * 70)
    print("1. VALIDATE DASHBOARD ENTITY REFERENCES")
    print("=" * 70)

    if not INVENTORY.exists():
        print("  SKIPPED — ha_device_inventory.json not found (run export first).")
        print()
        return
    if not DASHBOARD.exists():
        print("  SKIPPED — dashboard.yaml not found.")
        print()
        return

    data = load_inventory()
    entities = data.get("entities", [])
    inv_ids = {e.get("entity_id") for e in entities if "entity_id" in e}

    dash_text = load_dashboard()
    try:
        dash_data = yaml.load(dash_text, Loader=HASafeLoader)
    except yaml.YAMLError as e:
        print(f"  ERROR parsing dashboard.yaml: {e}")
        print()
        return

    ent_refs = _extract_entity_refs(dash_data)
    print(f"  Entities referenced in dashboard.yaml: {len(ent_refs)}")

    missing = []
    for ref in sorted(ent_refs):
        if ref not in inv_ids:
            print(f"    NOT IN INVENTORY: {ref}")
            missing.append(ref)

    if not missing:
        print("  All dashboard entity references found in inventory ✓")
    else:
        print(
            f"\n  {len(missing)} reference(s) not in inventory "
            "(may be template sensors defined in configuration.yaml)"
        )
    print()


# ── 2. Find all temperature/humidity sensors by room ────────────────────────
def find_temp_humidity_sensors() -> None:
    """List enabled temperature and humidity sensor entities grouped by area."""
    print("=" * 70)
    print("2. TEMPERATURE & HUMIDITY SENSORS BY ROOM")
    print("=" * 70)

    if not INVENTORY.exists():
        print("  SKIPPED — ha_device_inventory.json not found.")
        print()
        return

    data = load_inventory()
    entities = data.get("entities", [])

    for ent in entities:
        eid = ent.get("entity_id", "")
        if ("temperature" in eid or "humidity" in eid) and "sensor." in eid:
            if not ent.get("disabled_by"):
                area = ent.get("area") or {}
                aname = area.get("area_name", "—") if isinstance(area, dict) else "—"
                print(f"  {eid:65s} | {aname}")
    print()


# ── 3. Find all light entities by room ──────────────────────────────────────
def find_light_entities() -> None:
    """List enabled light entities grouped by their recorded area."""
    print("=" * 70)
    print("3. ALL LIGHT ENTITIES BY ROOM")
    print("=" * 70)

    if not INVENTORY.exists():
        print("  SKIPPED — ha_device_inventory.json not found.")
        print()
        return

    data = load_inventory()
    entities = data.get("entities", [])

    for ent in entities:
        eid = ent.get("entity_id", "")
        if eid.startswith("light.") and not ent.get("disabled_by"):
            area = ent.get("area") or {}
            aname = area.get("area_name", "—") if isinstance(area, dict) else "—"
            print(f"  {eid:55s} | {aname}")
    print()


# ── 4. Find installed custom frontend cards ─────────────────────────────────
def find_custom_cards() -> None:
    """List enabled Home Assistant update entities associated with configured custom frontend card integrations."""
    print("=" * 70)
    print("4. INSTALLED CUSTOM FRONTEND CARDS (HACS)")
    print("=" * 70)

    if not INVENTORY.exists():
        print("  SKIPPED — ha_device_inventory.json not found.")
        print()
        return

    data = load_inventory()
    entities = data.get("entities", [])
    card_keywords = [
        "mushroom", "bubble", "mini_graph", "card_mod", "foundry",
        "clock", "schedule_state", "digital_clock", "wall_clock", "wizard",
    ]

    for ent in entities:
        eid = ent.get("entity_id", "")
        if "update." in eid and any(k in eid.lower() for k in card_keywords):
            if not ent.get("disabled_by"):
                print(f"  {eid}")
    print()


# ── 5. Find all input_boolean helpers ───────────────────────────────────────
def find_input_booleans() -> None:
    """Print all enabled input Boolean helpers and their names."""
    print("=" * 70)
    print("5. ALL INPUT_BOOLEAN HELPERS")
    print("=" * 70)

    if not INVENTORY.exists():
        print("  SKIPPED — ha_device_inventory.json not found.")
        print()
        return

    data = load_inventory()
    entities = data.get("entities", [])

    for ent in entities:
        eid = ent.get("entity_id", "")
        if eid.startswith("input_boolean.") and not ent.get("disabled_by"):
            name = ent.get("original_name", "") or ent.get("name", "")
            print(f"  {eid:55s} | {name}")
    print()


def main() -> None:
    """Run all dashboard audit reports and display repository file status."""
    print(f"Repo root : {REPO.resolve()}")
    print(f"Inventory : {INVENTORY} ({'exists' if INVENTORY.exists() else 'MISSING — run export_ha_inventory.sh first'})")
    print(f"Dashboard : {DASHBOARD} ({'exists' if DASHBOARD.exists() else 'MISSING'})")
    print()

    validate_entity_refs()
    find_temp_humidity_sensors()
    find_light_entities()
    find_custom_cards()
    find_input_booleans()


if __name__ == "__main__":
    main()

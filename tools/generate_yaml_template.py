#!/usr/bin/env python3
"""
generate_yaml_template.py
=========================
Generates YAML template files from Python data structures.

This is the recommended pattern for writing large YAML template files
that exceed opencode's JSON payload limit (~50KB).

Usage:
    1. Edit this script to define your automations content
    2. Run: python3 tools/generate_yaml_template.py <basic|advanced>
    3. Or pipe to file: python3 tools/generate_yaml_template.py basic > auto.yaml

Pattern for writing large files in opencode:
    1. Write a Python script to /tmp/gen_*.py
    2. Execute it with: python3 /tmp/gen_*.py > target_file.yaml
    3. Verify with: python3 -c "import yaml; yaml.safe_load(open('target_file.yaml'))"
"""

import sys
import yaml


def generate_automations_basic() -> str:
    """Generate YAML content for a sample kitchen door automation.
    
    Returns:
        str: Block-style YAML containing the automation configuration.
    """
    automations = []

    # ── SECTION 1: SAFETY & SENSORS ──

    automations.append({
        "id": "1778264755475",
        "alias": "Kitchen: Main Light on Door Open",
        "description": "Triggered when the kitchen door opens from 17:00 to 07:00; turns on the kitchen light at full brightness if it is currently off.",
        "triggers": [
            {
                "type": "opened",
                "device_id": "<device_id_here>",
                "entity_id": "<your_door_contact_sensor>",
                "domain": "binary_sensor",
                "trigger": "device",
            }
        ],
        "conditions": [
            {
                "type": "is_illuminance",
                "condition": "device",
                "device_id": "<device_id_here>",
                "entity_id": "<your_luminance_sensor>",
                "domain": "sensor",
                "below": 200,
                "enabled": False,
            },
            {
                "condition": "device",
                "type": "is_off",
                "device_id": "<device_id_here>",
                "entity_id": "<your_main_light>",
                "domain": "light",
            },
            {"condition": "time", "after": "17:00:00", "before": "07:00:00"},
        ],
        "actions": [
            {
                "type": "turn_on",
                "device_id": "<device_id_here>",
                "entity_id": "<your_main_light>",
                "domain": "light",
                "brightness_pct": 100,
            },
            {
                "device_id": "<device_id_here>",
                "domain": "button",
                "entity_id": "<your_tablet_wake_button>",
                "type": "press",
            },
            {
                "device_id": "<device_id_here>",
                "domain": "button",
                "entity_id": "<your_tablet_dismiss_lock_button>",
                "type": "press",
            },
            {
                "device_id": "<device_id_here>",
                "domain": "button",
                "entity_id": "<your_tablet_open_dashboard_button>",
                "type": "press",
            },
            {
                "alias": "Mark tablet screen as awake",
                "action": "input_boolean.turn_on",
                "target": {"entity_id": "<your_tablet_screen_awake_boolean>"},
                "data": {},
            },
        ],
        "mode": "single",
    })

    # Add more automations here following the same pattern...
    # automations.append({...})

    return yaml.dump(automations, sort_keys=False, allow_unicode=True, default_flow_style=False)


def generate_automations_advanced() -> str:
    """Generate YAML content for the advanced automation template.
    
    Returns:
    	str: YAML representation of an empty automation list.
    """
    automations = []
    # Add advanced automations here
    return yaml.dump(automations, sort_keys=False, allow_unicode=True, default_flow_style=False)


def main():
    """
    Run the selected YAML automation template generator from the command line.
    
    Exits with status 1 when no target is provided or when the target is unsupported.
    """
    if len(sys.argv) < 2:
        print("Usage: python3 generate_yaml_template.py <basic|advanced>")
        sys.exit(1)

    target = sys.argv[1]

    generators = {
        "basic": generate_automations_basic,
        "advanced": generate_automations_advanced,
    }

    if target not in generators:
        print(f"Unknown target: {target}")
        print(f"Available: {', '.join(generators.keys())}")
        sys.exit(1)

    content = generators[target]()
    print(content)


if __name__ == "__main__":
    main()

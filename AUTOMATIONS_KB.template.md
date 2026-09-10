# Home Assistant Automations Knowledge Base

This document provides a human-readable summary of all automations in `automations.yaml`.
It is the quick-reference index for aliases, IDs, triggers, conditions, and key actions.
**Keep this file up to date whenever automations are added, changed, or removed.**

> [!TIP]
> You can automatically generate or update this file at any time by running:
> `python3 tools/generate_automations_kb.py`
>
> If you manually edit this file, follow the format below:

---

## Room: Automation Alias Example
- **ID**: `unique_automation_id`
- **Description**: Brief explanation of what the automation does and any fallback behaviors.

### Triggers
- What starts the automation (e.g., Motion sensor `binary_sensor.room_motion` turns **on**)

### Conditions
- Required state for the automation to run (e.g., Time is after 20:00)

### Actions
- Key actions performed (e.g., `light.turn_on` on `light.room_light`)

---

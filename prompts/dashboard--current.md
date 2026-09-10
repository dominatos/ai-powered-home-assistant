# Context Initialization (Dashboard Editor)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: Extend or improve the existing Lovelace dashboard (`dashboard.yaml`) for Home Assistant.
The dashboard already exists and is fully functional. Do NOT create a new file or replace it wholesale.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `HOUSE_CONTEXT.md` — rooms, devices, and key automation relationships
2. `ha_device_inventory.json` / `inventory.txt` — exact entity IDs
3. `dashboard.yaml` — the active, mature dashboard to modify

# Current Dashboard Structure

The dashboard lives in `dashboard.yaml` (not `ui-lovelace.yaml`).
It has the following views:

| # | Title      | Path          | Icon               | Purpose |
|---|-----------|---------------|--------------------|---------|
| 1 | Overview   | overview      | mdi:home           | Clock, presence summary, weather, master controls (All Lights Off), active alerts (conditional) |
| 2 | Kitchen    | kitchen       | mdi:silverware     | Lights, media, climate (A/C + fan), sensors, appliances, automation toggles |
| 3 | Bedroom    | bedroom       | mdi:bed            | Lights, controls grid, media (conditional), A/C readings, sensors |
| 4 | Bathroom   | bathroom      | mdi:shower         | Light, sensors (motion, door, temp, humidity), occupied status |
| 5 | Climate    | climate       | mdi:thermometer    | Thermostat (status, schedule helpers, boost controls), temperature/humidity graphs |
| 6 | Appliances | appliances    | mdi:washing-machine| Washing machine, water safety (leak sensors + valve), gas sensor |
| 7 | Energy     | energy        | mdi:lightning-bolt | Monthly consumption, circuit monitors, power history, consumer graphs |
| 8 | Settings   | settings      | mdi:cog            | TTS & notification toggles, bedroom internals, thermostat internals, system controls |

[Fill in or replace with your actual views]

# Design Conventions (already established)
- Section headers inside views use `# ── SECTION NAME ──` comments
- Cards use `type: grid` with `columns: 2` for control buttons
- `type: entities` for grouped state displays with `show_header_toggle: false`
- `type: glance` for compact sensor rows
- `type: conditional` to hide cards when entities are unavailable or in a specific state
- `tap_action: call-service / automation.trigger` for dashboard-driven automation buttons
- Entity IDs are real Zigbee/Z2M addresses (e.g. `binary_sensor.0xa4c138...`); always confirm IDs against `ha_device_inventory.json` before adding new cards

# Custom Frontend Cards (HACS)
Common cards in use (update with your actual installed cards):
- `type: custom:mushroom-*` — compact, modern cards for entities, climate, media, etc.
- `type: custom:mini-graph-card` — history sparkline graphs for sensors
- `type: custom:clock-weather-card` — combined clock and weather overview
- `type: custom:scheduler-card` — thermostat/timer schedule UI

# Verification Step
After any change to `dashboard.yaml`, run:
```bash
python3 tools/dashboard_audit.py
```
to validate entity references against the latest inventory.

Also run after any automation change:
```bash
python3 tools/check_docs.py
```
to ensure all automations are documented and no stale aliases remain.

# Task Instructions
Analyze the existing `dashboard.yaml` and the house context, then suggest or implement targeted additions or improvements. Do NOT:
- Replace the entire file
- Remove existing cards or sections without explicit approval
- Create a separate `ui-lovelace.yaml`

[INSERT_YOUR_CURRENT_TASK_HERE]

Present all proposed changes to the user for review before writing them to the file.

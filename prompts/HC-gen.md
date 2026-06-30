# Context Initialization (House Context Generation)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to generate the initial `HOUSE_CONTEXT.md` file from scratch based on my existing Home Assistant configuration.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Primary Data Sources for Generation:
1. `ha_device_inventory.json` / `inventory.txt` (Contains all known entities and devices)
2. `automations.yaml` (Contains behavioral logic that implies physical relationships)
3. `configuration.yaml`, `scripts.yaml`, `scenes.yaml` (Additional context)
4. `HOUSE_CONTEXT.template.md` (The structural template you MUST follow for the output)

# Task Instructions
User:
Please analyze my exported inventory and my existing `automations.yaml` to reverse-engineer the physical layout of my house. 

1. **Identify Rooms:** Look at entity ID prefixes/suffixes (e.g., `light.living_room_lamp`, `sensor.kitchen_temperature`) and group them into logical rooms.
2. **Identify Devices:** For each room, list the lights, sensors, climate controls, media players, and smart plugs you can find in the inventory.
3. **Identify Critical Automations:** Analyze `automations.yaml` to find high-level behaviors or safety rules (e.g., a water leak sensor shutting off a main valve, or a master "goodnight" switch). Add these to the "Critical Automations" section.
4. **Identify Quirks:** Look for unusual entity groupings or conditions in automations that suggest physical quirks (e.g., a motion sensor that only triggers at night, suggesting a bedroom or hallway setup).

# Output Expectations
- Output the fully generated content for `HOUSE_CONTEXT.md`.
- Use the exact structure defined in `HOUSE_CONTEXT.template.md` (General Quirks, Rooms & Layout, Critical Automations).
- If an entity's location is ambiguous, make your best logical guess based on its name and related automations, but add a `[?]` next to it so I know to review it.
- Present the final proposed `HOUSE_CONTEXT.md` text to me for review. Once I approve it, write it to the `HOUSE_CONTEXT.md` file.

[INSERT_ADDITIONAL_HINTS_HERE - e.g., "Note: The 'studio' is actually my home office on the second floor"]

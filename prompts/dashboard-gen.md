# Context Initialization (Dashboard Generator)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to generate a beautiful, organized Lovelace dashboard configuration for Home Assistant based on the physical layout of the house.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `HOUSE_CONTEXT.md` (Provides the rooms and the devices inside them)
2. `ha_device_inventory.json` / `inventory.txt` (Provides exact entity IDs)
3. `ui-lovelace.yaml` (The target file to create/update)

# Task Instructions
User:
Please read `HOUSE_CONTEXT.md` to understand the rooms in my house and the devices that belong in each room. 

I want you to generate a `ui-lovelace.yaml` configuration that gives me a clean, modern dashboard.
Follow these design rules:
1. **Views (Tabs):** Create a main "Home" view for critical controls (alarms, master off switches, outside weather), and then create a separate View for each major room (e.g., Living Room, Kitchen, Bedroom).
2. **Cards:** Use appropriate cards for the entities. 
   - Use `light` cards for dimmable bulbs.
   - Use `thermostat` cards for climate entities.
   - Use `glance` or `entities` cards to group sensors (temperature, humidity, motion).
   - Use `custom:mushroom-person-card` or standard `badge` equivalents for presence if you see person entities.
3. **Organization:** Use `vertical-stack` and `horizontal-stack` cards to keep the UI clean and prevent it from looking like a massive list of buttons. Group lighting together, climate together, and sensors together within each room view.

# Output Expectations
- Generate the full YAML required for this dashboard.
- Present it to me for review. 
- Once I approve it, write it to `ui-lovelace.yaml` in the root of the repository (or the designated dashboard folder if I specify one).

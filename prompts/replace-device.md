# Context Initialization (Device Migrator)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: I have replaced a broken or old smart device with a new one. I need you to find every reference to the old entity ID and seamlessly swap it with the new entity ID across my entire configuration.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `automations.yaml`
2. `scripts.yaml`
3. `scenes.yaml`
4. `HOUSE_CONTEXT.md`
5. Dashboard files (if applicable)

# Task Instructions
User:
I have replaced an old device. 
> Old Entity ID: `[INSERT_OLD_ENTITY_ID_HERE]`
> New Entity ID: `[INSERT_NEW_ENTITY_ID_HERE]`

Please perform the following steps:
1. **Search and Replace:** Scan `automations.yaml`, `scripts.yaml`, `scenes.yaml`, and any other relevant configuration files. Find every instance of the old entity ID and replace it with the new one.
2. **Update Context:** Open `HOUSE_CONTEXT.md` and update the documentation for the room where this device lives. Ensure the new entity ID is listed and any descriptions of the physical device are accurate (e.g., if I swapped a Wi-Fi bulb for a Zigbee bulb, note it).
3. **Check for Features:** If the old entity was just a basic switch, but the new entity is a dimmer or has color control, let me know! Propose ways we could enhance the existing automations to use the new features.

# Output Expectations
- Do NOT apply the changes immediately.
- Give me a summary of all the files and automations that will be affected by this swap.
- Show me the proposed updates for `HOUSE_CONTEXT.md`.
- Wait for my approval before making the changes to the files.

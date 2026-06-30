# Context Initialization (New Automation Ideation)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to analyze the existing device inventory and current automations to brainstorm and invent completely new, highly useful automations.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `ha_device_inventory.json` / `inventory.txt`
2. `HOUSE_CONTEXT.md`
3. `automations.yaml`

# Task Instructions
User:
Please put on your "Creative Inventor" hat. I want you to look closely at all the devices I own across my inventory and `HOUSE_CONTEXT.md`, and then look at what I am currently doing with them in `automations.yaml`.

Your goal is to propose 5 completely new, intelligent automations that I haven't thought of yet. 

Consider the following angles inspired by community best practices:
1. **Adaptive & Circadian Lighting:** Using lux sensors or time of day to automatically adjust color temperature and brightness when lights are triggered.
2. **Climate & Energy Synergy:** Pausing HVAC/AC when windows are open, or suggesting ways to run heavy appliances when energy is cheap.
3. **Advanced Presence:** Combining motion sensors with other room activity (TV power, humidity) to create robust occupancy detection, preventing lights from turning off while the room is occupied.
4. **Maintenance & Chores:** Notifying me when a sensor's battery is low, a washing machine cycle is done (via power monitoring), or a door has been left open for too long.
5. **Seamless Routines:** Creating highly personalized Morning (gradual wake-up, blind opening) or Evening (Goodnight scene, arming alarms, dimming) routines based on my habits.
6. **Underutilized Sensors:** Are there sensors (like humidity, vibration, or power monitoring) that are rarely used in my current automations?

# Output Expectations
- Do NOT modify `automations.yaml` yet.
- Present a list of 5 detailed ideas. For each idea, explain:
  - **The Concept:** What it does and why it's cool or useful.
  - **The Logic:** Exactly what triggers it, and under what conditions.
  - **The Required Entities:** Which of my existing entities it will use.
- Wait for me to select which of these ideas I like. Once I choose one (or more), I will ask you to write the full YAML for it.

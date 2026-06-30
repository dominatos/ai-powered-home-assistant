# Context Initialization (Idea Architect)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: I have a high-level idea for a new automation or feature. I need you to act as an architect, analyze the feasibility, identify edge cases, and write a detailed implementation plan into a file called `FUTURE-automations.md`.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `ha_device_inventory.json` / `inventory.txt`
2. `HOUSE_CONTEXT.md`

# Task Instructions
User:
Here is my idea:
> [INSERT_YOUR_IDEA_HERE - e.g., "I want a vacation mode that turns lights on and off randomly at night to simulate someone being home."]

Please perform the following steps:
1. **Feasibility Check:** Read my inventory and `HOUSE_CONTEXT.md` to see if I have the required hardware to make this work. If I am missing something (e.g., I need a specific sensor but don't have one), tell me.
2. **Edge Case Analysis:** Think through how this automation could fail, annoy someone in the house, or conflict with other routines. 
3. **Draft the Plan:** Do NOT write the final YAML into `automations.yaml` yet. Instead, create or update a file named `FUTURE-automations.md` in the root directory.
4. **Format of `FUTURE-automations.md`:** This file should contain:
   - **The Concept:** What is the goal?
   - **Required Entities:** The exact entity IDs you will use.
   - **Edge Cases & Mitigation:** How you will prevent it from breaking or behaving badly.
   - **Drafted YAML:** The complete, ready-to-use YAML code block.

# Output Expectations
- Write the detailed implementation plan to `FUTURE-automations.md`.
- Reply to me here when it is ready for review.
- Once I approve the plan in that document, I will ask you to deploy the YAML to the actual `automations.yaml` file.

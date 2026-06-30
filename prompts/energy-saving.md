# Context Initialization (Energy Efficiency Auditor)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to audit all existing automations and the physical layout to find opportunities to save energy and reduce wasted electricity.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `automations.yaml`
2. `HOUSE_CONTEXT.md`

# Task Instructions
User:
Please analyze `automations.yaml` and cross-reference with `HOUSE_CONTEXT.md`. Put on your "Energy Auditor" hat and identify areas where energy is likely being wasted.

Look specifically for the following patterns:
1. **Missing Timeouts:** Lights or appliances that turn on automatically but have no reliable mechanism to turn off when the room is empty.
2. **Vampire Drain:** Smart plugs controlling TVs, media centers, or chargers that could be completely powered off when the house is empty or at night.
3. **Climate Waste:** HVAC or AC units that are allowed to run while window or door sensors in the same room are open, or when the house is empty.
4. **Daylight Waste:** Lights that trigger on motion during the daytime because they lack an illuminance (lux) or sun condition.

# Output Expectations
- Do NOT modify `automations.yaml` immediately.
- Present a detailed report listing your findings. Group them by severity (High Potential Savings vs. Minor Optimizations).
- For each finding, propose the specific YAML changes or new automations required to fix the issue.
- Wait for my approval on which proposals you should implement.

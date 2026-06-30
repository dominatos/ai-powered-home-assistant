# Context Initialization (Naming Convention Fixer)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to standardize the naming and descriptions of all existing automations in `automations.yaml` to follow a strict and readable convention.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `automations.yaml`
2. `HOUSE_CONTEXT.md` (to verify room names)

# Task Instructions
User:
Please analyze all automations in `automations.yaml`. I want to standardize the `alias` and `description` fields for every automation based on what it actually does and where it is located.

Follow these strict naming rules:
1. **Alias Convention:** Every automation `alias` must follow the format: `[Room/Area]: [Action or Trigger]`.
   - *Example Good:* `Kitchen: Turn on main light with motion`
   - *Example Good:* `System: Notify when Home Assistant starts`
   - *Example Good:* `Bedroom: Turn off AC when window opens`
   - *Example Bad:* `kitchen motion light`
   - *Example Bad:* `auto off`
2. **Determine the Room:** Infer the room from the entity IDs used in the automation's triggers or actions. Cross-reference with `HOUSE_CONTEXT.md` if needed.
3. **Detailed Descriptions:** If the `description` field is empty or vague, write a detailed description explaining exactly what triggers it, what conditions must be met, and what actions it performs.
   - *Example:* `description: "Turns on the kitchen main light when motion is detected, but only if the illuminance is below 50 lux. Turns off after 5 minutes of no motion."`
4. **Preserve Logic:** Do NOT change any triggers, conditions, actions, or `id` fields. ONLY change the `alias` and `description`.

# Output Expectations
- Propose the changes for me to review first. Show me a before/after list of the aliases that will be changed.
- Once I approve, apply the changes directly to `automations.yaml` by modifying the `alias` and `description` fields.

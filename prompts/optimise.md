# Context Initialization (Logic Optimization Auditor)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to audit existing automations in `automations.yaml` to optimize them, improve robustness, and reduce complexity by merging similar logic.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `automations.yaml`
2. `HOUSE_CONTEXT.md`

# Task Instructions
User:
Please analyze all automations in `automations.yaml`. Put on your "Optimization" hat and identify areas where we can significantly improve the logic.

Look specifically for the following opportunities:
1. **Merging Automations:** Find multiple automations that handle the same entities (e.g., one for "turn on", one for "turn off", or different buttons on the same remote) and propose merging them into a single automation using Trigger IDs and `choose` blocks.
2. **Improving Robustness:** Identify logic that relies purely on single state transition events without considering what happens if Home Assistant restarts, or if the event is missed. Propose safer logic (like checking state on startup, or ensuring 'off' paths exist for every 'on' path).
3. **Template Simplification:** Find complex or repetitive YAML conditions/actions and replace them with cleaner, more efficient Jinja2 templates.
4. **Reducing Network Spam:** Identify actions that blindly send commands (e.g., turning off a light that is already off) and propose adding conditions to only send commands when the state actually needs to change.

# Output Expectations
- Do NOT modify `automations.yaml` immediately.
- Present a detailed report of optimization opportunities. 
- Show a clear "Before" and "After" YAML snippet for each major proposed change.
- Explain *why* the new version is more robust or efficient.
- Wait for my approval before applying the changes.

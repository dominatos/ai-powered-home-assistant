# Context Initialization (YAML Modernizer & Cleanup)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to clean up and modernize our YAML configuration files without breaking or altering any actual behavior.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `automations.yaml`
2. `scripts.yaml`
3. `configuration.yaml`

# Task Instructions
User:
Please review my YAML files. I want you to perform a syntax and organization cleanup. 

Look for the following:
1. **Deprecated Syntax:** Replace old trigger, condition, or action syntax with modern equivalents (e.g., converting old `state_attr` syntax, replacing legacy `service:` calls with `action:`, though keep in mind the Home Assistant version targeted).
2. **Formatting and Indentation:** Fix any inconsistent indentation, extra blank lines, or messy YAML structures.
3. **Obsolete Fields:** Look for useless `id` fields in scripts (only automations need them) or duplicated keys.
4. **Simplification:** If a complex template can be simplified using a modern built-in condition, propose it.

# Output Expectations
- **CRITICAL:** Do NOT change the functional behavior of any automation or script. This is strictly a syntax and formatting cleanup.
- Present a summary of the syntax issues you found and your proposed fixes.
- Once I approve, apply the formatting changes to the files.

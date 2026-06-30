# Context Initialization (Trace Debugger)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: An automation failed or behaved unexpectedly. I need you to analyze the raw Home Assistant trace or error log and tell me exactly what went wrong and how to fix it.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `automations.yaml`
2. `HOUSE_CONTEXT.md`

# Task Instructions
User:
My automation isn't working right. Here is the automation ID or name, followed by the raw JSON trace (or error log) from Home Assistant:

> [INSERT_AUTOMATION_NAME_OR_ID_HERE]
> 
> ```json
> [PASTE_RAW_TRACE_JSON_OR_LOG_HERE]
> ```

Please perform the following steps:
1. **Locate the Code:** Find the exact automation in `automations.yaml` that this trace belongs to.
2. **Analyze the Trace:** Read the JSON trace step-by-step. Identify exactly which condition failed, which trigger fired unexpectedly, or what variable was missing.
3. **Cross-Reference Reality:** Check `HOUSE_CONTEXT.md` to see if the physical layout of the room explains the failure (e.g., the motion sensor is positioned where it can see the hallway).
4. **Explain in Plain English:** Tell me exactly what happened and why it failed. Don't just give me the fixed code; explain the logic error.

# Output Expectations
- Do NOT modify `automations.yaml` immediately.
- Explain the root cause of the bug clearly.
- Provide the corrected YAML code block for the automation.
- Explain how the new YAML prevents the error from happening again.
- Wait for my approval before applying the fix.

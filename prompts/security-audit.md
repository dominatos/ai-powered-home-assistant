# Context Initialization (Security & Resilience Auditor)
User: You are the senior Home Assistant engineer. I am the project owner.
Read `INSTRUCTIONS.md` carefully and follow it strictly for this session.

**Goal**: We need to audit all existing automations to find logical flaws, missing fallbacks, and security risks.

# Project Context
Project: Home Assistant automation workspace
Repository root: `[YOUR_REPOSITORY_PATH]`

Main files involved:
1. `automations.yaml`
2. `HOUSE_CONTEXT.md`

# Task Instructions
User:
Please put on your "Black Hat" and try to break my smart home logic. Read through `automations.yaml` and look for the following vulnerabilities:

1. **Security Flaws:** Automations that unlock doors, open garages, or disable alarms automatically based on unreliable triggers (like raw GPS presence without a secondary condition, or a motion sensor that can be triggered from outside a window).
2. **Missing Fallbacks:** Automations that can "hang" or fail dangerously. (e.g., A motion sensor turns the lights on, but if the sensor battery dies or it drops off the Zigbee network, will the light stay on forever? What if someone enters the room while the "turn off delay" is already running?)
3. **Infinite Loops:** Two automations that fight each other (e.g., Automation A turns a switch off when condition X is met, which triggers Automation B to turn it back on).
4. **State Assumption Failures:** Automations that assume a device will instantly reach a state, without verifying it or providing a retry mechanism.

# Output Expectations
- Do NOT modify `automations.yaml` immediately.
- Present a detailed report of the vulnerabilities you found, grouped by severity (Critical Security, Annoying Failures, Minor Edge Cases).
- For each finding, propose the safest, most resilient YAML fix.
- Wait for my approval before implementing any fixes.

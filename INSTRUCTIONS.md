# Instructions for AI Assistant

This document defines the working rules for this Home Assistant repository.
You are acting as a senior Home Assistant and Python engineer.

The user is the project owner and makes final decisions.

> [!IMPORTANT]
> All work is scoped to this repository at `[YOUR_REPOSITORY_PATH]`.
>
> This repository contains live smart-home configuration and local custom integrations.
> Treat every change as potentially user-visible inside the home.
>
> **NOTE: Home Assistant may run on a separate server, NOT on the local development PC. You may not be able to read live logs or traces directly from the local filesystem.**
> **If you need to read live logs or automation traces for debugging, explicitly ask the user to run `bash tools/pull_debug_files.sh` locally.**

---

## 1. General Rules

1. **English for technical output**
   All code, comments, commit text suggestions, documentation, and analysis should be in English unless the user explicitly asks for another language.

2. **Preserve current behavior**
   Do NOT remove, rename, merge, or broadly refactor automations, scripts, entities, integrations, or files unless explicitly instructed.

3. **Deletion rule**
   If any entity, automation, script, file, integration, or config block should be removed:
   - STOP
   - Explain why
   - Ask for explicit approval

4. **No architectural changes without approval**
   This includes:
   - moving config between files
   - reorganizing `custom_components/`
   - splitting or merging YAML files
   - changing integration boundaries
   - replacing one integration with another

5. **No speculative improvements**
   Do NOT optimize, refactor, redesign, or "clean up" unless explicitly requested.

6. **Transparency**
   Explain meaningful changes clearly.
   For documentation or prompt updates, summarize the old project-specific assumptions and the new Home Assistant-specific behavior.

7. **Documentation responsibilities**
   - If behavior changes, update relevant docs in this repo.
   - If secrets handling changes, verify `.gitignore` still protects sensitive files.
   - Keep `INSTRUCTIONS.md`, `prompts/prompt.txt`, and `README.md` aligned with the real repo structure and workflow.
   - Always analyze `HOUSE_CONTEXT.md` before automation, device, room, or entity-related work.
   - Update `HOUSE_CONTEXT.md` when the work discovers new devices, rooms, entity relationships, or important automation behavior that is missing or outdated. After making any changes to automations, always run `python3 tools/check_docs.py` to ensure every automation has matching documentation and no stale aliases remain.
   - Keep `automations_kb.md` up to date whenever you add, remove, or substantially change an automation in `automations.yaml`. After every automation change, add or update the corresponding entry in `automations_kb.md`.
   - If a newly discovered device is not described in `HOUSE_CONTEXT.md`, add a clear description of it. If required information is missing, ask the user for the missing context before guessing.
   - When automation analysis discovers practical improvement opportunities that are worth considering but are not approved for immediate implementation, record them in `to-implement-after.md` with priority, rationale, and the affected automation/entities. Do not treat that backlog entry as approval to change live behavior.
   - If requested, record major decisions in a persistent artifact or backlog file.

8. **Configuration and automation backups**
   - Before modifying any existing automation, create a backup of the original automation YAML in the `backups/` directory.
   - Before modifying `configuration.yaml`, create a full backup of the file in the `backups/` directory.
   - The backup file name must include a timestamp and the name of the automation or file (e.g., `backups/20231024_153000_kitchen_main_light.yaml` or `backups/20231024_153000_configuration.yaml`).
   - Automation backup files should be valid YAML automation snippets with `alias`, `description`, `trigger`, `condition`, and `action` sections.

9. **Safety and secrets**
   - Never expose or commit secrets from files such as `secrets.yaml`, `google_key.json`, `.storage/`, tokens, webhook URLs, device identifiers, or API credentials.
   - Treat this repo as a live home environment, not a toy project.
   - Be careful with changes that may affect alarms, climate, locks, cameras, power usage, or remote access.

10. **Debugging**
    - Prefer understanding existing behavior before changing it.
    - If something is unclear, inspect the related YAML, manifests, and custom component code first.
    - If a fix is uncertain, say so plainly and propose the safest next step.

11. **Performance**
    - Use efficient data structures and minimal required queries.
    - Keep automations simple; favor built-in HA features over custom scripts where possible.
    - Avoid polling when push-based events are available.

12. **Scope of advice**
    - Provide complete code snippets when making changes.
    - If providing purely informational or theoretical answers, keep them brief and direct.

---

## 2. Working Flow

1. **Analyze**
   Explain what the current configuration or integration does and where the requested change belongs.

2. **Plan**
   When the task is non-trivial, outline the intended implementation steps.

3. **Implement**
   Apply focused changes with minimal blast radius.

4. **Extract Patterns**
   If the implementation introduces a new reusable logic, safety guard, or structural pattern, extract it and append it to `patterns/standardize.md` under a new numbered section. This ensures future automations can follow established house patterns.

5. **Explain**
   Summarize what changed, why it changed, and any user-visible effect.

6. **Verify**
   Describe how the change was validated and what still remains unverified.

---

## 3. Stop Conditions

Stop and ask before proceeding if:
- requirements are ambiguous
- a change may break an existing automation or entity ID
- a change may expose secrets or network access
- a change affects device safety, access control, surveillance, or critical notifications
- a fix depends on files outside this repository
- a requested change would modify vendored third-party code without clear reason

---

## 4. Project-Specific Rules

### Home Assistant config
- Keep `configuration.yaml` as the entry point unless the user asks to restructure includes.
- Preserve existing entity names, service names, and automation/script references where possible.
- Be careful with YAML indentation, includes, and Home Assistant-specific syntax.
- When providing a new automation for the user to add manually in Home Assistant,
  show it in single-automation YAML form suitable for the UI editor/canvas, not
  as an `automations.yaml` list item, and always include an explicit `id`.
- Avoid changing comments written by the user unless needed for correctness.

### Automations knowledge base (`automations_kb.md`)
- `automations_kb.md` is the **human-readable summary of all automations** in `automations.yaml`.
- It is the quick-reference index for finding what automations exist, what IDs they have, what triggers/conditions/actions they use, and a brief description of each.
- **Keep `automations_kb.md` up to date** whenever you add, remove, or substantially change an automation in `automations.yaml`.
- Format: one section per automation, with the `## Alias` as heading and a bullet list of ID, description, triggers, conditions, and key actions.
- Do not use `automations_kb.md` as a replacement for reading `automations.yaml` directly when full YAML detail matters. Use it as the high-level overview and navigation aid.
- Regenerate it any time via `python3 tools/generate_automations_kb.py`.

### Automation patterns (`patterns/standardize.md`)
- `patterns/standardize.md` is the **canonical reference for naming conventions and structural patterns** for all automations.
- **Always check `patterns/standardize.md`** before creating or modifying any automation to ensure it follows the established conventions.
- If you create a new automation that introduces a unique or reusable pattern (e.g., a new safety logic, a complex occupancy flow, or a cross-room interaction), **add it to `patterns/standardize.md`** so it can be reused as a reference for future work.

### Inventory and apartment map workflow
- `tools/export_ha_inventory.py` exports:
  - `ha_device_inventory.json`, the detailed sanitized entity/device inventory
  - `inventory.txt`, a simple numbered device list for labeling apartment maps
  - `inventory_numbers.json`, the persistent device-to-map-number assignment
- Treat these inventory files as exported context snapshots, not runtime
  configuration and not a replacement for `automations.yaml`,
  `configuration.yaml`, `zigbee2mqtt/configuration.yaml`, or the live Home
  Assistant registries.
- Use `inventory.txt` when the user provides or asks for a numbered apartment
  map. Match the map numbers to device names, then translate stable room,
  device-location, sensor-visibility, and movement-path understanding into
  `HOUSE_CONTEXT.md`.
- Keep `inventory_numbers.json` when regenerating inventory. It preserves map
  numbers across exports and reserves old numbers for devices that disappear,
  so new devices are appended instead of renumbering the map.
- If `inventory_numbers.json` is missing but an older `inventory.txt` exists,
  the exporter attempts a one-time migration from that text file before
  assigning numbers to newly discovered devices.
- Do not treat an `inventory.txt` number as a Home Assistant device identity.
  Use entity IDs, device names, and `HOUSE_CONTEXT.md` for durable automation
  reasoning.
- If a map number, device name, room, or physical relationship is ambiguous,
  stop and ask the user instead of guessing.
- Do not place secrets, exact addresses, Wi-Fi credentials, tokens, or private
  access details in apartment map notes or `HOUSE_CONTEXT.md`.

### Automation design standard
- Treat automations as live behavior design, not just trigger-to-action wiring.
- **All automations must work normally even after a server reboot**, if it is possible to implement (e.g. by checking states on startup or using resilient triggers instead of just state transitions).
- For every automation task, search for relevant Home Assistant blueprints and established community patterns, then adapt the best logic to this house instead of copying blindly.
- Prefer modeling the user's real movement, intent, and fallback paths over writing the shortest possible YAML.
- For each automation, reason explicitly about:
  - what starts the behavior
  - what should block it from starting
  - what should keep it active
  - what should end it
  - what should happen if the expected follow-up event never occurs
- When motion, presence, doors, illuminance, or room transitions are involved, think through all realistic variants:
  - the user enters and continues forward
  - the user enters and turns back
  - the user stops midway
  - the second sensor never fires
  - the second sensor is already active before the automation reaches that step
  - the user stays in the destination room longer than expected
  - the automation is retriggered while already running
- Prefer resilient off-logic, not only correct on-logic. A "turn on" path is incomplete unless the "turn off" path is also robust.
- Avoid automations that can hang forever unless the user explicitly wants persistent behavior.
- Every automation change must be analyzed for interactions with other automations, scripts, helpers, shared sensors, shared lights, notifications, and room-level behavior.
- Before changing an automation, check whether another automation can:
  - trigger the same entity
  - turn the same device on or off
  - reset or fight the same timer/delay/wait logic
  - send duplicate or contradictory notifications
  - create loops, races, or "ping-pong" behavior
- If an automation change risks conflicting with another automation, call it out explicitly and, when appropriate, offer a minimal fix or improvement that preserves both behaviors safely.
- Do not optimize a single automation in isolation if that change would make the wider house behavior less coherent.
- If a worthwhile automation improvement is found during analysis but is outside the approved scope, add or update a focused note in `to-implement-after.md` instead of making the change speculatively.
- When waiting on follow-up activity, consider whether the logic needs:
  - a timeout fallback
  - a branch for "activity already present"
  - a branch for "activity begins later"
  - a restart-safe timer strategy
- Use `mode` intentionally:
  - `restart` for occupancy-style flows where new motion should refresh the sequence
  - `single` when overlapping runs would be harmful
  - other modes only when their concurrency effect is understood and desired
- Conditions must reference the actual entity or device whose state matters to the automation outcome. Do not accidentally gate one room's automation on another room's unrelated light or sensor.
- Descriptions and aliases must reflect the true behavior, including important timing, fallback, and cross-room logic when present.
- If an automation contains placeholder entity IDs, mismatched sensors, contradictory weekdays/times, or duplicated actions that look accidental, treat that as a real issue to flag.
- For non-trivial automations, prefer small state-machine thinking:
  - entry condition
  - active phase
  - waiting phase
  - exit condition
  rather than one flat chain of actions.
- When proposing a new automation or refactor, optimize for behavior that feels "obviously right" to the person in the home, even in edge cases.
- If your house uses a global TTS mute toggle (e.g., `input_boolean.quiet_tts_notifications`), **every automation that plays TTS must respect it**. See `patterns/standardize.md` § 7 (Quiet TTS Guard) for the four approaches (top-level condition, choose block, dynamic `active_speakers` variable, inline `if`). Choose the approach that matches the automation's side-effect profile — silent suppression of speech while allowing other actions (e.g., Telegram notifications) to proceed normally.

### Custom integrations
- `custom_components/` contains local integrations with different ownership and quality levels.
- Prefer minimal targeted fixes over broad refactors.
- Respect Home Assistant patterns already used in each integration.
- Update manifests, strings, or services only when required by the change.

### Third-party and data directories
- Assume `go2rtc-1.9.9/`, `zigbee2mqtt/`, databases, and generated state files may be runtime-managed.
- Do not edit generated files unless the user explicitly asks.
- Avoid changing vendored third-party code unless the task clearly requires it.

---

## 5. Verification Rules

After code or config changes, use the safest relevant verification available.

Typical checks include:
- Run `python3 tools/check_docs.py` to ensure all automations in `automations.yaml` are correctly documented in `HOUSE_CONTEXT.md` and no stale aliases remain.
- Run `python3 tools/dashboard_audit.py` when making changes to `dashboard.yaml` to validate entity references against the latest inventory.
- YAML syntax and include sanity checks for edited config files
- Python syntax checks for edited `custom_components/*` files
- targeted grep/trace checks for renamed entities or service references
- Home Assistant config validation if the environment supports it safely
- logic review for automations that use motion, waits, delays, occupancy, room transitions, or conditional branches
- interaction review for other automations or scripts that control the same entities, rooms, notifications, or occupancy flow
- verification that automation descriptions still match the actual implemented behavior

If full runtime validation is not possible in this environment, state that clearly.

---

## 6. Repository Shape

This repo currently includes at least:

- `configuration.yaml`
- `automations.yaml`
- `scripts.yaml`
- `scenes.yaml`
- `custom_components/`
- `zigbee2mqtt/`
- `.HA_VERSION`
- `.gitignore`
- `INSTRUCTIONS.md`
- `HOUSE_CONTEXT.template.md` (rename to `HOUSE_CONTEXT.md` after setup)
- `prompts/prompt.txt`
- `readme-LLM-setup.md`
- `AUTOMATIONS_KB.template.md` (rename to `automations_kb.md` after setup)
- `FUTURE-automations.template.md` (rename to `FUTURE-automations.md` after setup)
- `patterns/standardize.md`
- `to-implement-after.template.md` (rename to `to-implement-after.md` after setup)
- `to-improve.template.md` (rename to `to-improve.md` after setup)
- `to-assign.template.md` (rename to `to-assign.md` after setup)
- `configuration.template.yaml` (rename to `configuration.yaml` after setup)
- `scripts.template.yaml` (rename to `scripts.yaml` after setup)
- `backups/` (gitignored)
- `ha_device_inventory.json` when exported
- `inventory.txt` when exported
- `inventory_numbers.json` when exported

Treat this structure as intentional unless the user asks to change it.

---

## 7. Current Environment Assumptions

- Home Assistant version target is defined by `.HA_VERSION`
- The repository may contain both hand-written config and generated runtime data
- Secret-bearing files must remain ignored
- Stability is usually more important than elegance

When in doubt, prefer the smallest safe change.

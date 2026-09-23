# Automation Standardization Guide

This document defines reusable patterns for Home Assistant automations.
Use these patterns as templates when creating new automations. Every new automation
should follow the closest matching pattern and adopt its structure, naming conventions,
and guard logic.

> [!IMPORTANT]
> **Always check this file before writing any new automation.**
> If your new automation introduces a unique reusable pattern, add it as a new numbered
> section here so future work can reference it.

---

## 1. Simple Toggle

Button press toggles a single device. No conditions, no delays.

**When to use:** Physical button or NFC tag directly controls a light, switch, or boolean.

**Template:**
```yaml
- id: unique_id
  alias: 'Room: Device Toggle'
  description: Triggered by [button source]; toggles [device].
  triggers:
    - domain: mqtt
      device_id: <button_device_id>
      type: action
      subtype: <button_action>
      trigger: device
  conditions: []
  actions:
    - type: toggle
      device_id: <target_device_id>
      entity_id: <target_entity_id>
      domain: <light|switch>
  mode: single
```

**Generic examples:**
- `Living Room: Main Light Toggle` — single press on wall switch toggles ceiling light
- `Hallway: NFC Tag Toggle` — NFC tag tap toggles hallway light

---

## 2. Time-Window Toggle

Button press toggles a device, but the target or behavior changes based on time of day.

**When to use:** Same button controls different devices depending on time (e.g., night vs day).

**Template:**
```yaml
- id: unique_id
  alias: 'Room: Device Toggle (Time-Aware)'
  description: Triggered by [button]; behavior changes at [time boundary].
  triggers:
    - domain: mqtt
      device_id: <button_device_id>
      type: action
      subtype: <button_action>
      trigger: device
      id: <trigger_id>
  conditions: []
  actions:
    - choose:
        - conditions:
            - condition: trigger
              id: <trigger_id>
            - condition: time
              after: '<start_time>'
              before: '<end_time>'
          sequence:
            - type: toggle
              device_id: <device_a_id>
              entity_id: <entity_a_id>
              domain: <domain>
        default:
          - type: toggle
            device_id: <device_b_id>
            entity_id: <entity_b_id>
            domain: <domain>
  mode: single
```

**Generic examples:**
- `Bedroom: Bedside Light Toggle` — same button toggles reading light by day, dim night light after 22:00
- `Hallway: Ceiling Toggle (Time-Aware)` — full bright before 21:00, 20% after 21:00

---

## 3. Motion-Activated Light

Motion turns a light on; no motion for a timeout turns it off.

**When to use:** Automatic room lighting based on occupancy.

**Template:**
```yaml
- id: unique_id
  alias: 'Room: Light on Motion'
  description: Turns on [light] on motion, off after [timeout] of no motion.
  triggers:
    - trigger: state
      entity_id: <motion_sensor>
      from: 'off'
      to: 'on'
      id: motion_on
    - trigger: state
      entity_id: <motion_sensor>
      to: 'off'
      for:
        minutes: <timeout_minutes>
      id: no_motion
  conditions: []
  actions:
    - choose:
        - conditions:
            - condition: trigger
              id: motion_on
            - condition: time
              after: '<start_time>'
              before: '<end_time>'
            - condition: state
              entity_id: <light_entity>
              state: 'off'
          sequence:
            - type: turn_on
              device_id: <device_id>
              entity_id: <entity_id>
              domain: light
        - conditions:
            - condition: trigger
              id: no_motion
            - condition: time
              after: '<start_time>'
              before: '<end_time>'
            - condition: state
              entity_id: <light_entity>
              state: 'on'
          sequence:
            - type: turn_off
              device_id: <device_id>
              entity_id: <entity_id>
              domain: light
  mode: restart
```

**Key decisions:**
- Use `mode: restart` so new motion resets the off-timer
- Guard turn-on with light-off check to avoid redundant commands
- Guard turn-off with light-on check to avoid redundant commands
- Add time window if motion lighting should only work during certain hours

**Generic examples:**
- `Bathroom: Light on Motion` — turns on bathroom light on motion, off after 5 min no motion
- `Hallway: Light on Motion (Evening)` — active 17:00–23:00 only, 3 min timeout

---

## 4. Night Path Light

Cross-room motion-based lighting for nighttime navigation between rooms.

**When to use:** When someone moves between rooms at night and needs subtle path lighting.

**Structure:** Two automations work together:
1. Source room motion → wait for destination confirmation → turn on path light
2. Path light ownership tracked via `input_boolean` to prevent conflicts with other automations

**Key rules:**
- Restrict to a nighttime window (e.g., 23:00–07:00)
- Track automation ownership via `input_boolean`
- Final off-check must verify ALL shared sensors are clear
- Clear ownership marker even when leaving light on for another reason
- Use `mode: restart` with `max_exceeded: silent`

**Generic examples:**
- `Hallway: Path Light on Night Motion` — hallway motion → corridor strip light on, off when motion clears
- `Bedroom: Corridor Light on Night Exit` — bedroom motion → hallway light on, confirmed off when bedroom + hallway motion both clear

---

## 5. Sensor-Driven Light

Environmental sensor (luminance, contact, humidity) controls a light.

**When to use:** Light should respond to ambient conditions, not just motion.

**Template:**
```yaml
- id: unique_id
  alias: 'Room: Light on Sensor Condition'
  description: Turns [light] on/off based on [sensor] threshold.
  triggers:
    - trigger: numeric_state
      entity_id: <sensor_entity>
      below: <on_threshold>
      id: turn_on
    - trigger: numeric_state
      entity_id: <sensor_entity>
      above: <off_threshold>
      id: turn_off
  conditions:
    - condition: time
      after: '<start_time>'
      before: '<end_time>'
  actions:
    - if:
        - condition: trigger
          id: turn_on
      then:
        - action: light.turn_on
          target:
            entity_id: <light_entity>
          data: {}
    - if:
        - condition: trigger
          id: turn_off
        - condition: state
          entity_id: <guard_entity>
          state: 'off'
      then:
        - action: light.turn_off
          target:
            entity_id: <light_entity>
          data: {}
  mode: restart
```

**Key decisions:**
- Use hysteresis (different on/off thresholds) to prevent rapid cycling
- Add guard conditions for shared devices (e.g., hood open = don't turn off)
- `mode: restart` so new sensor readings reset the sequence

**Generic examples:**
- `Kitchen: Under-Cabinet Light on Low Luminance` — luminance < 50 lux → on, > 200 lux → off with hood-open guard
- `Bathroom: Mirror Light on Humidity` — humidity > 70% → full brightness (shower detection)

---

## 5a. Motion-Gated Sensor-Driven Light with Auto-Off Timer

Light turns on when motion is detected AND a sensor condition is true. Turns off automatically after a no-motion timeout. Sensor threshold also provides a direct off path.

**When to use:** Sensor condition (e.g., low luminance) sets the *prerequisite*, motion provides the *activation*. Prevents the light from being on all day in an empty room.

**Template:**
```yaml
- id: unique_id
  alias: 'Room: Light on Motion + Sensor Condition'
  description: >-
    Turns on [light] when motion detected and [sensor] < threshold.
    Turns off after [N] min of no motion, or when [sensor] rises above off-threshold.
    [Guard] prevents turn-off while [condition].
  triggers:
  - trigger: state
    entity_id: <motion_sensor>
    from: 'off'
    to: 'on'
    id: motion_on
  - trigger: state
    entity_id: <motion_sensor>
    to: 'off'
    for:
      minutes: <timeout>
    id: no_motion
  - trigger: numeric_state
    entity_id: <sensor_entity>
    above: <off_threshold>
    id: high_sensor
  - trigger: homeassistant
    event: start
    id: ha_start
  conditions:
  - condition: time
    after: '<start_time>'
    before: '<end_time>'
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: motion_on
      - condition: numeric_state
        entity_id: <sensor_entity>
        below: <on_threshold>
      sequence:
      - action: light.turn_on
        target:
          entity_id: <light_entity>
        data: {}
    - conditions:
      - condition: trigger
        id: no_motion
      - condition: state
        entity_id: <guard_entity>
        state: 'off'
      sequence:
      - action: light.turn_off
        target:
          entity_id: <light_entity>
        data: {}
    - conditions:
      - condition: trigger
        id: high_sensor
      - condition: state
        entity_id: <guard_entity>
        state: 'off'
      sequence:
      - action: light.turn_off
        target:
          entity_id: <light_entity>
        data: {}
    - conditions:
      - condition: trigger
        id: ha_start
      - condition: state
        entity_id: <motion_sensor>
        state: 'on'
      - condition: numeric_state
        entity_id: <sensor_entity>
        below: <on_threshold>
      sequence:
      - action: light.turn_on
        target:
          entity_id: <light_entity>
        data: {}
  mode: restart
```

**Key decisions:**
- `mode: restart` — new motion resets the no-motion off-timer; automation never hangs
- Sensor threshold checked inline at motion time (condition), not as a trigger
- Guard (e.g., hood open) blocks all automatic turn-off paths
- HA startup recovery: turns on if motion + low sensor already active at boot
- Sensor rise (high_sensor) provides a direct off path if light is no longer needed

**Generic examples:**
- `Kitchen: Work Light on Motion + Low Lux` — motion + luminance < 100 → on, 5-min no-motion or luminance > 200 → off, extraction fan guard

---

## 6. AI TTS Announcement

An LLM generates a natural-language voice announcement, played on a speaker.

**When to use:** Dynamic announcements that should sound natural (weather, calendar, reminders).

**Template:**
```yaml
- id: unique_id
  alias: 'Room: AI Announcement'
  description: Announces [topic] using [LLM service] on [speaker].
  triggers:
    - trigger: time
      at: '<time>'
  conditions:
    - condition: state
      entity_id: input_boolean.quiet_tts_notifications
      state: 'off'
  actions:
    - variables:
        ai_prompt: >
          [Your LLM prompt here]
    - action: rest_command.<your_llm_command>
      data:
        prompt: '{{ ai_prompt }}'
      response_variable: llm_response
    - action: media_player.volume_set
      target:
        entity_id: <speaker_entity>
      data:
        volume_level: 0.4
    - action: tts.speak
      target:
        entity_id: tts.<your_tts_engine>
      data:
        cache: false
        media_player_entity_id: <speaker_entity>
        message: >
          {% if llm_response is defined and llm_response.status == 200 %}
            {% set content = llm_response.content %}
            {% if content is mapping and 'response' in content and content.response | trim | length > 0 %}
              {{ content.response | replace('*', '') | replace('"', '') }}
            {% else %}
              [Your fallback message]
            {% endif %}
          {% else %}
            [Your fallback message]
          {% endif %}
    - wait_template: "{{ is_state('<speaker_entity>', 'playing') }}"
      timeout: "00:00:10"
    - wait_template: "{{ is_state('<speaker_entity>', 'idle') or is_state('<speaker_entity>', 'off') }}"
      timeout: "00:01:30"
    - action: media_player.volume_set
      target:
        entity_id: <speaker_entity>
      data:
        volume_level: 0.2
  mode: single
```

**Generic examples:**
- `Weather: Morning Briefing` — at 07:30 Mon–Fri, generates a weather summary and plays it on kitchen speaker
- `Calendar: Evening Events Announcement` — at 18:00, reads today's remaining calendar events aloud

---

## 7. Quiet TTS Guard

Approaches to respect a global `input_boolean.quiet_tts_notifications` (or equivalent). Use the approach that matches the automation's needs.

> [!TIP]
> Create an `input_boolean.quiet_tts_notifications` helper in Home Assistant and use it as a house-wide TTS mute switch. All TTS automations must respect it. Dashboard-togglable for easy use at night or during meetings.

### 7a. Top-Level Condition (simplest)

Blocks the entire automation when quiet TTS is on. Use when the automation has **no other side effects** (no notifications, no device control).

```yaml
conditions:
  - condition: state
    entity_id: input_boolean.quiet_tts_notifications
    state: 'off'
```

> [!WARNING]
> `automation.trigger` called from a dashboard button **bypasses top-level conditions**. Use approach 7d instead if the automation has a dashboard trigger button.

### 7b. Choose Block (TTS only, other actions still run)

TTS is inside a `choose`, other actions (e.g., mobile notification) run unconditionally. Use when quiet mode should suppress speech but NOT push notifications.

```yaml
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: input_boolean.quiet_tts_notifications
            state: 'off'
        sequence:
          - action: tts.speak
            ...
  - action: notify.mobile_app_<device>
    ...
```

### 7c. Dynamic `active_speakers` Variable (multi-room TTS)

Build a list of active speakers at runtime. When quiet mode is on, the list is empty and TTS is skipped entirely. Add speakers conditionally based on room occupancy or other state.

```yaml
actions:
  - variables:
      active_speakers: >
        {% set ns = namespace(speakers=[]) %}
        {% if is_state('input_boolean.quiet_tts_notifications', 'off') %}
          {% set ns.speakers = ns.speakers + ['media_player.<kitchen_speaker>'] %}
          {% if is_state('<bedroom_occupied_indicator>', 'on') %}
            {% set ns.speakers = ns.speakers + ['media_player.<bedroom_speaker>'] %}
          {% endif %}
        {% endif %}
        {{ ns.speakers | join(', ') }}
  - if:
      - condition: template
        value_template: "{{ active_speakers | length > 0 }}"
    then:
      - action: media_player.volume_set
        target:
          entity_id: "{{ active_speakers }}"
        data:
          volume_level: 0.4
      - action: tts.speak
        ...
```

### 7d. Inline `if` (dashboard-trigger safe)

Quiet check as an `if` inside actions. Safe for dashboard-triggered automations because it evaluates at action time, not trigger time.

```yaml
actions:
  - if:
      - condition: state
        entity_id: input_boolean.quiet_tts_notifications
        state: 'off'
    then:
      - action: tts.speak
        ...
```

---

## 8. Occupancy-Based Auto-Off

Device turns off after prolonged inactivity (no motion, low power, etc.).

**When to use:** Safety net for devices that should not run indefinitely.

**Template:**
```yaml
- id: unique_id
  alias: 'Room: Turn Off [Device] After [Timeout]'
  description: Turns off [device] after [timeout] of no [activity].
  triggers:
    - trigger: state
      entity_id: <motion_or_power_sensor>
      to: '<inactive_state>'
      for:
        minutes: <timeout_minutes>
  conditions:
    - condition: state
      entity_id: <device_boolean_or_switch>
      state: 'on'
  actions:
    - action: switch.turn_off  # or light.turn_off / input_boolean.turn_off
      target:
        entity_id: <device_entity>
      data: {}
  mode: single
```

**Generic examples:**
- `Living Room: Turn Off A/C After 30 Min No Motion` — shuts down A/C if no motion for 30 min
- `Kitchen: Turn Off Oven After 2 Hours Idle` — kills oven smart plug if power drops below 10W for 2 hours

---

## 9. Boolean Sync

Keeps an `input_boolean` in sync with the real device state, covering all write paths.

**When to use:** When a virtual toggle must reflect the actual device state regardless of how it was changed (button, IR remote, HA UI, another automation).

**Template:**
```yaml
- id: unique_id
  alias: 'Room: Sync [Device] State to Boolean'
  description: Watches [device] and keeps [boolean] in sync.
  triggers:
    - trigger: state
      entity_id: <device_entity>
      id: device_on
      to: '<on_state>'
    - trigger: state
      entity_id: <device_entity>
      id: device_off
      to: 'off'
  conditions: []
  actions:
    - choose:
        - conditions:
            - condition: trigger
              id: device_on
          sequence:
            - action: input_boolean.turn_on
              target:
                entity_id: <boolean_entity>
              data: {}
        - conditions:
            - condition: trigger
              id: device_off
          sequence:
            - action: input_boolean.turn_off
              target:
                entity_id: <boolean_entity>
              data: {}
  mode: restart
```

**Key rules:**
- Use `mode: restart` so rapid state changes don't stack
- This automation must NOT be the one that changes the device (avoid feedback loops)
- Pair with the toggle automation that writes to the boolean

**Generic examples:**
- `Living Room: Sync TV State to Boolean` — keeps `input_boolean.living_room_tv_on` aligned with `media_player.living_room_tv`

---

## 10. Kill Switch / Delayed Re-Enable

Temporarily disables another automation, then re-enables it after a delay.

**When to use:** Manual override that expires automatically.

**Structure:** Three automations work together:
1. **Kill switch** — disables target automation + optional confirmation (TTS or notification)
2. **Delayed re-enable** — watches target automation state, waits, re-enables it
3. **Daily reset** — safety net that re-enables at a fixed time (survives HA restarts)

**Key rules:**
- Kill switch uses `automation.turn_off` with `stop_actions: true`
- Re-enable uses `automation.turn_on`
- Daily reset at a fixed time acts as fail-safe in case of HA restart
- Use `mode: restart` on the kill switch so double-press resets the timer

**Generic examples:**
- `Bedroom: Disable Motion Lighting for 2 Hours` — button press disables bedroom motion automation until re-enabled or until 07:00 reset
- `Living Room: Pause Presence Automation` — kills occupancy auto-off during movie mode, re-enables after 3 hours

---

## 11. Actionable Notification

Sends an interactive notification with response buttons, waits for user action.

**When to use:** When the user must choose an action from their phone.

**Template (single phone, no presence check):**
```yaml
- id: unique_id
  alias: 'Room: Actionable Notification'
  description: Sends actionable notification about [topic].
  triggers:
    - trigger: <trigger_type>
      entity_id: <entity>
  conditions: []
  actions:
    - action: notify.mobile_app_<device>
      data:
        title: "<title>"
        message: "<message>"
        data:
          tag: <unique_tag>
          actions:
            - action: ACTION_YES
              title: "Yes"
            - action: ACTION_NO
              title: "No"
    - wait_for_trigger:
        - platform: event
          event_type: mobile_app_notification_action
          event_data:
            action: ACTION_YES
        - platform: event
          event_type: mobile_app_notification_action
          event_data:
            action: ACTION_NO
      timeout: <timeout>
      continue_on_timeout: true
    - if:
        - condition: template
          value_template: "{{ wait.trigger is not none and wait.trigger.event.data.action == 'ACTION_YES' }}"
      then:
        - [action for YES]
    - action: notify.mobile_app_<device>
      data:
        message: clear_notification
        data:
          tag: <unique_tag>
  mode: single
```

**Template (multi-phone with presence check):**
```yaml
- id: unique_id
  alias: 'Room: Actionable Notification'
  triggers:
    - trigger: state
      entity_id: <entity>
      to: '<state>'
  conditions:
    - condition: or
      conditions:
        - condition: zone
          entity_id: person.<person_1>
          zone: zone.home
        - condition: zone
          entity_id: person.<person_2>
          zone: zone.home
  actions:
    - action: notify.mobile_app_<phone_1>
      data:
        title: "<title>"
        message: "<message>"
        data:
          tag: <unique_tag>
          actions:
            - action: ACTION_YES
              title: "Yes"
            - action: ACTION_NO
              title: "No"
    - action: notify.mobile_app_<phone_2>
      data:
        title: "<title>"
        message: "<message>"
        data:
          tag: <unique_tag>
          actions:
            - action: ACTION_YES
              title: "Yes"
            - action: ACTION_NO
              title: "No"
    - wait_for_trigger:
        - platform: event
          event_type: mobile_app_notification_action
          event_data:
            action: ACTION_YES
        - platform: event
          event_type: mobile_app_notification_action
          event_data:
            action: ACTION_NO
      timeout: '00:05:00'
      continue_on_timeout: true
    - action: notify.mobile_app_<phone_1>
      data:
        message: clear_notification
        data:
          tag: <unique_tag>
    - action: notify.mobile_app_<phone_2>
      data:
        message: clear_notification
        data:
          tag: <unique_tag>
    - if:
        - condition: template
          value_template: "{{ wait.trigger is not none and wait.trigger.event.data.action == 'ACTION_YES' }}"
      then:
        - [action for YES]
  mode: single
```

**Generic examples:**
- `Security: Actionable Door Open Alert` — alerts all home occupants when front door opens unexpectedly; Yes = dismiss, No = sound alarm
- `Appliances: Washing Machine Finished` — notifies when cycle completes; Yes = I'll handle it, dismisses after 5 min

---

## 12. Volume Boost & Restore

Temporarily raises speaker volume for an announcement, then restores it.

**When to use:** Any TTS announcement that needs to be heard over background noise.

**Template:**
```yaml
- action: media_player.volume_set
  target:
    entity_id: <speaker>
  data:
    volume_level: 0.4
- action: tts.speak
  ...
- wait_template: "{{ is_state('<speaker>', 'playing') }}"
  timeout: "00:00:10"
- wait_template: "{{ is_state('<speaker>', 'idle') or is_state('<speaker>', 'off') }}"
  timeout: "00:01:30"
- action: media_player.volume_set
  target:
    entity_id: <speaker>
  data:
    volume_level: 0.2
```

**Generic examples:**
- Used in `Weather: Morning Briefing` and `Calendar: Events Announcement`

---

## 13. Multi-Device Off

Turns off multiple devices across rooms in a single automation.

**When to use:** "All off" buttons, bedtime routines, leaving-home actions.

**Key rules:**
- Use `area_id` for room-wide light-off when possible
- Check each device state before turning off to avoid redundant commands
- Sync all related booleans (A/C, appliances, helpers)
- Include relevant side effects (thermostat mode change, tablet sleep, etc.)

**Generic examples:**
- `House: Goodnight Routine` — triggered by button 4 on bedroom remote; turns off all lights, sets thermostat to night temperature, locks front door
- `House: Away Mode` — presence trigger; all lights off, A/C off, appliances off

---

## 14. Startup Recovery

Reconnects or reloads integrations after Home Assistant restarts.

**When to use:** Devices that go offline after HA reboot and need manual reconnection or state restoration.

**Template:**
```yaml
- id: unique_id
  alias: 'System: Recovery on Startup'
  description: [What it recovers and why].
  triggers:
    - trigger: homeassistant
      event: start
  conditions: []
  actions:
    - delay: <stabilization_time>
    - action: <recovery_action>
  mode: single
```

**Key rules:**
- Always add a stabilization delay (30s–5min) for network/device availability
- Use `mode: single` to prevent stacking on rapid restarts
- Combine with state checks so you don't act if recovery is not needed

**Generic examples:**
- `System: Reload Local Integrations After Boot` — 5 min delay, then reloads Tuya Local or other LAN integrations
- `System: Restore Presence State After Restart` — checks WiFi sensors on startup and updates person states

---

## 15. Periodic Polling

Runs a check or update on a fixed interval.

**When to use:** Entities that don't push updates, or where faster reaction time is needed than the default polling.

**Template:**
```yaml
- id: unique_id
  alias: 'System: Periodic [Action]'
  description: [What it does and why polling is needed].
  triggers:
    - trigger: time_pattern
      minutes: /5
  conditions: []
  actions:
    - action: homeassistant.update_entity
      target:
        entity_id: <entity>
  mode: single
```

**Key rules:**
- Use `mode: single` to prevent stacking
- Keep interval as long as practical to reduce load
- Prefer push-based triggers if the integration supports them

**Generic examples:**
- `System: Sync Calendar Hourly` — calls `homeassistant.update_entity` on calendar sensor every hour
- `System: Fast Location Poll While Away` — polls GPS tracker every 30s when residents are not home

---

## 16. Naming Convention (Alias Standard)

Every automation `alias` must follow the format: **`[Room/Area]: [Action or Trigger]`**

### Formatting Rules
- **Room/Area Name**: Use the official room name from `HOUSE_CONTEXT.md`. Use Title Case (e.g., `Kitchen`, `Child Room`, `System`).
- **Action or Trigger**: Use Title Case. Be descriptive but concise. Use `on` for events (e.g., `on Door Open`, `on Motion`) and verbs for actions (e.g., `Toggle`, `Turn Off`, `Follows`).
- **Separator**: Use a colon and a space (`: `).
- **System-Wide**: For automations not tied to a specific room, use `System:`, `Weather:`, `Climate:`, or `Water Safety:`.

### Valid Examples
- `Kitchen: Main Light on Door Open`
- `Bedroom: Bedside Light on Motion`
- `System: Reload Integration After Boot`
- `Water Safety: Close Valve on Leak`
- `Climate: Sync Thermostat with Boiler Relay`

### Invalid Patterns
- `kitchen motion light` — missing room prefix, wrong case
- `auto off` — vague, missing room
- `Bathroom light off` — missing colon separator

---

## 17. Description Convention

Every automation must have a `description` that explains exactly what it does. If the logic is complex, include timing, conditions, and fallback behaviors.

### Structure
1. **Trigger**: What starts the behavior?
2. **Conditions**: What must be true for it to run?
3. **Actions**: What does it actually do?
4. **Timeouts/Fallbacks**: What happens if the expected event never occurs?

### Examples
- **Simple**: `Toggles the hallway light when the wall button is pressed.`
- **Complex**: `Triggered by hallway motion between 23:00 and 07:00; turns on the staircase strip light, tracks ownership via input_boolean, waits for hallway motion to clear with a 10-min timeout fallback, then turns off only if hallway and bedroom motion are both clear.`

---

## 18. Cross-Room Logic

When an automation in one room controls devices in another room, the **Room/Area** prefix in the alias should reflect where the **trigger** originates. The description must explicitly state the cross-room action.

### Example
- **Alias**: `Living Room: Toggle Hallway Light on Double Press`
- **Description**: `Triggered by double press on living room wall switch; toggles the hallway ceiling light.`

---

## 19. New Pattern Creation

If you create a new automation that introduces a unique or reusable pattern (e.g., a new way of handling motion, a new type of safety logic, a new integration pattern), **add it to this file** under a new numbered section so it can be reused as a reference for future automations.

### How to Add
1. Name the pattern and describe its use case.
2. Provide a YAML template or logic flow description.
3. Explain the key design decisions (e.g., "Prevents light loops," "Ensures boot recovery").
4. Add 1–2 generic example aliases showing typical usage.

---

## 20. Virtual Boolean → IR Reactor

A virtual boolean (`input_boolean`) acts as the single source of truth for an IR-controlled device's on/off state. A dedicated reactor automation watches the boolean and sends the actual IR commands via an IR blaster. All other automations (buttons, NFC, timers, scenes) only write to the boolean and never send IR commands directly.

**When to use:** When an IR-controlled device (A/C, TV, fan) must be controlled from multiple sources and the state must be tracked separately from the physical device (which has no state feedback to HA).

**Key design decisions:**
- **One reactor, many writers** — all write paths use `input_boolean.toggle/turn_on/turn_off`. IR logic lives in one place.
- **`mode: restart`** — ensures rapid on→off→on sequences resolve to the final intent.
- **Power-on first** — for A/C units: send Turn On before mode/temperature commands, with 1-second delays between each IR command to prevent missed signals.
- **No conditions on the reactor** — conditions for *when* to act belong in the upstream automations. The reactor is stateless and always responds.

**Template:**
```yaml
- id: room_sync_device_boolean_to_ir
  alias: 'Room: Sync Device Boolean to IR'
  description: >-
    Watches input_boolean.device_name and sends IR commands to the IR blaster.
    Turn on: sends power-on first, then mode and temperature. Turn off: sends power-off.
  triggers:
  - trigger: state
    entity_id: input_boolean.device_name
    to: 'on'
    id: turn_on
  - trigger: state
    entity_id: input_boolean.device_name
    to: 'off'
    id: turn_off
  conditions: []
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id: turn_on
      sequence:
      - action: button.press
        target:
          entity_id: button.<ir_device>_turn_on
      - delay:
          seconds: 1
      # Add further IR commands (mode, temperature) as needed with 1s delays
    - conditions:
      - condition: trigger
        id: turn_off
      sequence:
      - action: button.press
        target:
          entity_id: button.<ir_device>_turn_off
  mode: restart
```

**Generic examples:**
- `Living Room: Sync A/C Boolean to IR` — `input_boolean.living_room_ac_on` drives IR blaster to control split A/C unit

---

## 22. Dynamic Helper-Driven Timer Control (Start, Pause, Resume, Extend, Cancel)

A timer helper (`timer.<name>`) is managed with interactive dashboard controls (Start, Pause, Resume, Extend, Cancel), an `input_number` helper for runtime configuration, and an `input_boolean` state tracker.

**When to use:** Countdown features (e.g., TV timer, appliance timers) where users need to set countdown duration, start/pause/resume execution, extend remaining time dynamically, and receive notifications or auto-off actions on finish or cancel.

**Key design decisions:**
- **State Tracker (`input_boolean`):** Turned `on` when started, kept `on` while active or paused, turned `off` when finished or cancelled (`timer.cancelled` event trigger).
- **Dynamic Extend Script:** Checks `timer.<name>` state: if `idle`, starts the timer; if `active` or `paused`, calls `timer.change` with duration derived from `input_number.<name>`.
- **Paused Remaining Display:** Template sensor checks `is_state('timer.<name>', 'paused')` and formats `state_attr('timer.<name>', 'remaining')` into `HH:MM (Paused)` format so remaining time is preserved visually when paused.

**Template:**
```yaml
# Script for dynamic extend
extend_timer_script:
  alias: "Extend Timer"
  description: "Extends active/paused timer by configured input_number or starts if idle."
  sequence:
    - if:
        - condition: state
          entity_id: timer.my_timer
          state: "idle"
      then:
        - action: input_button.press
          target:
            entity_id: input_button.start_timer
      else:
        - action: timer.change
          target:
            entity_id: timer.my_timer
          data:
            duration: >
              {% set m = states('input_number.timer_minutes') | int(15) %}
              {{ '{:02d}:{:02d}:00'.format(m // 60, m % 60) }}

# Automation for cancel event handling
- id: timer_cancelled_reset
  alias: 'System: Reset Timer Active on Cancel'
  triggers:
    - trigger: event
      event_type: timer.cancelled
      event_data:
        entity_id: timer.my_timer
  actions:
    - action: input_boolean.turn_off
      target:
        entity_id: input_boolean.timer_active
```

**Generic examples:**
- `Living Room: TV Off After Timer` — user sets countdown; TV turns off when timer finishes; Extend button adds time

---

## 23. 24/7 API Health Probing & Auto-Recovery

An external API health check runs periodically (e.g., hourly) to validate remote service availability, automatically switching Home Assistant to a local fallback when the remote API fails, and restoring the primary provider when health is recovered.

**When to use:** Cloud vs. local provider selection (e.g., Cloud AI vs. local Ollama, Cloud TTS vs. local Piper) where Home Assistant should gracefully degrade on cloud outage and self-heal when the cloud recovers.

**Key design decisions:**
- **No blocking condition** — runs on schedule 24/7 regardless of current provider, ensuring recovery is detected.
- **Bi-directional transition check (`choose`):**
  1. *Primary selected + API fails* → switch to local fallback + alert.
  2. *Fallback selected + API succeeds* → restore primary + send recovery alert.
- **Alert deduplication** — notifications fire only on state changes, avoiding repeated false alarms when stable.

**Template:**
```yaml
- id: api_hourly_health_check
  alias: 'System: Service API Health Check'
  description: Probes remote API health on a schedule. Auto-switches to local fallback on failure and auto-recovers to cloud provider when healthy.
  mode: single
  triggers:
    - trigger: time_pattern
      minutes: '30'
  actions:
    - action: rest_command.check_cloud_api
      continue_on_error: true
      response_variable: health_response
    - variables:
        is_healthy: "{{ health_response is defined and health_response.status == 200 }}"
        current_provider: "{{ states('input_select.service_provider_selector') }}"
    - choose:
        - conditions:
            - condition: template
              value_template: "{{ not is_healthy and current_provider == 'Cloud' }}"
          sequence:
            - action: input_select.select_option
              target:
                entity_id: input_select.service_provider_selector
              data:
                option: Local
            - action: notify.mobile_app_<device>
              data:
                message: "⚠️ Cloud API health check failed! Switched to Local fallback."
        - conditions:
            - condition: template
              value_template: "{{ is_healthy and current_provider == 'Local' }}"
          sequence:
            - action: input_select.select_option
              target:
                entity_id: input_select.service_provider_selector
              data:
                option: Cloud
            - action: notify.mobile_app_<device>
              data:
                message: "✅ Cloud API restored! Automatically switched back to Cloud."
```

**Generic examples:**
- `System: AI Provider Hourly Health Check` — switches between cloud LLM and local Ollama based on API availability

---

## 24. Guarded Native Thermostat Schedule Synchronization

When dashboard helpers control device-resident schedules, separate schedule
storage from schedule activation:

1. Validate all transition times are strictly ascending before writing; invalid
   dashboard values must preserve the existing device schedule.
2. Use a readiness boolean for newly introduced schedule groups whose helper
   values have not yet been reviewed. Do not infer safe defaults from a device.
3. It is safe to write a future schedule during a temporary override, but do
   not re-activate `schedule` mode until Boost, Away/Night, and presence guards
   permit it.
4. Route all override-restoration paths through the one guarded schedule
   automation rather than publishing `schedule` mode independently. This avoids
   races with an override that has not finished setting its state.

**Generic examples:**
- `Thermostat: Write Native Schedule` — writes weekday/Saturday/Sunday schedules to Zigbee2MQTT with ascending-time validation and weekend readiness guard

---

## 25. Stable Presence Tracking & Master Occupancy

GPS tracking (`person` entities) can occasionally drift, causing false "not_home" states that trigger Away automations while someone is still in the house.

**When to use:** Whenever an automation needs to know if someone is home (e.g., thermostat away mode, alarm systems, "nobody was home" arrival announcements). Never use raw `person` state for away logic if the automation has high impact.

**Key design decisions:**
- **Debounced Departures:** Use `input_boolean.<person>_home_stable` helpers. On arrival, turn on immediately. On departure, wait 5 minutes before turning off. If the person returns to `home` within the 5 minutes, the timer cancels and the helper stays on uninterrupted.
- **Unified Master Sensor:** `binary_sensor.house_occupied` combines all stable helpers, `input_boolean.guest_mode`, and internal motion trackers (like Magic Areas) into a single unified `on`/`off` state.
- **Guest Mode:** Always include an `input_boolean.guest_mode` in the master occupancy logic to prevent the house from shutting down when owners leave guests behind.

**Template (Stable Sync Automation):**
```yaml
- id: presence_stable_sync
  alias: 'Presence: Stable Presence Sync'
  description: Updates stable input_booleans with a 5-minute debounce on departure.
  triggers:
    - trigger: state
      entity_id:
        - person.<owner_1>
        - person.<owner_2>
  actions:
    - variables:
        person_id: "{{ trigger.entity_id }}"
        is_home: "{{ trigger.to_state.state == 'home' }}"
        helper: "input_boolean.{{ person_id.split('.')[1] }}_home_stable"
    - if:
        - condition: template
          value_template: "{{ is_home }}"
      then:
        - action: input_boolean.turn_on
          target:
            entity_id: "{{ helper }}"
      else:
        - delay:
            minutes: 5
        - condition: template
          value_template: "{{ states(person_id) != 'home' }}"
        - action: input_boolean.turn_off
          target:
            entity_id: "{{ helper }}"
  mode: parallel
  max: 10
```

**Template (Master Occupancy Template Sensor):**
```yaml
template:
  - binary_sensor:
      - name: House Occupied
        unique_id: house_occupied_master
        state: >
          {{ 
             is_state('input_boolean.<owner_1>_home_stable', 'on') or 
             is_state('input_boolean.<owner_2>_home_stable', 'on') or 
             is_state('input_boolean.guest_mode', 'on') or
             is_state('binary_sensor.magic_areas_presence_tracking_interior_area_state', 'on')
          }}
```

**Generic examples:**
- `Presence: Stable Presence Sync` — debounces departure by 5 minutes per person
- `binary_sensor.house_occupied` — unified occupancy from stable helpers + guest mode + motion

---

## 26. Guest Mode Suppression (Night / Reminders)

Disables automations that assume normal family occupancy, such as night path lighting, energy-saving shutoffs, or loud announcements, when guests are visiting.

**When to use:** When an automation's default behavior would disturb a guest sleeping in a common area or turn off something they are using.

**Template (Condition Block):**
```yaml
  conditions:
    - condition: state
      entity_id: input_boolean.guest_mode
      state: 'off'
```

**Template (Energy Auto-Off Exception):**
Allows an auto-off timer during the day, but keeps the device on at night if a guest is present.
```yaml
  conditions:
    - condition: or
      conditions:
        - condition: time
          after: '08:00:00'
          before: '19:00:00'
        - condition: state
          entity_id: input_boolean.guest_mode
          state: 'off'
```

**Generic examples:**
- `Kitchen: Dish Light on Night Motion` (suppressed when guests present)
- `Kitchen: Turn Off A/C After 30m No Motion` (energy exception at night with guests)

---

## 27. Cross-Automation Time Guard

Uses the `last_triggered` attribute of a conflicting automation to block the current automation if the conflicting one fired recently.

**When to use:** When one action (e.g., turning off all lights to leave the house) should temporarily suppress an automatic reaction (e.g., opening the door turning the lights back on) that would otherwise defeat the intent of the first action.

**Template:**
```yaml
  conditions:
    - condition: template
      value_template: >
        {{ as_timestamp(now()) - as_timestamp(state_attr('automation.<target_automation>', 'last_triggered'), 0) > 300 }}
      alias: "Block if '<Target Automation>' fired within the last 5 minutes"
```

**Generic examples:**
- `Kitchen: Main Light on Door Open` (blocked for 5 minutes after `House: All Lights Off` triggers)

---

## 28. TTS Playback Guard (Non-Interruptive Announcements)

Prevents TTS announcements from interrupting active media playback (e.g., music, stories, podcasts). When a speaker is already `playing`, it is excluded from the `active_speakers` list so the TTS action simply skips that speaker instead of forcing a stream switch.

**When to use:** Any automation that sends TTS to speakers that may also play media via Music Assistant.

**Key design decisions:**
- **Playback check inside `active_speakers`** — each speaker is only added if its state is NOT `playing`. This is evaluated at action time, so it captures the live state.
- **No volume boost/restore when skipped** — if no speakers are available (all busy or quiet mode), the entire TTS block is skipped, including volume manipulation.
- **Telegram/push fallback stays outside the TTS guard** — notifications that already fire before the TTS block (like Telegram) are unaffected. The TTS skip is silent; the user still gets notified via phone.
- **Works alongside Quiet TTS guard** — the `input_boolean.quiet_tts_notifications` check remains the outermost guard. The playback check is an additional inner filter.

**Template (multi-room with Quiet TTS guard):**
```yaml
actions:
  - variables:
      active_speakers: >
        {% set ns = namespace(speakers=[]) %}
        {% if is_state('input_boolean.quiet_tts_notifications', 'off') %}
          {% if is_state('media_player.<speaker_1>', 'playing') == false %}
            {% set ns.speakers = ns.speakers + ['media_player.<speaker_1>'] %}
          {% endif %}
          {% if is_state('media_player.<speaker_2>', 'playing') == false %}
            {% set ns.speakers = ns.speakers + ['media_player.<speaker_2>'] %}
          {% endif %}
        {% endif %}
        {{ ns.speakers | join(', ') }}
  - if:
      - condition: template
        value_template: "{{ active_speakers | length > 0 }}"
    then:
      - action: media_player.volume_set
        target:
          entity_id: "{{ active_speakers }}"
        data:
          volume_level: 0.4
      - action: tts.speak
        ...
```

**Template (single-room, no Quiet TTS guard):**
```yaml
actions:
  - variables:
      active_speakers: >
        {% set ns = namespace(speakers=[]) %}
        {% if is_state('media_player.<speaker>', 'playing') == false %}
          {% set ns.speakers = ns.speakers + ['media_player.<speaker>'] %}
        {% endif %}
        {{ ns.speakers | join(', ') }}
  - if:
      - condition: template
        value_template: "{{ active_speakers | length > 0 }}"
    then:
      - action: tts.speak
        ...
```

**Generic examples:**
- `Calendar: Events Announcement` — skips speakers playing media
- `Bedroom: Weight Announcement with AI` — skips bedroom speaker during media playback

---

## 29. Sequential TTS Coordination & Speaker-Busy Guard

When multiple spoken announcements can trigger around the same time (e.g. morning weather and calendar), they compete for:
1. **AI Provider Generation**: Simultaneous calls can overload local LLM servers (like Ollama) or hit cloud rate limits.
2. **Media Player Playback**: Two `tts.speak` actions targeting the same speaker will clobber and cut each other off mid-sentence.

**When to use:** Any automation that delivers TTS speech or calls an AI provider where another automation might be active at or around the same time window.

**Key Techniques:**
1. **Upstream Automation Finish Wait**: Wait until the other automation's `current` attribute is 0 before calling AI.
2. **Speaker Busy Guard**: Wait until the target media player is not `playing` before adjusting volume and speaking.
3. **Resilient Direct Fallback**: If the AI call fails or times out, read the raw data directly from sensors/calendar instead of an unhelpful "I couldn't read this" error message.

**Template:**
```yaml
actions:
  # 1. Wait for upstream automation to finish (e.g. morning weather)
  - if:
      - condition: template
        value_template: "{{ trigger.id == 'today' and now().weekday() < 5 }}"
    then:
      - alias: "Wait for morning weather alert to finish if active"
        wait_template: "{{ is_state_attr('automation.<weather_alert>', 'current', 0) }}"
        timeout: "00:02:00"
        continue_on_timeout: true
      - delay:
          seconds: 2

  # 2. Call AI provider and format text...
  # [AI call sequence here]

  # 3. Speaker-Busy Guard before volume_set and tts.speak
  - if:
      - condition: state
        entity_id: input_boolean.quiet_tts_notifications
        state: 'off'
    then:
      - alias: "Wait for speaker to finish playing before speaking"
        wait_template: >-
          {{ not is_state('media_player.<speaker_1>', 'playing') and
             not is_state('media_player.<speaker_2>', 'playing') }}
        timeout: "00:01:30"
        continue_on_timeout: true
      - action: media_player.volume_set
        target:
          entity_id: "{{ active_speakers }}"
        data:
          volume_level: 0.4
      - action: tts.speak
        target:
          entity_id: tts.google_translate_<lang>
        data:
          media_player_entity_id: "{{ active_speakers }}"
          language: en
          message: >-
            {% if ai_response is defined and ai_response.status == 200 and ai_response.content is defined %}
              {{ ai_response.content }}
            {% else %}
              {# Resilient direct fallback reading the underlying entities #}
              ...
            {% endif %}
```

**Generic examples:**
- `Calendar: Events Announcement` — waits for weather alert to finish, then speaks calendar summary

---

## Mode Selection Guide

| Mode | When to use |
|------|-------------|
| `single` | One-shot actions, button toggles, notifications |
| `restart` | Occupancy flows, timers that should reset on re-trigger |
| `queued` | Actions that must complete in order (rare) |

---

## Documentation Checklist

After creating or modifying an automation:
1. Add or update its entry in `automations_kb.md`
2. Update `HOUSE_CONTEXT.md` if new devices, sensors, or room relationships are involved
3. Run `python3 tools/ha_toolkit.py audit_docs` to verify consistency

# Future Automations

This file is a design scratchpad for planned but not-yet-approved automations.
Use it to record the full intent, feasibility check, edge-case analysis, and
drafted YAML before asking the AI to implement anything in `automations.yaml`.

> **Why use this file?**
> Writing the full design first prevents half-finished logic from entering
> production. It also gives you a clear checklist for helpers, interactions, and
> verification steps before you commit to the change.

---

## Template: [Automation Name]

### The Concept

**Goal:** [One-sentence description of what the automation should do and why.]

**Strategy:** [How will you detect the trigger? What signal anchors the timing?
If timing is variable (e.g., "before bedtime"), describe how you will estimate it.]

---

### Feasibility Check

| Requirement | Available? | Entity / Device |
|---|---|---|
| [Trigger signal] | ✅ / ❌ | `[entity_id]` |
| [Notification channel 1] | ✅ / ❌ | `[notify.service]` |
| [TTS speaker] | ✅ / ❌ | `[media_player.*]` |
| [Presence or guard signal] | ✅ / ❌ | `[input_boolean.*]` |

**Missing hardware:** [None / List anything not yet available]

**New helpers required** (create in HA UI or `configuration.yaml`):

| Helper | Type | Purpose |
|---|---|---|
| `input_boolean.example_tracker` | `input_boolean` | Tracks whether action was completed today. Reset daily. |
| `input_datetime.example_time` | `input_datetime` (time only) | Configurable reminder time. |

---

### Required Entities

**Existing entities used:**
- `[entity_id]` — [description]

**New entities to create:**
- `[entity_id]` — Default: `[value]`. [How/when it is reset.]

---

### Edge Cases & Mitigation

| Edge Case | Risk | Mitigation |
|---|---|---|
| **Action already done** | Annoying redundant notification | Guard condition on the tracker boolean |
| **HA restart during wait** | State lost | Use `input_boolean` (survives restart); avoid in-memory waits |
| **User away from home** | Notification fires on empty house | Condition: `binary_sensor.house_occupied` is `on` |
| **Quiet TTS is on** | TTS skipped | TTS respects quiet guard; push notification always fires |
| **Retriggered while running** | Duplicate actions | Use `mode: single` or `mode: restart` as appropriate |

---

### Architecture

```text
┌─────────────────────────────┐     ┌───────────────────────────────┐
│ [Automation 1 Name]         │     │ [Automation 2 Name]           │
│ (Scheduled / Trigger-based) │     │ (Event-driven Guard)          │
├─────────────────────────────┤     ├───────────────────────────────┤
│ Trigger: [time/event]       │     │ Trigger: [event or state]     │
│                             │     │                               │
│ Condition:                  │     │ Condition:                    │
│  • [tracker] = off          │     │  • [tracker] = off            │
│  • house_occupied = on      │     │  • house_occupied = on        │
│                             │     │                               │
│ Action:                     │     │ Action:                       │
│  1. Push notification       │     │  1. Push notification (urgent)│
│  2. TTS (respects quiet)    │     │  2. TTS                       │
│  3. Wait for confirmation   │     │  3. Repeat if no confirm      │
└─────────────────────────────┘     └───────────────────────────────┘
```

---

### Drafted YAML

#### Automation 1: [Name]

```yaml
- id: [unique_id]
  alias: '[Category]: [Short Description]'
  description: >-
    [Full description including timing, fallback, and cross-room logic.]
  triggers:
    - trigger: time
      at: input_datetime.example_time
  conditions:
    - condition: state
      entity_id: input_boolean.example_tracker
      state: 'off'
    - condition: state
      entity_id: binary_sensor.house_occupied
      state: 'on'
  actions:
    # --- Push notification ---
    - action: notify.mobile_app_your_phone
      data:
        title: "[Emoji] [Title]"
        message: "[Message text]"
        data:
          tag: [notification_tag]
          persistent: true
          actions:
            - action: MARK_DONE
              title: "✅ Done"

    # --- TTS (respects Quiet TTS guard) ---
    - variables:
        active_speakers: >
          {% set ns = namespace(speakers=[]) %}
          {% if is_state('input_boolean.quiet_tts_notifications', 'off') %}
            {% set ns.speakers = ns.speakers + ['media_player.your_speaker'] %}
          {% endif %}
          {{ ns.speakers | join(', ') }}
    - if:
        - condition: template
          value_template: "{{ active_speakers | length > 0 }}"
      then:
        - action: tts.speak
          target:
            entity_id: tts.google_translate_en_com
          data:
            cache: false
            media_player_entity_id: "{{ active_speakers.split(', ')[0] }}"
            message: "[TTS message text]"

    # --- Wait for confirmation ---
    - wait_for_trigger:
        - platform: event
          event_type: mobile_app_notification_action
          event_data:
            action: MARK_DONE
        - platform: state
          entity_id: input_boolean.example_tracker
          to: 'on'
      timeout: "00:30:00"
      continue_on_timeout: true

    # --- Handle response ---
    - choose:
        - conditions:
            - condition: template
              value_template: "{{ wait.trigger is not none }}"
          sequence:
            - action: input_boolean.turn_on
              target:
                entity_id: input_boolean.example_tracker
            - action: notify.mobile_app_your_phone
              data:
                message: clear_notification
                data:
                  tag: [notification_tag]
      default:
        # Timeout — escalate
        - condition: state
          entity_id: input_boolean.example_tracker
          state: 'off'
        - action: notify.mobile_app_your_phone
          data:
            title: "⚠️ [Title] (2nd reminder)"
            message: "[Escalation message]"
  mode: restart
```

---

### Changes to `System: Daily Resets`

If the tracker boolean needs a daily reset, add to the existing `System: Daily Resets` automation:

```yaml
    - alias: Reset [tracker name] for new day
      action: input_boolean.turn_off
      target:
        entity_id: input_boolean.example_tracker
      data: {}
```

---

### Helpers to Create (via HA UI → Settings → Devices & Services → Helpers)

1. **`input_boolean.example_tracker`**
   - Name: `[Friendly Name]`
   - Icon: `mdi:[icon]`
   - Default: `off`

2. **`input_datetime.example_time`**
   - Name: `[Friendly Name]`
   - Has time: `true` / Has date: `false`
   - Icon: `mdi:clock-alert-outline`

---

### Interaction Analysis

| Existing Automation | Interaction | Risk |
|---|---|---|
| `[Automation A]` | [How it interacts] | ✅ / ⚠️ [Risk level and mitigation] |
| `System: Daily Resets` | Needs a new action line to reset the tracker | ✅ Additive change only |

---

### Deployment Checklist

1. Create helpers in HA UI
2. Add automations to `automations.yaml`
3. Add daily reset action to `System: Daily Resets`
4. Update `HOUSE_CONTEXT.md` with new automation section
5. Update `automations_kb.md` with new entries
6. Run `python3 tools/check_docs.py` for validation

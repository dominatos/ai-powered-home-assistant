# Sell Mode Plan

## Purpose

Create a "sell mode" that disables or neutralizes personal automations,
notifications, and language-specific content without deleting the underlying
configuration. This allows the system to stay present for later re-use while
making the home safer to hand over to a new owner.

---

## Scope

Sell mode should cover:
- Personalized notifications and TTS announcements
- AI prompt generation referencing personal names or schedules
- Personal presence and vehicle tracking behavior
- Optional sale-specific dashboard visibility

Not all items can be disabled by a runtime switch. Static labels, `customize:`
metadata, and hardcoded personal names/IDs still need manual review (see
`remove-customization.template.md`).

---

## Proposed Implementation

### 1. Global Runtime Switch

Add a global control in `configuration.yaml`:

```yaml
input_boolean:
  sell_mode:
    name: Sell Mode
    icon: mdi:door-open
    initial: false
```

Optionally, use a mode selector if you want more than two states:

```yaml
input_select:
  house_mode:
    name: House Mode
    options:
      - normal
      - sale
      - generic
    initial: normal
```

---

### 2. Guard Personalized Automations

For each personal automation, add a top-level condition or a guard around the
action sequence:

```yaml
conditions:
  - condition: state
    entity_id: input_boolean.sell_mode
    state: 'off'
```

Best applied to:
- TTS announcements referencing personal names
- Personal Telegram/push notifications
- AI prompt automations
- Presence/arrival/departure announcements

---

### 3. Neutralize AI and Language Behavior

For AI-driven automations, use Jinja2 to switch the prompt or language based on
sell mode:

```jinja
{% if is_state('input_boolean.sell_mode', 'on') %}
  Good morning! Today's weather will be...
{% else %}
  {{ states('input_text.ai_ollama_model') }} ... [personal prompt here]
{% endif %}
```

---

### 4. Dashboard Visibility

Use conditional cards to hide personal controls when sell mode is on:

```yaml
type: conditional
conditions:
  - entity: input_boolean.sell_mode
    state: 'off'
card:
  type: entities
  entities:
    - input_boolean.owner_home_stable
```

Or, if conditional cards are not feasible everywhere, rely on the runtime switch
to make the underlying automations inert and leave the cards visible but
non-functional.

---

### 5. Preserve Config — Manually Review Residual Personal Data

Keep `remove-customization.template.md` as the manual checklist for items that
cannot be fully disabled at runtime:
- `homeassistant.customize:` entries
- Personal text in automation descriptions, TTS prompts, and dashboard labels
- Notification target IDs (Telegram chat IDs, push device IDs)
- Any hardcoded personal metadata in `HOUSE_CONTEXT.md` or `dashboard.yaml`

---

## Implementation Steps

1. Add `input_boolean.sell_mode` to `configuration.yaml`.
2. Search automations for personal behaviors:
   - TTS announcements
   - Personal notification targets
   - AI prompts with personal content
   - Presence/arrival/departure flows
3. Add the guard condition to those automations.
4. Refactor AI prompt variables to choose generic copy during sell mode.
5. Add optional dashboard conditional cards or a banner showing sell mode is active.
6. Update `remove-customization.template.md` to document residual items.
7. Test by toggling `sell_mode`:
   - Ensure personal actions do not run.
   - Ensure generic mode applies if selected.
   - Verify dashboard behavior.

---

## Verification

- Enable sell mode and verify personal automations do not execute.
- Confirm no personal TTS or personal notification messages are sent while sell
  mode is active.
- Confirm the underlying automations remain present and can return to normal
  operation when sell mode is turned off.
- Review `remove-customization.template.md` for any manual cleanup items.

---

## Notes

- Sell mode is a safety layer, not a full replacement for cleanup.
- Static personal data still exists until manually edited or removed.
- Keep this plan separate from `remove-customization.template.md` to distinguish
  implementation strategy from the cleanup checklist.

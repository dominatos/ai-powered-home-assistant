# Remove Customization Checklist

This file documents the personalized Home Assistant configuration, automations,
dashboards, and notifications that should be reviewed, removed, or reconfigured
before handing over the home to a new owner.

It is not an automated migration script. Use it as a manual handoff checklist
and update it whenever new personalized logic is added.

---

## Purpose

- Identify personal automations, people tracking, and notification targets.
- Mark what must be sanitized or replaced to leave a generic smart home setup.
- Help the next owner avoid privacy leaks and personal-behavior logic.

---

## Before Sale / Handover: Review These Categories

### 1. Personal People Tracking and Zones

- `person.*` entities for each resident
- `zone.*` entries for personal work or home zones
- Any personal presence-related `input_boolean` helpers (e.g., `input_boolean.owner_home_stable`)

**Why**: These entities are specific to current residents and should be removed,
renamed, or replaced with generic presence sensors or guest-friendly alternatives.

---

### 2. Personal Calendar Integration

- `calendar.*` entities connected to personal or family calendars
- Automations that call `calendar.get_events` for personal announcements

**Why**: The family calendar is personal data. Remove or replace it with a shared
neutral calendar, or disable related automations.

---

### 3. Personalized Voice Announcements and AI Prompts

- Any automation that generates personalized TTS messages referencing residents
  by name or private attributes
- AI prompt templates that reference personal names, schedules, or private health data
- Any automation using language-specific TTS that should be replaced with the
  language of the next owner

**Why**: These automations contain personal context that is inappropriate for a
handover.

---

### 4. Personal Notification Channels and Chat IDs

- `notify.*` services targeting personal mobile apps
- `telegram_client.send_messages` calls with hardcoded personal chat IDs
- Any other hardcoded personal notification targets

**Why**: Personal notification targets should not remain in a generic handoff
configuration. The next owner will need to configure their own.

---

### 5. Personal Vehicle Tracking

- `device_tracker.*` for any specific vehicle or resident's phone
- Car arrival/departure automations specific to the current owner's vehicle
- Car-related dashboard cards and map views

**Why**: Vehicle tracker data and car arrival/departure automations expose
private mobility habits.

---

### 6. Room or Person-Specific Helper Entities

- Helpers named after specific residents
- Routine helpers (sleep schedules, diet tracking, etc.) specific to current
  occupants

**Why**: Highly tailored helpers may confuse the next owner or trigger
unexpected behavior.

---

### 7. Local AI Model References

- Local LLM host URLs (e.g., Ollama endpoints pointing to a personal server)
- AI model names and authentication tokens

**Why**: The next owner may not want or have a local AI server. Note the
dependency clearly in a handover document so they can remove or reconfigure it.

---

## Recommended Actions

- Audit all automations in `automations.yaml` for:
  - `person.` entities with personal names
  - `zone.` entries that are personal zones
  - Personal calendar references
  - Hardcoded notification targets (push, Telegram, SMS)
  - AI prompt templates referencing personal names or private data
  - Vehicle trackers and location-based automations

- Audit dashboards in `dashboard.yaml` for:
  - Personal person cards or ETA cards
  - Banners referencing a named person
  - Vehicle tracker cards

- Audit `configuration.yaml` for:
  - Personal `input_boolean` helpers and zone customizations
  - Personal `customize:` friendly names
  - Any external URLs or internal IPs belonging to the current owner's network

- Audit documentation files:
  - `HOUSE_CONTEXT.md` — remove or anonymize personal details
  - Any temporary or notes files that contain personal information

---

## What Should Remain Generic

The following may remain if they serve general home automation purposes and do
not expose personal data:

- Lighting, motion, temperature, humidity, and safety automations
- A/C and appliance control
- Night lights, motion-driven lights, and energy-saving logic
- General alerts that do not reference specific people or personal schedules

---

## Handoff Guidance

- Do not remove standard safety or utility automations unless the next owner
  explicitly requests it.
- Prefer disabling or anonymizing personal automations over deleting the
  underlying generic infrastructure.
- Keep the final handoff as simple as possible while removing personal identities
  and data flows.

---

## Maintenance Note

Update this file whenever you add or change:

- Personal people tracking
- Family or shared calendar announcements
- AI-generated personal messages
- Personal notification targets
- Vehicle tracking automations
- Dashboard cards that expose individual family routines

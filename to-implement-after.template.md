# To Implement After

> **Instructions for the user:** Use this file to record future high-value automation improvements or complex logic changes you thought of but decided to postpone. This keeps your main `automations.yaml` clean from speculative or half-finished code, while ensuring good ideas aren't lost.
>
> *Delete this instruction block when you are done.*

---

## Priority 1: Safety System Hardening

### Water leak debounce and confirmation

- Add a short confirmation window to leak triggers, for example requiring each
  leak sensor to remain `on` for 5–10 seconds before closing the valve.
- Keep a Home Assistant startup re-check path so leaks already active at startup
  are still handled.
- Do not require multiple leak sensors before closing the valve. A single confirmed
  leak in one room should still be enough to trigger water shutdown.

### Water valve close verification

- After the valve switch is turned off, wait 10–30 seconds and verify that the
  valve switch state is actually `off`.
- If the valve does not confirm closed, send an urgent notification and create a
  persistent Home Assistant notification.
- Keep this as verification and escalation only; do not add risky automatic
  reopen behavior.

### Manual water-safety override

- Add an explicit helper such as `input_boolean.water_safety_auto_close_enabled`.
- When enabled, leak detection should close the valve as it does today.
- When disabled, leak detection should notify loudly but not close the valve.
- Avoid remote "reopen after leak" shortcuts unless separately designed and
  approved, because reopening after a real leak can be unsafe.

---

## Priority 2: Notification Throttling

### Reduce repeated alert noise

- Update high-power or high-usage warning automations so they do not repeat
  notifications indefinitely at the same frequency.
- Suggested behavior:
  - first 3 alerts: every minute while the sensor stays above threshold
  - after that: lower-frequency alerts (e.g., every 5 minutes)
  - keep a persistent notification active until the condition clears
- Preserve the current safety intent: the house should still clearly warn when
  the condition remains active.

---

## Priority 3: Documentation / Correctness Cleanup

### Disabled illuminance conditions

- Some automations contain disabled illuminance conditions.
- Decide whether each is intentionally parked for future use.
- If intentional, document the reason in `HOUSE_CONTEXT.md`.
- If obsolete, remove only after explicit approval.

### Missed TTS timeout visibility

- Automations that wait for presence before speaking may silently timeout.
- Add a low-noise trace (logbook entry or optional notification) so missed
  announcements are easier to debug.
- This should not change the normal announcement path.

---

## Priority [N]: [Feature Name]

### [Sub-feature or specific logic]
- Description of the improvement.
- Rationale: Why this change is needed.
- What needs to be changed.
- Affected automations/entities: List the automations or entities impacted.
- Potential risks or dependencies.

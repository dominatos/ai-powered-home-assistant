# To Assign

> **Instructions for the user:** This file lists entities, helpers, and devices that are not explicitly assigned to a single physical room in `HOUSE_CONTEXT.md` (e.g., system-wide variables, global sensors, network devices). Tracking them here helps the AI understand their purpose without cluttering room descriptions.
>
> *Delete this instruction block when you are done.*

---

## Global / Multi-Room Helpers

| Entity | Usage | Context |
|--------|-------|---------|
| `input_boolean.quiet_tts_notifications` | High | Suppresses TTS speech actions across all rooms while leaving other notifications (Telegram, push) active. |
| `sensor.total_house_power` | Medium | Used by power warning automations to trigger alerts and flash lights. |
| `input_boolean.guest_mode` | Medium | When on, suppresses personal automations and adjusts presence logic. |
| `person.owner_1` | Medium | Primary resident; used for presence and arrival/departure logic. |
| `person.owner_2` | Medium | Secondary resident; used for presence and departure notifications. |

## System / Appliance Entities

| Entity | Usage | Context |
|--------|-------|---------|
| `climate.main_thermostat` | High | Main house thermostat; synced with boiler relay and managed by schedule automations. |
| `switch.boiler_relay` | Medium | Boiler dry relay; controlled by thermostat demand sync automation. |
| `sensor.energy_monitoring_main_power` | Medium | Main energy monitor; used by power warning automations. |
| `input_boolean.water_safety_auto_close_enabled` | Low | Override toggle for water valve auto-close on leak detection. |

## Network / Phone Sensors

| Entity | Usage | Context |
|--------|-------|---------|
| `sensor.phone_1_wifi_connection` | Low | Primary phone WiFi; used to detect home presence. |
| `sensor.phone_2_wifi_connection` | Low | Secondary phone WiFi; used to detect home presence. |

## Tablet / Dashboard Entities

| Entity | Usage | Context |
|--------|-------|---------|
| `sensor.dashboard_tablet_battery` | Low | Kitchen tablet battery level; shown in dashboard. |
| `button.dashboard_tablet_wake` | Low | Wakes the kitchen tablet screen. |
| `button.dashboard_tablet_sleep` | Low | Puts the kitchen tablet screen to sleep. |
| `input_boolean.kitchen_tablet_screen_awake` | Medium | Tracks screen state for the kitchen tablet; used by motion, door, and sleep automations. |

## Thermostat Schedule Helpers

| Entity | Usage | Context |
|--------|-------|---------|
| `input_datetime.thermostat_schedule_time_1` | Low | Morning schedule time slot. |
| `input_number.thermostat_schedule_temp_1` | Low | Morning schedule temperature. |
| `input_datetime.thermostat_schedule_time_2` | Low | Day schedule time slot. |
| `input_number.thermostat_schedule_temp_2` | Low | Day schedule temperature. |
| `input_datetime.thermostat_schedule_time_3` | Low | Evening schedule time slot. |
| `input_number.thermostat_schedule_temp_3` | Low | Evening schedule temperature. |
| `input_datetime.thermostat_schedule_time_4` | Low | Night schedule time slot. |
| `input_number.thermostat_schedule_temp_4` | Low | Night schedule temperature. |
| `input_number.thermostat_night_away_temp` | Low | Shared setpoint for Away/Night override modes. |

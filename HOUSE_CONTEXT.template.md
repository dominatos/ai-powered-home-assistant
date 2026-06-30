# House Context Template

> **Instructions for the user:** Fill this file with the physical layout of your house, the logical naming of your rooms, and the specific smart devices in each room. The AI uses this file to understand the "real world" context behind your `automations.yaml` file, preventing it from making dangerous assumptions (e.g., turning off the bathroom light when someone is in the shower).
> 
> *Delete this instruction block when you are done.*

## General House Rules & Quirks
- *Example: The house has 2 floors. The router is on the 1st floor.*
- *Example: We have a cat, so motion sensors near the floor should not trigger the alarm.*
- *Example: The "Night Mode" boolean is used to disable all TTS announcements.*

## Rooms & Layout

### 1. Kitchen (`cucina`)
- **Location:** Ground floor, connects to the living room and hallway.
- **Lighting:** Main ceiling light (`light.kitchen_main`), under-cabinet LED strip (`light.kitchen_led`).
- **Sensors:** 
  - Motion sensor on the ceiling (`binary_sensor.kitchen_motion`).
  - Temperature & Humidity (`sensor.kitchen_temp`).
  - Window contact sensor (`binary_sensor.kitchen_window`).
- **Appliances:**
  - Smart plug on the oven to track power (`sensor.oven_power`).
  - Smart plug on the dishwasher.

### 2. Bathroom (`bagno`)
- **Location:** Ground floor, end of the hallway.
- **Lighting:** Ceiling light (`light.bathroom_main`), Mirror light (`light.bathroom_mirror`).
- **Sensors:**
  - Motion sensor (`binary_sensor.bathroom_motion`).
  - Door contact sensor (`binary_sensor.bathroom_door`). *Critical for knowing if someone is inside.*
  - Humidity sensor (`sensor.bathroom_humidity`). *Used to detect showers.*

### 3. Bedroom (`letto`)
- **Location:** First floor.
- **Lighting:** Bedside lamps (`light.bed_lamp_left`, `light.bed_lamp_right`).
- **Controls:** IKEA 4-button remote on the wall. 
  - Button 1: Toggle lamps.
  - Button 2: Toggle A/C.
- **Climate:** Split A/C unit (`climate.bedroom_ac`), controlled via IR blaster.

## Critical Automations (High Level)
- *List any automations that must NEVER be broken by the AI.*
- *Example: The Water Leak safety system must always shut off the main valve (`switch.main_water_valve`) if any leak sensor triggers.*
- *Example: The Blackout prevention system must turn off the A/C if total house power exceeds 3000W.*

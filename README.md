# AI-Powered Home Assistant

This repository is a framework and template for managing your Home Assistant instance using an LLM (like Claude, ChatGPT, or Gemini) as your personal Senior Home Assistant Engineer.

Many people use AI to generate simple Home Assistant YAML scripts, but they quickly run into problems: the AI hallucinates entity IDs, breaks existing automations, or misunderstands how the physical house is laid out (e.g., turning off the bathroom light while someone is in the shower).

This repository solves that problem by providing a **strict context and tooling framework**.

## What's Included

### 🛠️ Sync & Export Scripts (`tools/`)
Shell scripts to safely move files between your live Home Assistant and this repository:

| Script | Purpose |
|--------|---------|
| `tools/sync_from_homeassistant.sh` | Pull latest config from HA → repo (run *before* AI work) |
| `tools/sync_to_homeassistant.sh` | Push AI-generated changes repo → HA (run *after* review) |
| `tools/export_ha_inventory.sh` | Export all device/entity IDs so the AI never guesses |

All scripts create automatic backups, support `--dry-run` and `--diff` flags, and require a clean Git tree for safety. See [Sync Your Configuration](#3-sync-your-configuration-tools-folder) below for details.

### 🤖 Ready-to-Use AI Prompts (`prompts/`)
Drop-in prompt templates you paste into your AI IDE to perform specific tasks:

| Prompt | What It Does |
|--------|-------------|
| `prompts/prompt.txt` | **Main session prompt** — the starting point for any AI task |
| `prompts/HC-gen.md` | Auto-generate `HOUSE_CONTEXT.md` from your existing inventory |
| `prompts/naming-fix.md` | Standardize all automation names to `Room: Action` format |
| `prompts/energy-saving.md` | Audit for energy waste (vampire drain, missing timeouts) |
| `prompts/security-audit.md` | Find security flaws and missing fallbacks in your automations |
| `prompts/dashboard-gen.md` | Auto-generate a Lovelace dashboard from your house context |
| `prompts/yaml-cleanup.md` | Modernize YAML syntax without changing behavior |
| `prompts/optimise.md` | Merge redundant automations and improve robustness |
| `prompts/invent-new.md` | Brainstorm brand new automations based on your devices |
| `prompts/describe-idea.md` | Architect your idea into a detailed plan in `FUTURE-automations.md` |
| `prompts/replace-device.md` | Swap old entity IDs for new ones across all files |
| `prompts/troubleshoot-trace.md` | Paste a JSON trace or error log and get a plain-English diagnosis |

### 📋 Context & Rules
| File | Purpose |
|------|---------|
| `INSTRUCTIONS.md` | Strict rules that prevent the AI from guessing or breaking things |
| `HOUSE_CONTEXT.template.md` | Template to describe your physical house layout and devices |

## How It Works

Instead of just asking the AI to "write an automation," you provide it with this entire repository (or parts of it) so the AI understands:
1. **Your Strict Rules:** (`INSTRUCTIONS.md`) Forces the AI to ask for permission before deleting things, validates changes against other automations, and prevents it from rewriting your entire configuration file.
2. **Your Physical House:** (`HOUSE_CONTEXT.template.md`) Gives the AI "eyes" into the real world. It knows which room connects to which, and what sensors are actually present.
3. **Your Current Automations:** You sync your actual YAML files here so the AI can analyze how a new automation might conflict with an old one.

## Getting Started

### 1. Clone this Template
Clone or download this repository to your computer (preferably to a local workspace, not directly into your production `/homeassistant` folder).

### 2. Set Up Your Context
1. Rename `HOUSE_CONTEXT.template.md` to `HOUSE_CONTEXT.md`.
2. Open it and document your physical house layout, rooms, and devices. Be as descriptive as possible. *(Tip: If you already have a lot of devices and automations in Home Assistant, you can paste the contents of `prompts/HC-gen.md` into the AI IDE to have it automatically generate your `HOUSE_CONTEXT.md` for you!)*
3. Open `prompts/prompt.txt` and read the prompt structure. Update the `Repository root:` path to match your local setup.

### 3. Sync Your Configuration (`tools/` folder)

This repository includes several scripts in the `tools/` folder to safely move files between your live Home Assistant server and this local repository. 

*Note: These scripts default to `/homeassistant` as the Home Assistant directory. If your setup differs (e.g., you use `/config` on HAOS), you can override the paths using environment variables like `SOURCE_ROOT` and `TARGET_ROOT`.*

**Available Scripts:**

- **`tools/sync_from_homeassistant.sh`**
  Pulls the latest automations, scripts, scenes, and configurations from your live Home Assistant server into this repository. Run this *before* you start working with the AI to ensure the AI has the most up-to-date context. 
  *Usage:* `./tools/sync_from_homeassistant.sh` (Supports `--dry-run` and `--diff`)

- **`tools/sync_to_homeassistant.sh`**
  Pushes the generated and modified configuration files from this repository back to your live Home Assistant server. Run this *after* the AI has finished its work and you have reviewed the changes.
  *Usage:* `./tools/sync_to_homeassistant.sh` (Supports `--dry-run` and `--diff`)

- **`tools/export_ha_inventory.sh`**
  Reads the hidden `.storage` folder in Home Assistant and exports a clean, sanitized list of all your devices and entities into `ha_device_inventory.json` and `inventory.txt`. This gives the AI exact entity IDs so it never has to guess. (The `sync_from_homeassistant.sh` script usually runs this automatically).
  *Usage:* `./tools/export_ha_inventory.sh` (Uses `STORAGE_DIR` environment variable)

**Safety Features:**
Both sync scripts automatically create backups in a `.sync_backups/` folder before making any changes. If something goes wrong, you can easily run the `restore.sh` script found in the backup folder to revert the changes. They also require your Git working tree to be clean before running, ensuring you can undo any mistakes via Git.

### 4. Setup AI IDE (Antigravity IDE, Cursor, VS Code)
For the best experience, do not use simple web chats (like ChatGPT). Instead, use an agentic AI IDE (like Antigravity IDE, Cursor, or Visual Studio Code with an AI extension) installed on your personal PC:
1. Open this repository folder in your AI IDE.
2. The AI will automatically have access to all your files (`automations.yaml`, `HOUSE_CONTEXT.md`, etc.).
3. When you are ready to build a complex automation, open the AI chat panel inside the IDE.
4. Paste the contents of `prompts/prompt.txt`, ensuring you fill out the `[INSERT_YOUR_CURRENT_TASK_HERE]` block.
5. The AI IDE will read your files, write the new automations, and even execute the sync tools for you!

### 5. Connecting to HAOS
If your Home Assistant is running on a dedicated device like a Raspberry Pi or Mini PC (HAOS), you should keep this repository on your personal PC and use the network to sync:
1. Enable the **Samba Share** or **SSH & Web Terminal** Add-on in Home Assistant OS.
2. Mount the Home Assistant `/config` folder to your PC, or configure the `tools/sync_from_homeassistant.sh` script to pull files via SSH/SCP.
3. The AI IDE runs entirely on your PC, safely modifying the files in this local repository. Once the AI finishes writing an automation and you approve it, use the sync tools to push the updated `automations.yaml` back to HAOS.

### 6. Git Syncing (Advanced)
Alternatively, you can use a private Git repository to sync changes between your PC and HAOS.

First, set up the base template on HAOS (via SSH/Terminal):
```bash
cd /config
git clone https://github.com/dominatos/ai-powered-home-assistant/
cd ai-powered-home-assistant
rm -rf .git
```

Next, create a private repository to sync with your PC:
1. Create a **New Repository** on GitHub, GitLab, or Bitbucket. Make sure to set its visibility to **Private**.
2. Initialize your local Git repository on HAOS and push it to your new remote:
   ```bash
   git init
   git add .
   git commit -m "Initial config"
   git branch -M main
   git remote add origin <your-private-repo-url>
   git push -u origin main
   ```
3. **On your PC**, clone your new *private* repository and open it in your AI IDE.
4. As the AI generates and modifies files on your PC, you can commit and push them. Then, simply run `git pull` on HAOS to deploy the updates and launch `tools/sync_to_homeassistant.sh` to push the changes.

## Example Use Cases (What to ask the AI)

Once your context is set up and your files are synced, you can ask your AI IDE to perform complex tasks safely. Here are a few examples of what you can paste into the `[INSERT_YOUR_CURRENT_TASK_HERE]` section of `prompts/prompt.txt`:

### 1. Creating a New Smart Automation
> "I bought a new Zigbee motion sensor and a smart bulb for the bathroom. I've added them to `HOUSE_CONTEXT.md`. Please write an automation that turns on the bathroom light when motion is detected, but only if the illuminance is below 50 lux. Also, make sure it turns off after 5 minutes of no motion, but DO NOT turn it off if the shower humidity sensor indicates someone is taking a shower."

### 2. Debugging Conflicting Rules
> "My living room lights keep turning off randomly while we are watching TV. Please review the automations related to the Living Room in `automations.yaml`. Identify any conflicting rules or motion sensor timeouts, explain the issue, and propose a fix that keeps the lights on if the TV (media_player.living_room_tv) is playing."

### 3. Context Updates & Scaffolding
> "I just added 5 new smart plugs around the house for holiday lights. Here is a rough list of where I put them and what they are called in Home Assistant. Please update `HOUSE_CONTEXT.md` to include these new devices in their respective rooms, and then write a script to turn them all on at sunset and off at midnight."

### 4. Analyzing Blast Radius
> "I want to change the 'Goodnight' script to also lock the front door and arm the alarm. Before doing this, please analyze all other automations that call the 'Goodnight' script. Will this change cause issues if someone runs it while someone else is still in the backyard?"

### 5. Using Utility Prompts
This repository ships with 11 ready-to-use prompt templates in the `prompts/` folder. See the full list in the [What's Included](#whats-included) section above. Simply copy the contents of any prompt file, paste it into your AI IDE chat, and fill in the placeholders.

## The Rules Engine (`INSTRUCTIONS.md`)
The `INSTRUCTIONS.md` file is the secret sauce. It forces the AI to:
- **Never guess:** If a device is missing from the context, it must stop and ask you.
- **Design for resilience:** It forces the AI to consider "off" logic as much as "on" logic (e.g., what happens if the motion sensor never triggers again?).
- **Respect the blast radius:** It forbids the AI from refactoring or "cleaning up" files unless explicitly requested.

## Security Warning
> ⚠️ **DO NOT UPLOAD YOUR SECRETS!**
> If you upload your version of this repository to GitHub, ensure that `.gitignore` is properly configured. **Never commit `secrets.yaml`, `.storage/`, or files containing MQTT passwords (like `zigbee2mqtt/configuration.yaml`) to a public repository.**

## Enjoy!
Using this framework, you can build incredibly complex, intelligent automations that go far beyond the limitations of simple "If this, then that" apps like Tuya Smart, without breaking your live home environment.

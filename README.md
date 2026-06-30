# AI-Powered Home Assistant

This repository is a framework and template for managing your Home Assistant instance using an LLM (like Claude, ChatGPT, or Gemini) as your personal Senior Home Assistant Engineer.

Many people use AI to generate simple Home Assistant YAML scripts, but they quickly run into problems: the AI hallucinates entity IDs, breaks existing automations, or misunderstands how the physical house is laid out (e.g., turning off the bathroom light while someone is in the shower).

This repository solves that problem by providing a **strict context and tooling framework**.

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
2. Open it and document your physical house layout, rooms, and devices. Be as descriptive as possible.
3. Open `prompt.txt` and read the prompt structure. Update the `Repository root:` path to match your local setup.

### 3. Sync Your Configuration
Use the bash and python scripts in the `tools/` folder to securely export your live Home Assistant entity inventory and configuration files into this repository. (Make sure to update the scripts if you have a non-standard Home Assistant setup).

### 4. Setup AI IDE (Antigravity IDE, Cursor, VS Code)
For the best experience, do not use simple web chats (like ChatGPT). Instead, use an agentic AI IDE (like Antigravity IDE, Cursor, or Visual Studio Code with an AI extension) installed on your personal PC:
1. Open this repository folder in your AI IDE.
2. The AI will automatically have access to all your files (`automations.yaml`, `HOUSE_CONTEXT.md`, etc.).
3. When you are ready to build a complex automation, open the AI chat panel inside the IDE.
4. Paste the contents of `prompt.txt`, ensuring you fill out the `[INSERT_YOUR_CURRENT_TASK_HERE]` block.
5. The AI IDE will read your files, write the new automations, and even execute the sync tools for you!

### 5. Connecting to HAOS
If your Home Assistant is running on a dedicated device like a Raspberry Pi or Mini PC (HAOS), you should keep this repository on your personal PC and use the network to sync:
1. Enable the **Samba Share** or **SSH & Web Terminal** Add-on in Home Assistant OS.
2. Mount the Home Assistant `/config` folder to your PC, or configure the `tools/sync_from_homeassistant.sh` script to pull files via SSH/SCP.
3. The AI IDE runs entirely on your PC, safely modifying the files in this local repository. Once the AI finishes writing an automation and you approve it, use the sync tools to push the updated `automations.yaml` back to HAOS.

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

# Local AI Integration with Ollama

This document covers how to run a local Ollama instance and integrate it with
Home Assistant automations for AI-generated TTS announcements, weather summaries,
and other text generation tasks.

---

## Why Local AI?

Running a local LLM (via Ollama) for Home Assistant gives you:
- **No API costs** — completely free after hardware setup
- **Privacy** — prompts and responses never leave your network
- **Low latency** — no internet round-trips for short text generation
- **Custom models** — fine-tune behavior via system prompts

---

## Requirements

| Requirement | Notes |
|---|---|
| Ollama server | Runs on any PC/Mac/NAS with a GPU or fast CPU |
| Network access | HA must reach the Ollama host (same LAN or VPN) |
| `rest_command` in HA | Built into HA — no custom integration needed |
| Ollama model | Pull any model from `ollama.com/library` |

---

## Recommended Models

| Model | Size | Best For |
|---|---|---|
| `qwen2.5:7b` | ~4 GB | Fast, good at concise text |
| `llama3.1:8b` | ~5 GB | General purpose |
| `mistral:7b` | ~4 GB | Good instruction following |
| `phi3:mini` | ~2 GB | Very fast, lower quality |

For TTS announcements, smaller models (7B or less) are recommended — they
respond in 2–5 seconds and generate short, well-formed text.

---

## Creating a Custom "No-Think" Model

By default, some models output reasoning ("thinking") steps before the answer.
For TTS, you only want the final answer. Create a custom model that suppresses
this:

```bash
# API call
curl -s -X POST http://<YOUR_OLLAMA_HOST>:11434/api/create \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-nothink",
    "from": "qwen2.5:7b",
    "system": "You are a concise assistant.\n\nAlways answer directly.\nNever output reasoning or thinking.\nNever explain your thought process.\nRespond only with the final answer.",
    "params": {
      "temperature": 0.6,
      "top_p": 0.95,
      "repeat_penalty": 1.0,
      "num_predict": 256
    }
  }'
```

Equivalent Modelfile:

```dockerfile
FROM qwen2.5:7b

SYSTEM You are a concise assistant.

Always answer directly.
Never output reasoning or thinking.
Never explain your thought process.
Respond only with the final answer.

PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER repeat_penalty 1.0
PARAMETER num_predict 256
```

---

## Home Assistant Configuration

### `rest_command` in `configuration.yaml`

```yaml
rest_command:
  ollama_generate:
    url: "http://<YOUR_OLLAMA_HOST>:11434/api/generate"
    method: POST
    timeout: 60
    headers:
      Content-Type: "application/json"
    payload: >
      {
        "model": "{{ model | default('your-model-nothink') }}",
        "prompt": {{ prompt | to_json }},
        "stream": false,
        "think": false,
        "options": {
          "num_predict": 500,
          "temperature": 0.9
        }
      }
```

**Key parameters:**
- `"think": false` — disables chain-of-thought output (Qwen3+ models only)
- `"stream": false` — required for `rest_command` (needs the full response at once)
- `"num_predict": 500` — max tokens per response; keep short for TTS
- `"temperature": 0.9` — higher = more varied/creative output

---

## Using Ollama in Automations

### Example: AI-Generated TTS Announcement

```yaml
- id: example_ai_tts_announcement
  alias: 'Example: AI Morning Greeting'
  description: >-
    Calls Ollama to generate a short morning greeting and speaks it via TTS.
    Respects the Quiet TTS guard.
  triggers:
    - trigger: time
      at: "08:00:00"
  conditions:
    - condition: state
      entity_id: binary_sensor.house_occupied
      state: 'on'
  actions:
    # --- Build the prompt ---
    - variables:
        ai_prompt: >
          Generate a short, friendly good morning greeting in English.
          Maximum 15 words. No emojis.

    # --- Call Ollama ---
    - action: rest_command.ollama_generate
      data:
        prompt: "{{ ai_prompt }}"
      response_variable: ollama_response

    # --- Extract the response text ---
    - variables:
        ai_text: "{{ (ollama_response.content | from_json).response | trim }}"

    # --- TTS (respects Quiet TTS guard) ---
    - condition: state
      entity_id: input_boolean.quiet_tts_notifications
      state: 'off'
    - action: tts.speak
      target:
        entity_id: tts.google_translate_en_com
      data:
        cache: false
        media_player_entity_id: media_player.your_speaker
        message: "{{ ai_text }}"
  mode: single
```

---

## Inspecting and Testing

```bash
# List all models
curl -s http://<YOUR_OLLAMA_HOST>:11434/api/tags | python3 -m json.tool

# Quick test
curl -s http://<YOUR_OLLAMA_HOST>:11434/api/generate \
  -d '{"model": "your-model-nothink", "prompt": "Say hello in one sentence.", "stream": false}'

# Show model configuration
curl -s http://<YOUR_OLLAMA_HOST>:11434/api/show \
  -d '{"name": "your-model-nothink"}' | python3 -m json.tool
```

---

## Recreating After Ollama Reset

If Ollama is reinstalled or the model is lost, re-run the creation API call.
Pull the parent model first:

```bash
curl -s http://<YOUR_OLLAMA_HOST>:11434/api/pull -d '{"name": "qwen2.5:7b"}'
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `rest_command` returns `500` | Ollama not running or wrong host | `curl http://<host>:11434/api/tags` |
| Long delay (>10s) | Model too large for hardware | Switch to a smaller model |
| Response includes `<think>` text | Thinking mode not disabled | Add `"think": false` or use a custom model with system prompt |
| Empty TTS output | Response parsing failed | Log `ollama_response.content` in Developer Tools → Template |
| HA can't reach Ollama | Firewall or VLAN | Allow TCP 11434 from HA's IP to the Ollama host |

# NFS Music Library + Music Assistant + Playlist Generator

This guide explains how to set up a local audio library on an NFS share, serve it through Home Assistant's Music Assistant integration, and keep an M3U playlist automatically in sync using `python_scripts/create_playlist.py`.

## What It Does

```
NFS Server (your NAS / Linux box)
  └─ /export/music/          ← audio files live here
       │
       ├─ NFS mount on HA host at /media/music
       │
       ├─ create_playlist.py scans the folder → writes playlist.m3u
       │
       └─ Music Assistant reads playlist.m3u via Filesystem provider
            └─ Speakers play from the playlist
```

- **NFS share** holds your audio files (MP3, FLAC, WAV, AAC, OGG, M4A, WMA, OPUS).
- **`create_playlist.py`** scans the folder and generates a valid `#EXTM3U` playlist file.
- **Music Assistant** picks up the M3U via its Filesystem (NFS) provider and makes it available for playback on any speaker.
- An optional **automation** re-generates the playlist on a schedule so new files appear without manual intervention.

## Prerequisites

| Component | Requirement |
|-----------|-------------|
| NFS server | A NAS or Linux machine sharing an audio folder (e.g., `/export/music`) |
| Home Assistant OS | `python_scripts` must be enabled in `configuration.yaml` |
| Music Assistant | Installed as an HACS integration or add-on |
| NFS client | HA host must be able to mount NFS shares (HAOS has built-in NFS support) |

## Step 1 — Export the NFS Share

On your NFS server (example: Ubuntu/Debian):

```bash
# Install NFS server
sudo apt install nfs-kernel-server

# Create the music directory
sudo mkdir -p /export/music

# Add to /etc/exports:
# /export/music 192.168.1.X/24(rw,sync,no_subtree_check)
sudo exportfs -ra

# Start the service
sudo systemctl enable --now nfs-kernel-server
```

Place your audio files in `/export/music` (subdirectories are supported and sorted alphabetically).

## Step 2 — Mount NFS on Home Assistant Host

### HAOS (Supervised / OS)

Use the built-in network storage workflow:

1. Go to **Settings → System → Storage**.
2. Click **Add network storage**.
3. Select **NFS** as the type.
4. Enter the NFS server address and share path (e.g., `192.168.1.X:/export/music`).
5. Set the mount point to `/media/music`.
6. Save. Home Assistant will mount the share and make it available at `/media/music`.

### Docker / HA Core

Add a volume mount to your `docker-compose.yml` or `docker run` command:

```yaml
volumes:
  - /export/music:/media/music:ro
```

Or mount on the host and map into the container.

## Step 3 — Enable python_scripts

In `configuration.yaml`:

```yaml
python_script:
```

That's it — just the one line. HA will look for scripts in `/config/python_scripts/`.

## Step 4 — Place create_playlist.py

Copy `python_scripts/create_playlist.py` to your HA config directory:

```bash
cp python_scripts/create_playlist.py /config/python_scripts/
```

### Test it manually

```bash
# On the HA host:
    python3 /config/python_scripts/create_playlist.py /media/music /media/music/playlist.m3u
```

You should see: `Playlist saved to /media/music/playlist.m3u (N tracks)`

## Step 5 — Configure shell_command

Add to `configuration.yaml`:

```yaml
shell_command:
  create_playlist: >
python3 /config/python_scripts/create_playlist.py /media/music /media/music/playlist.m3u
```

## Step 6 — Set Up Music Assistant Filesystem Provider

1. Open **Music Assistant** from the HA sidebar.
2. Go to **Settings → Providers → Add Provider**.
3. Select **Filesystem (local/network)**.
4. Configure:
   - **Name**: `NFS Music Library` (or any name)
   - **Path type**: NFS
   - **URL**: `nfs://192.168.1.X/export/music` (or the mounted path `/media/music`)
   - **Playlist folder**: Inside the NFS music source (e.g., `/media/music` or `/export/music`)
5. Save. Music Assistant will scan and index the files.

## Step 7 — Store Playlist Name

Add an `input_text` helper (already in `configuration.template.yaml`):

```yaml
input_text:
  media_playlist_name:
    name: "Playlist Name"
    initial: "playlist"        # ← the M3U filename without .m3u
    icon: mdi:playlist-music
```

Music Assistant matches this name against the M3U files in its configured playlist folder.

## Step 8 — Automate Playlist Regeneration (Optional)

Create an automation to regenerate the playlist periodically (e.g., every 10 minutes) so new files are picked up automatically:

```yaml
- id: sync_media_playlist
  alias: 'Media: Sync Playlist from NFS'
  description: Regenerates the M3U playlist from the NFS audio folder.
  triggers:
    - trigger: time_pattern
      minutes: "/10"
  conditions: []
  actions:
    - action: shell_command.create_playlist
  mode: single
```

## Step 9 — Play via Automation

Use Music Assistant's `play_media` action in your automations:

```yaml
- action: music_assistant.play_media
  target:
    entity_id: media_player.<your_speaker>
  data:
    media_id: "{{ states('input_text.media_playlist_name') }}"
    media_type: playlist
    enqueue: play
```

### Multi-room Transfer

Use `music_assistant.transfer_queue` to move playback between speakers:

```yaml
- action: music_assistant.transfer_queue
  target:
    entity_id: media_player.<target_speaker>
  data:
    source_player: media_player.<source_speaker>
    auto_play: true
```

## Customization

| Setting | Where | Notes |
|---------|-------|-------|
| Audio formats | `create_playlist.py` line 10 | Add/remove extensions in `AUDIO_EXTENSIONS` tuple |
| Playlist location | `shell_command` + script args | Change `/media/music/playlist.m3u` to any path |
| Sync interval | Automation `time_pattern` | Change `"/10"` to `"/5"`, `"/30"`, etc. |
| Playlist name | `input_text.media_playlist_name` | Must match the M3U filename (without `.m3u`) |
| NFS mount path | Mount command | Change `/media/music` to any local path |

## Troubleshooting

**Playlist is empty / 0 tracks:**
- Check the NFS mount is active: `mount | grep nfs`
- Verify files exist: `ls /media/music/*.mp3`
- Run the script manually and check output

**Music Assistant doesn't see the playlist:**
- Verify the Filesystem provider path matches where the M3U is written
- Check that `input_text.media_playlist_name` matches the M3U filename
- Restart Music Assistant after adding the provider

**`shell_command` fails:**
- Ensure `python_script:` is in `configuration.yaml`
- Check HA logs for the exact error
- Verify the script has no syntax errors: `python3 -c "import py_compile; py_compile.compile('/config/python_scripts/create_playlist.py')"`

**NFS mount drops after reboot:**
- Add to `/etc/fstab` with `_netdev` option
- Or use HA's built-in NFS mount configuration if available

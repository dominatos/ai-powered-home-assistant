"""
Scan a folder for audio files and generate an M3U playlist.

Called by shell_command from Home Assistant.
Usage: python3 create_playlist.py <audio_folder> <m3u_file>
"""
import os
import sys
import tempfile

AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus")

def _raise_walk_error(err):
    """Re-raise os.walk errors so unreadable directories abort the scan."""
    raise err

def main():
    """Generate an M3U playlist from the audio folder and output CLI arguments.

    Recursively scan supported audio extensions, ignoring case, and write
    sorted entries with paths relative to the playlist directory. Skip names
    or paths containing line breaks. Replace the output only after writing
    the complete UTF-8 playlist; its parent directory must already exist.

    Raise SystemExit(1) for missing arguments, an invalid source directory, or
    filesystem errors. Other exceptions propagate after temporary-file
    cleanup; cleanup errors themselves propagate as OSError.
    """
    if len(sys.argv) < 3:
        print("Usage: python3 create_playlist.py <audio_folder> <m3u_file>")
        sys.exit(1)

    audio_folder = sys.argv[1]
    m3u_file = sys.argv[2]

    if not os.path.isdir(audio_folder):
        print(f"Error: '{audio_folder}' is not a directory or does not exist.")
        sys.exit(1)

    count = 0
    dest_dir = os.path.dirname(m3u_file) or "."
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(dir=dest_dir, suffix=".m3u.tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            for root, dirs, files in os.walk(audio_folder, onerror=_raise_walk_error):
                dirs.sort(key=lambda name: name + os.sep)
                for filename in sorted(files):
                    if filename.lower().endswith(AUDIO_EXTENSIONS):
                        filepath = os.path.join(root, filename)
                        relative_path = os.path.relpath(filepath, dest_dir)
                        title = os.path.splitext(filename)[0]
                        if "\n" in title or "\r" in title or "\n" in relative_path or "\r" in relative_path:
                            print(f"WARNING: Skipping file with newline in name: {filename}", file=sys.stderr)
                            continue
                        f.write(f"#EXTINF:0,{title}\n")
                        f.write(f"{relative_path}\n\n")
                        count += 1
        os.replace(tmp_path, m3u_file)
    except OSError as exc:
        print(f"Error: Playlist generation failed: {exc}", file=sys.stderr)
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        sys.exit(1)
    except Exception:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"Playlist saved to {m3u_file} ({count} tracks)")

if __name__ == "__main__":
    main()

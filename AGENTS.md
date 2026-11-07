# slidegen – notes for AI agents

Python tooling for the Sunday livestream of the Mennonitengemeinde Basel-Holee. It started as a song slide generator and now also covers OBS song switching, CD recording/burning and sermon uploads. The README explains the song file format and every config key in detail; read the relevant part there instead of guessing.

Production runs on the livestreaming PC (Fedora Silverblue, inside the `python_venv` toolbox, **Python 3.13**). That PC is set up by the sibling repo `livestreaming-pc-infra` (see below). Most entry points are not run by hand but triggered by VulcanBoard touchscreen buttons via shell wrappers.

## Layout

- **Entry points (repo root)** are thin: `colorama.init()`, a `validate_*_config()` call from `input/`, then a call into a package. Keep them that way.
  - `slidegen.py` → renders slides for one song file (`SRC_PATH DEST_DIR PROMPT_INPUT`).
  - `ssync.py` → interactive wrapper: sync the song repo (rclone/Nextcloud), choose songs via fzf, generate slides into the OBS dirs, push them to OBS via WebSocket.
  - `next_song.py` / `previous_song.py` / `force_song.py`, `next_slide.py` / `previous_slide.py` → OBS scene/slide switching (`song_switcher/`).
  - `set_cd_marker.py` (starts the recording if none is running, otherwise sets a track marker), `stop_cd_recording.py`, `choose_cd_dialog.py` / `burn_cds_of_today.py` → CD recording and burning (`recording/`).
  - `cd_recording_status_websocket.py` → status server for the OBS dock (systemd unit on the PC).
  - `upload_sermon_of_today.py`, `choose_sermon_dialog.py`, `manually_upload_sermon_file.py` → sermon upload (`recording/sermon.py`).
  - `auto_print_infomail.py` → infomail printing (still Windows-only, `.bat`).
  - `check_song_files.py DIR [--fix-book OUTDIR]` → report on a folder of song files (what slidegen stops on, files without song number, numbers with several files, structures to check); changes nothing, `--fix-book` writes corrected copies elsewhere. Runs anywhere (only `song_files/`).
  - `export_song_index.py DIR` → JSON on stdout: per song number the files, verses and refrain. Used by the nightly job on the NAS (`website/deploy/folien-sync.sh`, clones this repo from GitHub to `/opt/slidegen`) for the intern area; keep it and `song_files/` standard-library only and compatible with Python 3.11 (NAS).
- **Packages:** `slides/` (rendering with Wand/ImageMagick; `slides/engine/`), `input/` (argv/file/prompt parsing, `validate_config.py`), `sync/`, `song_switcher/`, `song_structure/` (verse prompt → slide order with refrains, pure Python), `song_files/` (song number like `gm 37` from the `book:` line, index number → files, file checks; pure Python, shared with the planned automatic slides), `recording/`, `os_agnostic/` (all `sys.platform` branching lives here), `utils/`, `audio/`.
- `media/` → README images only. `template.txt` → song file template.

## Config

- `config/__init__.py` loads `constants.py`, then `default_config.py`, then the optional, gitignored `config/config.py`, all via star imports. Code uses it as `import config as const` → `const.SOME_KEY`.
- **New config key:** add a default to `config/default_config.py`, validate it in the matching `validate_*_config()` in `input/validate_config.py`, and document it in the README. If production needs a non-default value, it goes into `livestreaming-pc-infra`'s `roles/sw_setup/templates/slidegen_config.py.j2`.
- Directory values support `~` and `$VAR` via `utils.expand_dir`.
- **Renaming or removing a key** breaks the production config in `livestreaming-pc-infra`. Change both sides.

## Conventions

- Match the surrounding style: black-style formatting with lines ≤ 79 columns, type hints, `# pylint: disable=...` only where needed, `pyrightconfig.json` for type checking.
- Scripts run from VulcanBoard have no visible terminal. Report errors to the user through the PyQt5 dialogs (`utils.InfoMsgBox`, `gui_error_out=True`), not only through `log`/`warn`.
- Wrappers start the Qt scripts with `QT_QPA_PLATFORM=wayland`.
- State between button presses lives in small cache files (`NEXTSONG_CACHE_FILE`, `CD_RECORD_CACHEFILE`). The CD cache file has a fixed 6-line format checked in `recording/verify.py` (date, last marker, ffmpeg PID, start ms, last-track ms, CD number). Change the writer, the validator and all readers together.
- The CD recording records from the PipeWire source `studiolive_main_mix` (set via `CD_RECORD_FFMPEG_INPUT_ARGS` on the PC). Tracks shorter than `CD_RECORD_MIN_TRACK_MILIS` are prevented on purpose (audio CD limitation).
- Windows support (`requirements-win32.txt`, `os_agnostic/`) still exists in the code, but production is Linux. Don't remove it without asking.
- Tests: `python -m unittest discover tests` from the repo root (only the standard library). So far they cover `song_structure/` (verse prompt → slide order) and `song_files/`, which has no third-party imports on purpose; keep new pure logic like that so it stays testable without PyQt5/Wand. Slide rendering itself is not tested: run `slidegen.py` on a song file with a temporary `DEST_DIR`.

## Safety

- Don't run scripts with external side effects without asking: sermon upload (publishes to the website), CD burning, `ssync.py` (rclone sync against the Nextcloud song repo), OBS switching or CD recording against the live PC.
- `config/config.py` on the PC contains credentials (rendered from Ansible Vault). Never print it, never commit a `config/config.py`.

## Sibling repos

On the dev machine, the related repos are checked out next to this one in `~/dox/src/` (`../<name>/`).

| Sibling | Interface with this repo |
| :--- | :--- |
| `livestreaming-pc-infra` | Deploys this repo (from the `master` branch of the GitHub URL) into the toolbox and renders `config/config.py` from `slidegen_config.py.j2`. Its shell wrappers in `roles/sw_setup/files/scripts/` call the entry points above **by file name** and activate this repo's venv. It also contains `launch-ssync` and the systemd unit for `cd_recording_status_websocket.py`. |
| `obs-cd-rec-status` | OBS plugin that consumes the CD status WebSocket (`CD_RECORD_WEBSOCKET_PORT`, default 8765). The JSON keys `recording`, `cd`, `track`, `cd_time`, `track_time` are its contract. |
| `VulcanBoard` | Indirect: the buttons that trigger the wrappers. Button IDs/states live in `livestreaming-pc-infra`'s `config.yml`. |
| `technik-dokumentation` | Full technical documentation (German). Read its `AGENTS.md` (section map) first, then only the relevant sections of `home.md`, never the whole file. Most relevant: `## Script fürs Lieder einpflegen ausführen` (ssync usage), `### Die automatische CD-Aufnahme und Marker-Setzung`. |

Rules:

* When renaming or moving an entry point, changing its arguments or exit behavior, renaming config keys or changing the WebSocket JSON, check the other side and make the matching change, or explicitly say what needs to change there.
* Read siblings selectively (e.g. `grep -rn 'slidegen/' ../livestreaming-pc-infra/roles`), never whole repos.
* If a sibling is not checked out, say so instead of guessing its interface.

## Workflow

* **NEVER commit or push.** Leave all git history operations to the user.
* When a change is done, suggest a commit message following Conventional Commits,
  **unscoped** (`feat!: ...`, `feat: ...`, `fix: ...`, `chore: ...`, `doc: ...`, `refactor: ...`),
  lowercase, imperative, matching `git log`. If the change spans several repos, suggest
  one message per repo.

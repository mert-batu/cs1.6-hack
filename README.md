# CS 1.6 External Multi-Tool (Unified Runtime)

Refactored and unified Counter-Strike 1.6 external toolset running from a single entry point: [main.py](main.py).

This repository is designed for clean maintenance and practical usage:
- single runtime core
- safer memory access wrappers
- native config selection through system file explorer
- optional overlay thread for ESP and crosshair
- GitHub-ready project structure and docs

## Highlights

- Triggerbot v1
- Triggerbot v2 (offset + screen-space fallback)
- Bunnyhop
- Duck spam logic
- Aimbot (FOV, smooth, RCS, hold mode)
- ESP boxes (overlay)
- Crosshair overlay
- Live key toggles

## Architecture

Main runtime: [main.py](main.py)

Compatibility wrappers (all forward to main):
- [aimbot.py](aimbot.py)
- [esp.py](esp.py)
- [crosshair.py](crosshair.py)
- [esptest.py](esptest.py)

This prevents feature drift and cross-file conflicts.

## Compatibility

| Item | Status | Notes |
| :--- | :--- | :--- |
| OS | Windows | Tested on Windows environment |
| Python | 3.8+ | Recommended 3.11 |
| Game Process | hl.exe | Required by pymem attach |
| CS Branch | steam_legacy (recommended) | Pre-25th Anniversary branch is closest to expected offsets |
| Default New Branch | Not guaranteed | Offsets may differ after engine updates |

### Build Note: 8664 vs 8684

Current offset set is most likely aligned with the classic Steam legacy line commonly referenced as build 8684 in community sources.

If you were thinking 8664, that is very likely a typo in this context.

What is officially verifiable from Steam side:
- Valve provides a steam_legacy beta branch (pre-25th Anniversary behavior).
- Exact offset compatibility must always be verified at runtime because updates can shift memory layout.

Practical conclusion for this repository:
- If you want the highest chance of offset compatibility, use steam_legacy branch first.
- Community discussions around legacy offsets frequently reference build 8684 naming.
- Treat any exact build number as a compatibility hint, not a permanent guarantee.

## How to Verify Your Game Version

1. Open Steam.
2. Right-click Counter-Strike.
3. Properties -> Betas.
4. Select steam_legacy branch.
5. Launch the game.
6. Open in-game console and run: version
7. Compare runtime behavior. If features fail, offsets likely changed.

## Research References

- Steam community guide documenting branch switch to steam_legacy:
	https://steamcommunity.com/sharedfiles/filedetails/?id=3607645870
- Community index entries commonly labeled as Steam build 8684:
	https://archive.org/download/counter-strike-1.6-steam-build-8684

Note: Steam officially exposes branch selection; exact offset viability must always be tested on your local build.

## Install

1. Clone repository.
2. Install dependencies:

pip install -r requirements.txt

## Run

python main.py

When started, runtime asks for config mode:
- (1) default path
- (2) native TXT picker
- (3) native folder picker + custom filename

If selected config file is missing, it is auto-created with defaults.

## Configuration

Sample file: [log_1401202414458947.txt](log_1401202414458947.txt)

Sections:
- SETTINGS
- TRIGGERBOT SETTINGS
- KEYBINDS
- AIMBOT
- DUCK
- OVERLAY

The sample config now includes bilingual TR/EN comments for easier editing.

## Default Toggle Keys

- Triggerbot v1: h
- Triggerbot v2: j
- Bunnyhop: k
- Ducking: l
- Aimbot: u
- ESP: i
- Crosshair: o

## Dependencies

See [requirements.txt](requirements.txt).

Main packages:
- pymem
- keyboard
- mouse
- pywin32
- pygame
- PyQt5

## Release Docs

Prepared release notes draft:
- [RELEASE_NOTES_v2.0.0.md](RELEASE_NOTES_v2.0.0.md)

## Troubleshooting

Issue: hl.exe process not found
- Open CS 1.6 first.
- Ensure process name is hl.exe.

Issue: overlay does not appear
- Confirm pygame is installed.
- Check whether CS window is running in a mode compatible with topmost transparent overlays.

Issue: key toggles do not respond
- Run terminal/editor with sufficient privileges.
- Verify key names in config.

Issue: features stopped after game update
- Recheck branch (steam_legacy).
- Validate offsets for your current game build.

## Disclaimer

This repository is provided for educational and research purposes.

Using third-party game tools may violate platform or server rules and can result in penalties.
You are responsible for your own usage and outcomes.

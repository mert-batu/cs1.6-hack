# Release Notes - v2.0.0 Unified Runtime

## Summary

This release consolidates the project into a single runtime architecture and improves stability, configuration flow, and repository documentation.

## Major Changes

- Unified all main functionality under [main.py](main.py)
- Added native OS file picker and folder picker for config selection
- Introduced safer memory read/write wrappers and structured feature control
- Added threaded overlay rendering flow for ESP and crosshair
- Preserved compatibility via wrapper entry files:
  - [aimbot.py](aimbot.py)
  - [esp.py](esp.py)
  - [crosshair.py](crosshair.py)
  - [esptest.py](esptest.py)

## Configuration Improvements

- Expanded sample config: [log_1401202414458947.txt](log_1401202414458947.txt)
- Added bilingual TR/EN comments
- Added new settings groups and keys:
  - AIMBOT
  - DUCK
  - OVERLAY

## Documentation Improvements

- Rebuilt README for clearer project identity and usage flow: [README.md](README.md)
- Added detailed publishing guide in Turkish: [GITHUB_PUBLISH_GUIDE_TR.md](GITHUB_PUBLISH_GUIDE_TR.md)

## Compatibility Notes

- Primary target: Counter-Strike 1.6 legacy behavior with hl.exe process
- Recommended branch: steam_legacy (pre-25th Anniversary behavior)
- Offsets may differ on newer/default branch updates

## Upgrade Impact

- Existing users can continue launching old script names because they now forward to main runtime.
- No forced deletion of old entry files required.

## Known Limits

- Overlay requires pygame
- Runtime behavior depends on game build-offset compatibility

## Suggested Next Version (v2.1.0)

- Runtime offset profile switching per build
- In-app config validation and auto-repair
- Optional hot-reload for config changes

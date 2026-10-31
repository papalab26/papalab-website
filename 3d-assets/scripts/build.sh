#!/usr/bin/env bash
set -euo pipefail
asset_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$asset_root/.tools/environment.sh" ]; then bash "$asset_root/scripts/setup.sh"; fi
source "$asset_root/.tools/environment.sh"
"$BLENDER_BIN" --background --factory-startup --python-exit-code 1 --python "$asset_root/scripts/build_rifleman.py" "$@"
node "$asset_root/tests/validate_glb.mjs"

node "$asset_root/scripts/package_preview.mjs"

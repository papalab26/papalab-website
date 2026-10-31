#!/usr/bin/env bash
set -euo pipefail
asset_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
port="${PORT:-8765}"
echo "啟動獨立 3D 預覽，連接埠 $port；模型與 Three.js 均使用本地檔案。"
exec python3 -m http.server "$port" --bind 0.0.0.0 --directory "$asset_root"

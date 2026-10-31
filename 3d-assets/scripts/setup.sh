#!/usr/bin/env bash
# Papa-Lab 免費 3D 環境：使用已有 Blender，或下載官方 4.3.2 Linux 套件並驗證校驗碼。
set -euo pipefail
asset_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tools_dir="$asset_root/.tools"
mkdir -p "$tools_dir"
for program in python3 node npm; do
  command -v "$program" >/dev/null || { echo "缺少 $program，請先在雲端環境安裝。" >&2; exit 1; }
done
blender_bin="${BLENDER_BIN:-$(command -v blender || true)}"
if [ -n "$blender_bin" ]; then
  version_line="$($blender_bin --version | head -n 1)"
else
  version_line=""
fi
if [[ "$version_line" != Blender\ 4.3.* ]]; then
  case "$(uname -m)" in x86_64|amd64) ;; *) echo '官方備援腳本目前僅支援 Linux x64。' >&2; exit 1;; esac
  for program in curl tar sha256sum; do command -v "$program" >/dev/null; done
  archive='blender-4.3.2-linux-x64.tar.xz'
  release_url='https://download.blender.org/release/Blender4.3'
  blender_bin="$tools_dir/blender-4.3.2-linux-x64/blender"
  if [ ! -x "$blender_bin" ]; then
    curl --fail --location --retry 2 "$release_url/blender-4.3.2.sha256" -o "$tools_dir/checksums.txt"
    curl --fail --location --retry 2 "$release_url/$archive" -o "$tools_dir/$archive"
    python3 - "$tools_dir/checksums.txt" "$tools_dir/$archive" <<'PY'
import hashlib,sys
from pathlib import Path
checks=Path(sys.argv[1]).read_text().splitlines(); archive=Path(sys.argv[2])
matches=[line.split()[0] for line in checks if line.split() and line.split()[-1].lstrip('*')==archive.name]
if len(matches)!=1:raise SystemExit('找不到唯一的官方 SHA256 校驗碼。')
actual=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
if actual!=matches[0]:raise SystemExit('Blender 校驗失敗，拒絕解壓縮。')
print('官方 Blender 套件 SHA256 驗證通過。')
PY
    tar -xJf "$tools_dir/$archive" -C "$tools_dir"
  fi
fi
printf 'export BLENDER_BIN=%q\n' "$blender_bin" > "$tools_dir/environment.sh"
"$blender_bin" --background --factory-startup --python-exit-code 1 --python "$asset_root/scripts/smoke_test.py" -- "$tools_dir"
npm ci --ignore-scripts --no-audit --no-fund --cache "${TMPDIR:-/tmp}/papalab-npm-cache" --prefix "$asset_root"
node "$asset_root/scripts/vendor.mjs"
echo '3D 環境初始化成功；沒有付費服務或 API。'

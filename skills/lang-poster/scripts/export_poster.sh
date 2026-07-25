#!/bin/bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: export_poster.sh <html> [output.jpg] [width] [height] [scale]" >&2
  exit 2
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.*}.jpg}"
WIDTH="${3:-1080}"
HEIGHT="${4:-1440}"
SCALE="${5:-2}"

if [ ! -f "$INPUT" ]; then
  echo "ERROR: input HTML not found: $INPUT" >&2
  exit 2
fi
case "$WIDTH:$HEIGHT:$SCALE" in
  *[!0-9:]*|0:*|*:0:*|*:0) echo "ERROR: width, height and scale must be positive integers" >&2; exit 2 ;;
esac

INPUT_DIR="$(cd "$(dirname "$INPUT")" && pwd)"
INPUT_NAME="$(basename "$INPUT")"
if [[ "$OUTPUT" != /* ]]; then OUTPUT="$(pwd)/$OUTPUT"; fi

CHROME=""
for candidate in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "$(command -v google-chrome 2>/dev/null || true)" \
  "$(command -v chromium 2>/dev/null || true)" \
  "$(command -v chromium-browser 2>/dev/null || true)"; do
  if [ -n "$candidate" ] && [ -x "$candidate" ]; then CHROME="$candidate"; break; fi
done
if [ -z "$CHROME" ]; then
  echo "ERROR: Chrome or Chromium not found" >&2
  exit 2
fi

python3 -c 'from PIL import Image' 2>/dev/null || {
  echo "ERROR: Pillow is required: python3 -m pip install pillow" >&2
  exit 2
}

TEMP_DIR="$(mktemp -d)"
SERVER_PID=""
cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

cp "$INPUT_DIR/$INPUT_NAME" "$TEMP_DIR/poster.html"
PORT=$((18000 + RANDOM % 10000))
python3 -m http.server "$PORT" --directory "$TEMP_DIR" >/dev/null 2>&1 &
SERVER_PID=$!

for _ in 1 2 3 4 5; do
  if curl -fsS "http://127.0.0.1:$PORT/poster.html" >/dev/null 2>&1; then break; fi
  sleep 1
done

RAW="$TEMP_DIR/raw.png"
"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --screenshot="$RAW" --window-size="$WIDTH,$HEIGHT" \
  --force-device-scale-factor=1 "http://127.0.0.1:$PORT/poster.html" >/dev/null 2>&1

TARGET_W=$((WIDTH * SCALE))
TARGET_H=$((HEIGHT * SCALE))
python3 - "$RAW" "$OUTPUT" "$WIDTH" "$HEIGHT" "$TARGET_W" "$TARGET_H" <<'PY'
import sys
from PIL import Image

raw, output = sys.argv[1:3]
w, h, target_w, target_h = map(int, sys.argv[3:])
image = Image.open(raw).crop((0, 0, w, h))
if image.size != (target_w, target_h):
    image = image.resize((target_w, target_h), Image.Resampling.LANCZOS)
image.convert("RGB").save(output, "JPEG", quality=95)
print(f"OK: {output} {target_w}x{target_h}")
PY

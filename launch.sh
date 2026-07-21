#!/bin/bash
# Double-click (or run) this to put the Reyse Ops Console on screen.
# Run with --mock to watch it cycle through all five states on its own,
# with no voice-line running — good for showing it off standalone.
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE_FLAG=""
PORT=8777
if [ "${1:-}" == "--mock" ]; then
  MODE_FLAG="--mock"
  PORT=8778
fi
URL="http://127.0.0.1:$PORT"

if ! curl -s -o /dev/null "$URL/state"; then
  echo "Starting the local server..."
  LOG_DIR="$(mktemp -d /tmp/voice-visualizer-log-XXXXXX)"
  nohup python3 "$DIR/server.py" $MODE_FLAG > "$LOG_DIR/server.log" 2>&1 &
  for _ in $(seq 1 25); do
    curl -s -o /dev/null "$URL/state" && break
    sleep 0.2
  done
fi

PROFILE_DIR="$(mktemp -d /tmp/voice-visualizer-profile-XXXXXX)"

for BROWSER in google-chrome google-chrome-stable chromium-browser chromium; do
  if command -v "$BROWSER" >/dev/null 2>&1; then
    "$BROWSER" \
      --kiosk \
      --user-data-dir="$PROFILE_DIR" \
      --no-first-run \
      --noerrdialogs \
      --disable-session-crashed-bubble \
      "$URL" >/dev/null 2>&1 &
    exit 0
  fi
done

echo "No Chrome/Chromium found on this machine."
echo "Opening your default browser instead — once it's open, go fullscreen"
echo "with F11 (the same key most browsers use)."
xdg-open "$URL" 2>/dev/null || echo "Open this address by hand: $URL"

# Reyse Ops Console (voice-visualizer)

A fullscreen screen that reacts to the voice line — the "ON AIR" light for
`voice-line`. It doesn't do any listening or talking itself; it just watches
three small files `voice-line` writes and reacts on screen. Built to sit on
the same Chromebook as `voice-line`, since that's where those files live.

## Running it

You need `~/voice-line` and `~/voice-visualizer` (this folder) both cloned
onto the same machine, in your home folder, at those exact names.

- **With the voice line running:** `./launch.sh` — starts the local server
  if it's not already running, then opens the scene fullscreen.
- **On its own, no voice line needed:** `./launch.sh --mock` — cycles through
  all five looks automatically (idle, listening, thinking, speaking, alert)
  so you can enjoy it or show it off without anything else switched on.

Closing the fullscreen window the normal way leaves the server running in
the background, so opening `launch.sh` again is instant.

## What it's reacting to

`server.py` reads three files written by `voice-line` in `~/voice-line/`:

- `.voice_state` — which of the four states it's in (idle/listening/thinking/speaking)
- `.voice_waveform` — how loud it's currently speaking
- `.voice_alert` — whether something else on the machine needs attention

It never writes to any of them — strictly read-only, so it can't interfere
with the voice line itself.

## The five looks

- **idle** — the ops board ticking over quietly
- **listening** — a ring pulses inward toward the centre, reading as "taking something in"
- **thinking** — the network speeds up and a radar-style sweep passes through, reading as "working on it"
- **speaking** — the centre R mark is the star: it breathes with your actual voice level, live
- **alert** — an unmistakable red bleed across the whole screen, independent of whatever else is happening

## Trying it without touching the real voice line

- `./launch.sh --mock` — full automatic loop through all five states
- Add `?mockstate=speaking` (or any state name) to the address bar to freeze
  the page on one look, simulated locally, without touching the server at all
- Add `?shot=speaking&t=1200` to render one exact frame 1200ms into that
  state and stop there — this is the self-check hook used to verify each
  look during building, not something you'll normally need

## Swapping the look later

Everything on screen is drawn from code, no image files — so there's nothing
to swap by default. If you ever want a real photo or logo file worked in
instead of the drawn R mark, that's a small separate change, just ask.

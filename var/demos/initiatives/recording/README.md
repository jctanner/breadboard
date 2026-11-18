# Recording the Initiatives demo as a video

This directory records the [Initiatives demo](../demo-script.md) as a captioned,
narrated video. The first recording was made on 2026-11-18 against the w530
stack. It follows one Initiative from opt-in, through autofix, a strategy, human
sign-off and decomposition, to its Epics. Everything shown is a real run of the
production pipeline definitions against the emulators. Waits for agents are
fast-forwarded; nothing is mocked or re-enacted.

| File | Purpose |
| --- | --- |
| `record.mjs` | Drives the demo and records it: browser, captions, pipeline steps and encoding |
| `clips.mjs` | Films extra shots after a run, from the run's end state |
| `narrate.py` | Adds spoken narration, using Kokoro text-to-speech offline |

Videos, frames and the speech model are large, so they stay out of git. Keep
them under `~/.cache/initiative-video/`.

## How it works

```text
  this machine                                  stack host (w530)
  ────────────                                  ─────────────────
  record.mjs ──── headless Chrome ──HTTPS──▶ Jira and GitLab emulator UIs
      │              │ CDP screencast frames
      │              ▼
      │         frames/*.jpg + timestamps
      │
      └──── ssh ──▶ scripts/demo.py optin|autofix|live|signoff|decompose
                     (the same commands as the demo script; model calls go
                      through Model Relay on the stack)
```

- **The browser is a viewer only.** Chrome runs on the recording machine and
  opens the emulator UIs. Each state change is made with
  [`demo.py`](../scripts/demo.py) over SSH: labels through the Jira API, and
  pipeline runs through the GitLab API. Labels aren't set through the Jira edit
  form because saving that form converts the description's line endings to
  CRLF, which changes the text the agents read. The command and its output
  appear in a terminal card at the top right, so viewers can see what was run.
- **Frames come from the Chrome DevTools Protocol (CDP).** `record.mjs` uses
  `Page.startScreencast`, which delivers a JPEG each time the page changes,
  with a timestamp. It doesn't use Playwright's `recordVideo` because that
  needs Playwright's bundled ffmpeg. The system ffmpeg does all the encoding.
- **Overlays are injected into the page.** The caption bar, the terminal card
  and the fast-forward badge are DOM elements added to the top of the page.
  They are redrawn after every navigation, and the screencast captures them
  with the page.
- **Fast-forwarding happens at encoding time.** Each time the playback speed
  changes, `record.mjs` adds the time and the new speed to a list of segments:
  1× by default, and 15× (`FF`) while a job log is tailing. At encoding time,
  each frame's on-screen duration is the real gap to the next frame divided by
  the speed at that moment. The result is written as an ffmpeg concat list
  (`concat.txt`) and encoded with libx264 at 30 fps. The fast-forward badge
  shows the real elapsed time, so viewers can see how long each agent took.
- **Job logs follow themselves.** The GitLab emulator's job page polls the log
  and stays at the bottom when it is scrolled there. The recorder scrolls to
  the bottom, then checks the job status over the API every 20 s.
- **Everything is logged.** `events.log` records each caption, navigation,
  remote output line and job result with a timestamp. Narration timing and
  splicing are both worked out from it.

## Prerequisites

On the stack host:

- The demo already works: `scripts/demo.py board` runs from the demo directory
  with `BREADBOARD_DOMAIN` and `BREADBOARD_CA_FILE` set
  (see [the demo's README](../README.md)).
- Jira is reset to the baseline: `demo.py reset`.
- The Model Relay credentials for the demo project are set up. That is a human
  task.

On the recording machine:

- SSH access to the stack host, with the host key already in `known_hosts`.
  The scripts use `StrictHostKeyChecking=yes` and `BatchMode=yes`.
- Google Chrome, Node.js with Playwright, and ffmpeg with libx264. If
  Playwright isn't installed in this directory, set `PW_MODULE` to its
  `index.mjs`.
- The machine doesn't need DNS for the stack's domain. Chrome is started with
  `--host-resolver-rules=MAP *.<domain> <STACK_IP>`. TLS errors are ignored for
  the emulator certificates.
- For narration, Kokoro in a virtualenv. It runs on the CPU, and nothing is
  sent to an outside service:

  ```bash
  mkdir -p ~/.cache/initiative-video/tts && cd ~/.cache/initiative-video/tts
  uv venv --python python3 .venv
  uv pip install --python .venv/bin/python kokoro-onnx soundfile
  for f in kokoro-v1.0.onnx voices-v1.0.bin; do
    curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f
  done
  ```

## Recording

```bash
export STACK_IP=<stack host address> STACK_SSH=<user>@<stack host>
export BREADBOARD_DOMAIN=w530.local
mkdir -p ~/.cache/initiative-video && cd ~/.cache/initiative-video
R=<repo>/var/demos/initiatives/recording

DRY=1 node $R/record.mjs   # rehearsal: no model calls, a few minutes
node $R/record.mjs         # the real thing: about an hour, about $16 through Model Relay
```

- **Dry run.** `DRY=1` films the same shots, but it doesn't change any labels.
  Instead of starting pipelines, it replays the logs of jobs that have already
  finished (`REPLAY` in `record.mjs`). Use it to check framing, captions and
  timing before spending money. Shots of results won't appear, because Jira is
  at the baseline.
- **Live run.** Opts in `OPTIN` (default `RHAISTRAT-75016`), plays the autofix
  schedule with `--limit 3`, then runs the strategy for `KEY` (default
  `RHAISTRAT-75028`), signs it off and decomposes it. The run stops with a
  "Stopped" card if any job fails.
- **Output.** `run-<timestamp>/demo.mp4`, plus `frames/`, `frames.txt`,
  `events.log` and `concat.txt`.
- **Reset afterwards.** Take a Jira snapshot of the end state, so shots can be
  filmed again later, then run `demo.py reset`:

  ```bash
  curl --cacert $BREADBOARD_CA_FILE -u admin:admin -X POST \
    -H 'Content-Type: application/json' -d '{"label": "cc75-video-end"}' \
    https://jira.$BREADBOARD_DOMAIN/api/admin/snapshots
  ```

`KEY` has to be an Initiative that is already opted in and has passed autofix
(`initiative-autofix-rubric-pass`), because the strategy stage is meant to
follow a passing autofix. In the baseline, 75028 is one. Picking a ticket that is ready
means a failed autofix can't stall the recording an hour in. As a result, the
video follows two tickets: autofix works on the newly opted-in Initiative,
while strategy and decomposition work on `KEY`. The narration should say so.
To follow one ticket the whole way, set `KEY` and `OPTIN` to the same Initiative.
If autofix doesn't pass it, the recording has nothing to show a strategy for.

Costs from the 2026-11-18 recording:

| Stage | Job | Real time | Model cost |
| --- | --- | --- | --- |
| Autofix | rfe-autofixer 405 | 14 min | $2.97 |
| Strategy | strat-pipeline 415 | 26 min | $8.31 |
| Decompose | epic-decomposer 423 | 17 min | $4.62 |
| **Total** | | about 60 min | **$15.90** |

## Filming extra shots afterwards

If a shot is missed or needs filming again, restore the end-state snapshot
and film it again at 1× with `clips.mjs`. This needs no model calls.

```bash
curl --cacert $BREADBOARD_CA_FILE -u admin:admin -X POST \
  https://jira.$BREADBOARD_DOMAIN/api/admin/snapshots/<snapshot file>/restore
node $R/clips.mjs run-<timestamp>   # writes clip-S.mp4 (strategy, review), clip-E.mp4 (Epics, results)
# ...splice them in (below), then run: demo.py reset
```

Then cut the clips into the main video, using `events.log` to find the cut
points. In the 2026-11-18 recording, the live take missed three shots: the
strategy document, the Epics list and an opened Epic. The causes are described
in the next section. The final video was spliced together like this:

```bash
ffmpeg -i demo.mp4 -i clip-S.mp4 -i clip-E.mp4 -filter_complex "
  [0:v]trim=0:264.07,setpts=PTS-STARTPTS[a];
  [1:v]setpts=PTS-STARTPTS[s];
  [0:v]trim=276.302:374.566,setpts=PTS-STARTPTS[b];
  [2:v]setpts=PTS-STARTPTS[e];
  [0:v]trim=start=395.8,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=3[c];
  [a][s][b][e][c]concat=n=5:v=1:a=0[v]" \
  -map '[v]' -c:v libx264 -crf 23 -pix_fmt yuv420p -movflags +faststart initiative-demo.mp4
```

`record.mjs` has since been fixed, so a new recording should capture all of
these shots live, and `clips.mjs` should only be needed for repairs.

## Narration

```bash
~/.cache/initiative-video/tts/.venv/bin/python $R/narrate.py \
  run-<timestamp>/initiative-demo.mp4 run-<timestamp>/initiative-demo-narrated.mp4 [voice] [speed]
```

The narration is the list of `(seconds, text)` pairs in `LINES` in
`narrate.py`. Each line is spoken in Kokoro's voice (default `af_heart`, speed
1.05). It starts at its scene's time, or 0.5 s after the previous line ends if
that one runs over. The lines are mixed into one track, loudness-normalised
(`loudnorm`, −16 LUFS) and muxed into the video. The video stream is copied
unchanged unless the narration runs past the end; then the last frame is held
until it finishes. A re-render takes about a minute. The script prints each
line's start, length and lateness, so it's easy to see when a line is too long
for its scene.

The `LINES` timings match the 2026-11-18 video, and **a new recording needs new
times**. To get the scene times, map each `events.log` timestamp to video time.
Find the frame in `frames.txt` that was showing at that moment, add up the
`concat.txt` durations up to that frame, and add the part of that frame's
duration that had already passed. Then shift the times for any splices.

Writing narration that sounds right:

- Spell out anything that would be read badly: "W five-thirty", "R F E",
  "C I", and issue numbers as "seventy-five oh twenty-eight".
- Keep lines to about 2.3 words a second of the scene they cover. The
  fast-forwarded log sections have room for longer explanations.
- Narrate why something happens, not only what. The captions already say what
  is on screen.
- Check every number against the run: jobs, costs, Epic counts and review
  scores.

Other voices include `am_michael` (US male) and `bf_emma` (UK female). Kokoro
ships about 50.

## Lessons from the first recording

- **Jira emulator links.** Child issues link to `/issue/<KEY>`, not
  `/browse/<KEY>`. An attachment's filename link downloads the file; the row's
  **View** button (`/attachment/<id>/view`) renders it inline.
- **Smooth scrolling.** A smooth `scrollIntoView` is cancelled by the next
  wheel event. Jump to a heading with `window.scrollTo`, then use wheel events
  for visible scrolling.
- **Navigation races.** A "navigation interrupted" message in `events.log`
  means a later `go()` replaced an earlier one, for example the pipeline page
  followed straight away by the job page. It's harmless.
- **Node can't reach the stack's domain.** Node's HTTP stack doesn't use
  Chrome's resolver rule. API calls for job status and labels go through
  `curl` on the stack host, over SSH.
- **Data.** The Initiatives are synthetic (see [`catalogue.yaml`](../catalogue.yaml)).
  Don't record against real Jira content.

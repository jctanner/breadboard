"""Narrate initiative-demo.mp4 with Kokoro.  narrate.py VIDEO OUT [VOICE] [SPEED]
Each line starts at its scene time, or just after the previous line ends if that runs over."""
import subprocess, sys, os, json
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
TTS = os.environ.get("KOKORO_DIR", os.path.expanduser("~/.cache/initiative-video/tts"))  # kokoro-v1.0.onnx, voices-v1.0.bin
VIDEO, OUT = sys.argv[1], sys.argv[2]
VOICE = sys.argv[3] if len(sys.argv) > 3 else "af_heart"
SPEED = float(sys.argv[4]) if len(sys.argv) > 4 else 1.05
GAP = 0.5

LINES = [
    (0.5,   "This is one Initiative's journey, from idea to Epics, on the W five-thirty test lab."),
    (6.5,   "Here's the board: synthetic Initiatives in an emulated Jira. The text is invented, but the shapes match real ones."),
    (15.5,  "We'll follow Initiative seventy-five oh twenty-eight. It was opted in and passed autofix earlier, so it's ready for a strategy."),
    (25.8,  "Automation only touches Initiatives that a person has opted in. A small demo script adds the opt-in label, just as someone would in Jira."),
    (40.8,  "Next, the R F E autofixer. In production it runs on a timer. Here we start its schedule by hand, and it picks up opted-in Initiatives that are new, or have changed."),
    (60.0,  "Now the agent is working. This is its live log, sped up fifteen times. It reads each Initiative, checks it against the quality rubric, and fixes what it can."),
    (90.0,  "Every model call goes through the Model Relay, so no real model keys ever sit in C I."),
    (119.0, "The job passed. Autofix handled three Initiatives, including the one we just opted in, and recorded each result as a label."),
    (133.5, "Here are two of them, with their new labels."),
    (146.4, "Back to seventy-five oh twenty-eight, which passed autofix earlier. The strategy pipeline now runs live for it, from its main branch."),
    (156.0, "Strat creator drafts the strategy: the technical approach, the components, phasing, and risks. Then a separate reviewer scores it against a rubric."),
    (200.0, "This step takes about twenty-five minutes of real time, and around eight dollars of model use."),
    (261.3, "Done. The strategy and its review are now attached to the ticket."),
    (271.5, "This is the strategy itself. The requirements it covers trace back to the Initiative."),
    (288.5, "And the independent review. It approved the strategy, scoring seven out of eight."),
    (301.5, "Now the one manual gate. A person reads the strategy and signs it off. Again, the script adds the label a human would."),
    (311.0, "Once it's signed off, the epic decomposer takes over, and splits the Initiative into Epics."),
    (325.0, "It plans the Epics from the approved strategy, has the plan reviewed, and then creates them in Jira."),
    (360.0, "About seventeen minutes of real time, and under five dollars."),
    (396.8, "Ten new Epics, each one a child of the Initiative."),
    (413.3, "Each Epic has its own scope, acceptance criteria, and dependencies, written from the strategy."),
    (429.0, "And every run leaves a record in its results repository."),
    (433.0, "Same jobs, same labels, same gates as production, on synthetic data. About an hour end to end, and roughly sixteen dollars of model use."),
]

k = Kokoro(os.path.join(TTS, "kokoro-v1.0.onnx"), os.path.join(TTS, "voices-v1.0.bin"))
vlen = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VIDEO]))
SR = 24000
clips, t_free, plan = [], 0.0, []
for want, text in LINES:
    s, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
    assert sr == SR
    start = max(want, t_free)
    clips.append((start, s)); t_free = start + len(s) / SR + GAP
    plan.append({"want": want, "start": round(start, 2), "dur": round(len(s) / SR, 2), "late": round(start - want, 2), "text": text})
total = max(vlen, t_free + 1.0)
track = np.zeros(int(total * SR) + SR, dtype=np.float32)
for start, s in clips:
    i = int(start * SR); track[i:i + len(s)] += s
sf.write(OUT + ".wav", track, SR)
json.dump(plan, open(OUT + ".plan.json", "w"), indent=1)
for p in plan:
    print(f"{p['start']:7.2f} +{p['dur']:5.2f} late {p['late']:5.2f}  {p['text'][:70]}")
hold = total - vlen
print(f"video {vlen:.1f}s, narration ends {t_free:.1f}s, hold last frame {max(0, hold):.1f}s")
vf = ["-c:v", "copy"] if hold <= 0 else ["-vf", f"tpad=stop_mode=clone:stop_duration={hold:.2f}", "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p"]
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-i", OUT + ".wav", *vf,
                       "-af", "loudnorm=I=-16:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest", OUT])
print("wrote", OUT)

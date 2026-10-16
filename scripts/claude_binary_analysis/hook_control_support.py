"""Observe actual native hook payloads in isolated, credential-free controls."""
import json
import shlex


def observed_settings(output, settings):
    probe = output / "observe_hook.py"
    events = output / "observed-hooks.jsonl"
    probe.write_text(
        "import json,sys\n"
        "from pathlib import Path\n"
        "event=json.load(sys.stdin)\n"
        f"with Path({str(events)!r}).open('a') as stream:\n"
        "    stream.write(json.dumps(event)+'\\n')\n")
    settings = dict(settings)
    settings["hooks"] = {
        event: [{"matcher": matcher, "hooks": [{"type": "command",
            "command": "python3 " + shlex.quote(str(probe)), "timeout": 5,
            "onFailure": "block"}]}]
        for event, matcher in [("PreToolUse", "^(Workflow|StructuredOutput)$"),
                               ("PostToolUse", "Skill"), ("SubagentStop", ".*")]
    }
    return settings

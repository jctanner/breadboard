import json
import sys

# Reads JSON from stdin (sent by script_exec stdin) and reports its size.
data = json.load(sys.stdin)
print(json.dumps({"items": len(data), "bytes": len(json.dumps(data))}))

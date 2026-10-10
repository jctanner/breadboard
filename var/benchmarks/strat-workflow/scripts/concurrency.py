#!/usr/bin/env python3
# Per job: wall time, time with >=1 model call in flight, call-seconds (integral of calls in
# flight), average concurrency while busy, and a per-minute profile of calls in flight.
# Requests and responses can't be paired, but +1 per request file and -1 per response file
# (by mtime) gives the number in flight at every moment. Run inside the dashboard pod.
import glob, os, sys, json
for job in sys.argv[1:]:
    ev = sorted((os.path.getmtime(f), 1 if f.endswith(".request.json") else -1)
                for f in glob.glob(f"/app/artifacts/apibodies/{job}/*.json"))
    job_info = json.load(open(f"/app/artifacts/jobs/{job}.json")) if os.path.exists(f"/app/artifacts/jobs/{job}.json") else {}
    t0, t1 = ev[0][0], ev[-1][0]
    inflight = 0; busy = 0.0; callsec = 0.0; prev = t0; peak = 0
    minutes = {}
    for t, d in ev:
        if inflight > 0:
            busy += t - prev; callsec += inflight * (t - prev)
            # spread over minute buckets
            a = prev
            while a < t:
                m = int((a - t0) // 60); edge = t0 + (m + 1) * 60; b = min(t, edge)
                minutes[m] = minutes.get(m, 0) + inflight * (b - a); a = b
        inflight = max(0, inflight + d); peak = max(peak, inflight); prev = t
    span = t1 - t0
    prof = " ".join(f"{minutes.get(m, 0)/60:.1f}" for m in range(int(span // 60) + 1))
    print(f"{job[:60]:60} span {span/60:5.1f}m  busy {busy/60:5.1f}m  call-min {callsec/60:5.1f}  "
          f"avg concurrency {callsec/busy if busy else 0:4.2f}  peak {peak}")
    print(f"{'':60} calls in flight per minute: {prof}")

"""Converge emulator runner registrations; executed inside the emulator pod.

Only reconcile prints a token (captured privately by the deployment script).
All other diagnostics deliberately contain IDs/counts, never credentials.
"""

import argparse
import sys
import time

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["drain", "reconcile", "resume", "reset"])
    parser.add_argument("--name", default="glemu-k8s-runner")
    parser.add_argument("--tags", default="k8s-incluster,aipcc-small-x86_64")
    parser.add_argument("--run-untagged", choices=["true", "false"], default="false")
    parser.add_argument("--registration-token", default="runner-registration-token")
    parser.add_argument("--drain-timeout", type=int, default=180)
    args = parser.parse_args()
    with httpx.Client(base_url="http://127.0.0.1:8000/api/v4", timeout=30) as client:
        def api(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            # Do not include response/request bodies in errors: they can carry tokens.
            if not response.is_success:
                raise RuntimeError(f"{method} {path}: HTTP {response.status_code}")
            return response.json() if response.content else None

        def pages(path):
            items = []
            page = 1
            while True:
                batch = api("GET", path, params={"page": page, "per_page": 100})
                items.extend(batch)
                if len(batch) < 100:
                    return items
                page += 1

        def update(runner, paused):
            detail = api("GET", f'/runners/{runner["id"]}')
            return api("POST", "/runners", json={
                "token": detail["token"],
                "description": runner["description"],
                "tag_list": ",".join(runner["tag_list"]),
                "run_untagged": runner["run_untagged"],
                "locked": runner["locked"],
                "paused": paused,
            })

        runners = pages("/runners")
        if args.mode == "drain":
            for runner in runners:
                update(runner, True)
            deadline = time.monotonic() + args.drain_timeout
            while True:
                active = [job["id"] for runner in runners
                          for job in pages(f'/runners/{runner["id"]}/jobs')
                          if job["status"] in {"running", "canceling"}]
                if not active:
                    print(f"Drained {len(runners)} runner registration(s)")
                    return
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Drain timed out; active jobs {active}; runners remain paused")
                print(f"Waiting for active jobs {active}", file=sys.stderr, flush=True)
                time.sleep(3)

        # Mutations after drain require every registration to remain paused and idle.
        if args.mode in {"reconcile", "reset"}:
            for runner in runners:
                if not runner["paused"] or any(
                    job["status"] in {"running", "canceling"}
                    for job in pages(f'/runners/{runner["id"]}/jobs')
                ):
                    raise RuntimeError("Pause and drain all runners before reconciliation/reset")
            keep = next((r for r in runners if r["description"] == args.name), None)
            for runner in runners:
                if args.mode == "reset" or runner != keep:
                    token = api("GET", f'/runners/{runner["id"]}')["token"]
                    api("DELETE", "/runners", json={"token": token})
            if args.mode == "reset":
                if pages("/runners"):
                    raise RuntimeError("Runner registry did not reset")
                print("Runner registry reset; projects and job history preserved")
                return
            token = (api("GET", f'/runners/{keep["id"]}')["token"]
                     if keep else args.registration_token)
            result = api("POST", "/runners", json={
                "token": token, "description": args.name,
                "tag_list": args.tags, "run_untagged": args.run_untagged == "true",
                "locked": False, "paused": True,
            })
            if len(pages("/runners")) != 1:
                raise RuntimeError("Expected exactly one reconciled runner")
            print(result["token"])
            return

        if len(runners) != 1 or runners[0]["description"] != args.name:
            raise RuntimeError("Expected exactly one maintained runner before resuming")
        update(runners[0], False)
        print(f'Resumed maintained runner {runners[0]["id"]}')


if __name__ == "__main__":
    main()

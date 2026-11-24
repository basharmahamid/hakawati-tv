#!/usr/bin/env python3
"""Mark an agent as running / finished in status.json so the TV page can show it.

Usage (from a clone of this repo):
    python3 scripts/status.py start <trigger_id>
    python3 scripts/status.py done  <trigger_id> [failed]
Only this agent's own entry is touched. Safe to call when the push fails: it never raises.
"""
import datetime, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "status.json")


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("start", "done"):
        print(__doc__)
        return
    action, trig = sys.argv[1], sys.argv[2]
    failed = len(sys.argv) > 3 and sys.argv[3] == "failed"
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for attempt in range(4):
        git("fetch", "--depth=1", "origin", "main")
        git("reset", "--hard", "origin/main")
        try:
            doc = json.load(open(PATH, encoding="utf-8"))
        except Exception:
            doc = {}
        rows = [r for r in doc.get("data", []) if isinstance(r, dict) and r.get("id")]
        row = next((r for r in rows if r["id"] == trig), None)
        if row is None:
            row = {"id": trig, "enabled": True}
            rows.append(row)
        if action == "start":
            row["last_run"] = {"status": "RUNNING", "fired_at": now}
        else:
            lr = row.get("last_run") or {"fired_at": now}
            lr["status"] = "FAILED" if failed else "SUCCEEDED"
            lr["finished_at"] = now
            row["last_run"] = lr
        doc = {"updated_at": now, "data": rows}
        json.dump(doc, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        git("add", "status.json")
        git("-c", "user.name=hakawati-agent", "-c", "user.email=noreply@anthropic.com",
            "commit", "-m", f"status: {action} {trig}")
        if git("push", "origin", "HEAD:main").returncode == 0:
            print("status updated:", action, trig)
            return
    print("status update skipped (push failed)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never break the agent's real work
        print("status update skipped:", e)

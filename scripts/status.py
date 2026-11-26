#!/usr/bin/env python3
"""Mark an agent as running / finished in status.json so the TV page can show it.

Usage (from a clone of this repo):
    python3 scripts/status.py start <agent key>
    python3 scripts/status.py done  <agent key> [failed]
    python3 scripts/status.py link  <from key> <to key>   # a line lights up between two desks
Agent keys (fixed, also if a task is re-created): viki producer distributor community
analyst scout researcher toolscout meeting-daily meeting-weekly
Link keys are desk names: maestro viki scout producer packaging guardian distributor community
analyst researcher toolscout. A link stores the two names and the time only (this repo is public).
Only this agent's own entry is touched. Safe to call when the push fails: it never raises.
"""
import datetime, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "status.json")
DESKS = ("maestro viki scout producer packaging guardian distributor community "
         "analyst researcher toolscout").split()
MAX_LINKS = 30


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("start", "done", "link") or (sys.argv[1] == "link" and len(sys.argv) < 4):
        print(__doc__)
        return
    action, trig = sys.argv[1], sys.argv[2]
    failed = action != "link" and len(sys.argv) > 3 and sys.argv[3] == "failed"
    if action == "link":
        a, b = sys.argv[2], sys.argv[3]
        if a not in DESKS or b not in DESKS or a == b:
            print("status update skipped: link needs two different desk names:", " ".join(DESKS))
            return
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    last = ""
    for attempt in range(4):
        git("fetch", "--depth=1", "origin", "main")
        git("reset", "--hard", "origin/main")
        try:
            doc = json.load(open(PATH, encoding="utf-8"))
        except Exception:
            doc = {}
        rows = [r for r in doc.get("data", []) if isinstance(r, dict) and r.get("id")]
        links = [l for l in doc.get("links", []) if isinstance(l, dict)][-(MAX_LINKS - 1):]
        row = next((r for r in rows if r["id"] == trig), None)
        if action == "link":
            links.append({"from": sys.argv[2], "to": sys.argv[3], "at": now})
        elif row is None:
            row = {"id": trig, "enabled": True}
            rows.append(row)
        if action == "link":
            pass
        elif action == "start":
            row["last_run"] = {"status": "RUNNING", "fired_at": now}
        else:
            lr = row.get("last_run") or {"fired_at": now}
            lr["status"] = "FAILED" if failed else "SUCCEEDED"
            lr["finished_at"] = now
            row["last_run"] = lr
        doc = {"updated_at": doc.get("updated_at", now) if action == "link" else now, "data": rows, "links": links}
        json.dump(doc, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        git("add", "status.json")
        git("-c", "user.name=hakawati-agent", "-c", "user.email=noreply@anthropic.com",
            "commit", "-m", f"status: {action} {trig}" + (f" {sys.argv[3]}" if action == "link" else ""))
        r = git("push", "origin", "HEAD:main")
        if r.returncode == 0:
            print("status updated:", action, trig, sys.argv[3] if action == "link" else "")
            return
        last = (r.stderr or r.stdout or "").strip()[-400:]
    print("status update skipped (push failed):", last)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never break the agent's real work
        print("status update skipped:", e)

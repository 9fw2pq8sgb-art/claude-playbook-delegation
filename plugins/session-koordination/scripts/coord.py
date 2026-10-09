#!/usr/bin/env python3
"""Hook-Skript fuer das Plugin session-koordination (nur Standardbibliothek)."""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

DEFAULT_RESOURCES = {
    "blender": {
        "command": "(?i)(^|[\\s;&|(/'\"])blender(\\s|$|['\"])",
        "process": "(?i)(^|/)blender(\\s.*)?\\s(-b|--background)(\\s|$)",
        "mcp": "(?i)^mcp__.*blender",
    }
}
CLAIM_TTL = 90
MAX_LIST = 10


def home():
    return os.environ.get("COORD_HOME") or os.path.expanduser("~/.claude/coord")


def sub(name):
    p = os.path.join(home(), name)
    os.makedirs(p, exist_ok=True)
    return p


def run_ps(args):
    try:
        return subprocess.run(["ps"] + args, capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""


def ancestors(pid):
    out = []
    for _ in range(15):
        if pid <= 1:
            break
        line = run_ps(["-o", "ppid=,comm=", "-p", str(pid)]).strip()
        if not line:
            break
        parts = line.split(None, 1)
        try:
            ppid = int(parts[0])
        except (ValueError, IndexError):
            break
        comm = parts[1] if len(parts) > 1 else ""
        out.append((ppid, comm))
        pid = ppid
    return out


def self_claude_pid():
    env = os.environ.get("COORD_SELF_PID")
    if env:
        try:
            return int(env)
        except ValueError:
            pass
    for pid, comm in ancestors(os.getpid()):
        if os.path.basename(comm.strip()) == "claude":
            return pid
    return os.getppid()


def alive(pid):
    try:
        os.kill(int(pid), 0)
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError):
        return False
    return True


def processes():
    skip = {os.getpid()} | {p for p, _ in ancestors(os.getpid())}
    res = []
    for line in run_ps(["-axo", "pid=,command="]).splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        if pid not in skip:
            res.append((pid, parts[1]))
    return res


def load_resources():
    try:
        with open(os.path.join(home(), "config.json")) as f:
            r = json.load(f).get("resources")
        if isinstance(r, dict) and r:
            return r
    except Exception:
        pass
    return DEFAULT_RESOURCES


def write_json(path, data):
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def load_sessions(cleanup=False):
    d = sub("sessions")
    res = []
    for fn in os.listdir(d):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(d, fn)
        s = read_json(p)
        if not isinstance(s, dict):
            continue
        if alive(s.get("pid")):
            res.append(s)
        elif cleanup:
            try:
                os.remove(p)
            except OSError:
                pass
    return res


def lstart(pid):
    return run_ps(["-o", "lstart=", "-p", str(pid)]).strip()


def hhmm(pid):
    s = lstart(pid)
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %Y").strftime("%H:%M")
    except ValueError:
        return s


def owner_of(pid, sessions):
    chain = [pid] + [p for p, _ in ancestors(pid)]
    for s in sessions:
        if s.get("pid") in chain:
            return s.get("name")
    return None


def busy_processes(name, rcfg, sessions):
    rx = re.compile(rcfg["process"])
    return [(p, c) for p, c in processes() if rx.search(c)]


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))


def on_start(data, sid):
    cwd = data.get("cwd") or os.getcwd()
    sdir = sub("sessions")
    write_json(os.path.join(sdir, sid + ".json"), {
        "session_id": sid, "cwd": cwd, "name": os.path.basename(cwd.rstrip("/")) or cwd,
        "pid": self_claude_pid(), "started": datetime.now().isoformat(timespec="seconds")})
    sessions = load_sessions(cleanup=True)
    others = [s for s in sessions if s.get("session_id") != sid]
    parts = []
    if others:
        lst = ", ".join("%s (%s)" % (s.get("name"), s.get("cwd")) for s in others[:MAX_LIST])
        if len(others) > MAX_LIST:
            lst += ", ... (+%d weitere)" % (len(others) - MAX_LIST)
        parts.append("Andere aktive Claude-Code-Sessions auf diesem Rechner: %s." % lst)
    busy = []
    for name, rcfg in load_resources().items():
        for pid, _ in busy_processes(name, rcfg, sessions):
            who = owner_of(pid, sessions)
            who = "Session %s" % who if who else "außerhalb von Claude gestartet"
            busy.append("%s PID %d (%s) seit %s" % (name.capitalize(), pid, who, hhmm(pid) or "unbekannt"))
    if busy:
        parts.append("Belegt: %s. Diese Ressource erst nach dem Ende des Prozesses starten." % "; ".join(busy))
    if parts:
        emit({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                     "additionalContext": " ".join(parts)}})


def on_end(data, sid):
    try:
        os.remove(os.path.join(sub("sessions"), sid + ".json"))
    except OSError:
        pass
    cdir = sub("claims")
    for fn in os.listdir(cdir):
        p = os.path.join(cdir, fn)
        c = read_json(p)
        if isinstance(c, dict) and c.get("session_id") == sid:
            try:
                os.remove(p)
            except OSError:
                pass


def on_pretool(data, sid):
    tool = data.get("tool_name") or ""
    resources = load_resources()
    if tool == "Bash":
        cmd = (data.get("tool_input") or {}).get("command") or ""
        affected = [n for n, r in resources.items() if re.search(r["command"], cmd)]
    else:
        affected = [n for n, r in resources.items() if r.get("mcp") and re.search(r["mcp"], tool)]
    if not affected:
        return
    sessions = load_sessions()
    cdir = sub("claims")
    reasons = []
    pids = []
    claim_only = True
    for name in affected:
        procs = busy_processes(name, resources[name], sessions)
        if procs:
            claim_only = False
            for pid, _ in procs:
                who = owner_of(pid, sessions)
                who = "Session %s" % who if who else "außerhalb von Claude gestartet"
                reasons.append("%s ist belegt: Prozess PID %d (%s), gestartet %s."
                               % (name.capitalize(), pid, who, lstart(pid) or "unbekannt"))
                pids.append(pid)
            continue
        c = read_json(os.path.join(cdir, name + ".json"))
        if (isinstance(c, dict) and c.get("session_id") != sid
                and time.time() - float(c.get("time", 0)) < CLAIM_TTL and alive(c.get("pid"))):
            owner = next((s.get("name") for s in sessions if s.get("session_id") == c.get("session_id")), None)
            reasons.append("%s ist belegt: Session %s startet gerade." % (name.capitalize(), owner or "unbekannt"))
    if reasons:
        if pids:
            wait = ("Nicht parallel starten. Mit dem Monitor-Tool auf das Prozessende warten, z. B. "
                    "`while kill -0 %d 2>/dev/null; do sleep 30; done`, dann diesen Aufruf wiederholen. "
                    "Dem Nutzer kurz sagen, dass gewartet wird." % pids[0])
        else:
            wait = ("Nicht parallel starten. In 60 s erneut versuchen. "
                    "Dem Nutzer kurz sagen, dass gewartet wird.")
        emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                     "permissionDecisionReason": " ".join(reasons) + " " + wait}})
        return
    me = self_claude_pid()
    for name in affected:
        write_json(os.path.join(cdir, name + ".json"),
                   {"session_id": sid, "pid": me, "time": time.time()})


def main():
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            return
        sid = str(data.get("session_id") or "")
        if not sid or "/" in sid:
            return
        ev = data.get("hook_event_name")
        if ev == "SessionStart":
            on_start(data, sid)
        elif ev == "SessionEnd":
            on_end(data, sid)
        elif ev == "PreToolUse":
            on_pretool(data, sid)
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)

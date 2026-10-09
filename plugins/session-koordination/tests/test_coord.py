import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "coord.py")


class CoordTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        # Hermetisch: nur der eigene Fake-Render zaehlt, nicht ein echtes Blender auf dem Rechner.
        self.marker = "render-%d.blend" % os.getpid()
        res = json.loads(json.dumps(self.default_resources()))
        res["blender"]["process"] = r"(?i)(^|/)blender(\s.*)?\s(-b|--background)\s+" + self.marker.replace(".", r"\.")
        with open(os.path.join(self.home, "config.json"), "w") as f:
            json.dump({"resources": res}, f)
        self.procs = []
        self.sess = {}

    def tearDown(self):
        for p in self.procs:
            try:
                p.kill()
                p.wait()
            except Exception:
                pass
        shutil.rmtree(self.home, ignore_errors=True)

    @staticmethod
    def default_resources():
        import importlib.util
        spec = importlib.util.spec_from_file_location("coord", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.DEFAULT_RESOURCES

    def spawn(self, argv):
        p = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.procs.append(p)
        return p

    def session(self, name):
        if name not in self.sess:
            self.sess[name] = self.spawn(["sleep", "120"])
        return self.sess[name]

    def call(self, name, event, **kw):
        data = {"session_id": "sid-" + name, "cwd": "/work/" + name, "hook_event_name": event}
        data.update(kw)
        return self.raw(name, json.dumps(data))

    def raw(self, name, text):
        env = dict(os.environ, COORD_HOME=self.home, COORD_SELF_PID=str(self.session(name).pid))
        return subprocess.run([sys.executable, SCRIPT], input=text, capture_output=True,
                              text=True, env=env, timeout=10)

    def bash(self, name, cmd):
        return self.call(name, "PreToolUse", tool_name="Bash", tool_input={"command": cmd})

    def start_fake(self):
        name = "blender -b " + self.marker
        p = self.spawn(["bash", "-c", 'exec -a "%s" sleep 30' % name])
        for _ in range(50):
            out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout
            if any(l.split(None, 1)[0] == str(p.pid) and name in l
                   for l in out.splitlines() if l.strip()):
                return p
            time.sleep(0.1)
        self.skipTest("ps zeigt die Fake-Kommandozeile nicht")

    def denied(self, r):
        self.assertEqual(r.returncode, 0)
        o = json.loads(r.stdout)
        self.assertEqual(o["hookSpecificOutput"]["permissionDecision"], "deny")
        return o["hookSpecificOutput"]["permissionDecisionReason"]

    def silent(self, r):
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_a_harmlos(self):
        self.silent(self.bash("A", "ls -la"))

    def test_b_c_d_claim(self):
        self.silent(self.bash("A", "blender -b scene.blend -a"))
        self.assertTrue(os.path.exists(os.path.join(self.home, "claims", "blender.json")))
        self.session("B")
        reason = self.denied(self.bash("B", "blender -b scene.blend -a"))
        self.assertIn("startet gerade", reason)
        self.silent(self.bash("A", "blender -b scene.blend -a"))

    def test_e_fake_render_bash(self):
        p = self.start_fake()
        reason = self.denied(self.bash("B", "/Applications/Blender.app/Contents/MacOS/Blender -b x.blend"))
        self.assertIn(str(p.pid), reason)

    def test_f_mcp(self):
        self.start_fake()
        self.denied(self.call("B", "PreToolUse", tool_name="mcp__blender-ahujasid__execute_blender_code",
                              tool_input={}))

    def test_g_regex_trifft_nicht(self):
        self.start_fake()
        self.silent(self.bash("B", "cat blender_notes.txt"))

    def test_h_start_nennt_andere(self):
        self.call("A", "SessionStart")
        r = self.call("B", "SessionStart")
        self.assertEqual(r.returncode, 0)
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("A", ctx)

    def test_i_tote_session(self):
        self.call("A", "SessionStart")
        p = self.session("A")
        p.kill()
        p.wait()
        r = self.call("B", "SessionStart")
        self.silent(r)
        self.assertFalse(os.path.exists(os.path.join(self.home, "sessions", "sid-A.json")))

    def test_j_session_end(self):
        self.call("A", "SessionStart")
        self.bash("A", "blender -b s.blend")
        self.silent(self.call("A", "SessionEnd"))
        self.assertFalse(os.path.exists(os.path.join(self.home, "sessions", "sid-A.json")))
        self.assertFalse(os.path.exists(os.path.join(self.home, "claims", "blender.json")))

    def test_k_kaputtes_stdin(self):
        self.silent(self.raw("A", "nicht json"))

    def test_l_nach_ende_frei(self):
        p = self.start_fake()
        self.denied(self.bash("B", "blender -b x.blend"))
        p.kill()
        p.wait()
        self.silent(self.bash("B", "blender -b x.blend"))


if __name__ == "__main__":
    unittest.main()

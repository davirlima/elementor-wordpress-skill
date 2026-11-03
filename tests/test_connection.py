import base64
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/env_from_mcp.py'

class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        home = pathlib.Path(self.tmp.name)
        (home / 'config.toml').write_text(''.join(
            f'[mcp_servers.{name}]\nurl = "https://{host}/wp-json/elementor/mcp/"\nhttp_headers = {{ Authorization = "Basic {base64.b64encode(b"user:password").decode()}" }}\n'
            for name, host in [('first', 'one.example'), ('second', 'two.example')]))
        self.env = dict(os.environ, HOME=self.tmp.name, CODEX_HOME=self.tmp.name)

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.tmp.name, env=self.env, text=True, capture_output=True)

    def test_ambiguous_selection_fails_closed(self):
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('export ', result.stdout)

    def test_exact_host_selects_site(self):
        result = self.run_script('two.example')
        self.assertEqual(result.returncode, 0)
        self.assertIn('https://two.example', result.stdout)
        self.assertNotIn('one.example', result.stdout)

    def test_substring_cannot_select_wrong_site(self):
        self.assertNotEqual(self.run_script('one').returncode, 0)

if __name__ == '__main__':
    unittest.main()

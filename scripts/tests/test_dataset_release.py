"""Use the release validator once for the actual published data."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ReleaseIntegrityTests(unittest.TestCase):
    def test_current_release_passes_integrity_check(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/maintenance/validate_clean_release.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])


if __name__ == "__main__":
    unittest.main()

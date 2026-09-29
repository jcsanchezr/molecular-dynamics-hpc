"""Synthetic parser tests only; these do not execute GROMACS."""
import importlib.util
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

source = Path(__file__).resolve().parents[1] / "analysis" / "check_water_em.py"
spec = importlib.util.spec_from_file_location("check_water_em", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WaterEMTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        atom_lines = [f"{1:5d}{'SOL':<5}{atom:>5}{i:5d}{x:8.3f}{0:8.3f}{0:8.3f}"
                      for i, (atom, x) in enumerate(
                          [("OW", 0.1), ("HW1", 0.2), ("HW2", 0.3)], 1)]
        gro = "fixture\n3\n" + "\n".join(atom_lines) + "\n3.0 3.0 3.0\n"
        for name in ("water.gro", "em.gro"):
            (self.run / name).write_text(gro)
        (self.run / "topol.top").write_text("[ molecules ]\nSOL 1\n")
        (self.run / "em.mdp").write_text("emtol = 1000\n")
        (self.run / "em.log").write_text(
            "Potential Energy = -2.000e+01\nMaximum force = 500 on atom 1\n")
        (self.run / "potential.xvg").write_text("0 -10\n1 -20\n")
        (self.run / "mdrun-console.log").write_text("Steepest Descents completed\n")

    def test_accepts_coarse_convergence(self):
        self.assertEqual(module.assess(self.run)["status"], "PASS")

    def test_rejects_force_above_threshold(self):
        p = self.run / "em.log"
        p.write_text(p.read_text().replace("500", "1500"))
        self.assertEqual(module.assess(self.run)["status"], "REVIEW_REQUIRED")

    def test_rejects_nonfinite(self):
        (self.run / "potential.xvg").write_text("0 nan\n")
        with self.assertRaises(ValueError):
            module.assess(self.run)

    def test_rejects_increased_energy(self):
        (self.run / "potential.xvg").write_text("0 -30\n1 -20\n")
        self.assertEqual(module.assess(self.run)["status"], "REVIEW_REQUIRED")

    def test_rejects_topology_count_mismatch(self):
        (self.run / "topol.top").write_text("[ molecules ]\nSOL 2\n")
        with self.assertRaises(ValueError):
            module.assess(self.run)

    def test_rejects_missing_final_force(self):
        (self.run / "em.log").write_text("unfinished log\n")
        with self.assertRaises(ValueError):
            module.assess(self.run)


    def test_rejects_settle_even_when_force_converged(self):
        p = self.run / "em.log"
        p.write_text(p.read_text() +
                     "step 11: One or more water molecules can not be settled.\n")
        report = module.assess(self.run)
        self.assertTrue(report["numerical_checks_passed"])
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["diagnostics"][0]["code"], "SETTLE_DIAGNOSTIC")

    def test_rejects_settle_in_console_only(self):
        (self.run / "mdrun-console.log").write_text(
            "step 11: One or more water molecules can not be settled.\n")
        self.assertEqual(module.assess(self.run)["status"], "REVIEW_REQUIRED")

    def test_rejects_missing_console_log(self):
        (self.run / "mdrun-console.log").unlink()
        report = module.assess(self.run)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["diagnostics"][0]["code"], "MISSING_DIAGNOSTIC_LOG")

    def test_rejects_empty_console_log(self):
        (self.run / "mdrun-console.log").write_text("")
        self.assertEqual(module.assess(self.run)["status"], "REVIEW_REQUIRED")

    def test_rejects_lincs_warning(self):
        (self.run / "mdrun-console.log").write_text("LINCS WARNING at step 4\n")
        self.assertEqual(module.assess(self.run)["status"], "REVIEW_REQUIRED")

    def test_rejects_fatal_error(self):
        (self.run / "mdrun-console.log").write_text("Fatal error: stopped\n")
        self.assertEqual(module.assess(self.run)["status"], "REVIEW_REQUIRED")

    def test_normal_constraint_configuration_is_not_a_warning(self):
        (self.run / "mdrun-console.log").write_text(
            "Using SETTLE for rigid water\nconstraint-algorithm = Lincs\n")
        self.assertEqual(module.assess(self.run)["status"], "PASS")

    def test_stdout_only_preserves_original_summary(self):
        p = self.run / "summary.json"
        original = b'{"status":"PASS","historical":true}\n'
        p.write_bytes(original)
        (self.run / "mdrun-console.log").write_text(
            "step 11: One or more water molecules can not be settled.\n")
        result = subprocess.run(
            [sys.executable, str(source), "--stdout-only", str(self.run)],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('"status": "REVIEW_REQUIRED"', result.stdout)
        self.assertEqual(p.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()

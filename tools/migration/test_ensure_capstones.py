import shutil
import unittest
from pathlib import Path

import ensure_capstones as ec


class EnsureCapstonesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parents[2] / ".test-tmp" / "ensure-capstones"
        if self.tmp.exists():
            shutil.rmtree(self.tmp)
        self.tmp.mkdir(parents=True)

    def tearDown(self):
        if self.tmp.exists():
            shutil.rmtree(self.tmp)

    def test_route_capstone_last_uses_raw_input_inside_exercises_index(self):
        index = self.tmp / "volume-ii" / "integers" / "proofs" / "exercises" / "index.tex"
        target = "volume-ii/integers/proofs/exercises/capstone-integers"

        ec.route_capstone_last(index, target, True)

        text = index.read_text(encoding="utf-8")
        self.assertIn(r"\input{volume-ii/integers/proofs/exercises/capstone-integers}", text)
        self.assertNotIn(r"\LRACapstoneInput", text)
        self.assertNotIn(r"\subsection*{Exercise Proofs}", text)

    def test_ensure_proofs_routes_exercises_uses_raw_input_inside_proofs_index(self):
        index = self.tmp / "volume-ii" / "integers" / "proofs" / "index.tex"
        index.parent.mkdir(parents=True)
        index.write_text("% proofs\n", encoding="utf-8")
        target = "volume-ii/integers/proofs/exercises/index"

        ec.ensure_proofs_routes_exercises(index, target, True)

        text = index.read_text(encoding="utf-8")
        self.assertIn(r"\input{volume-ii/integers/proofs/exercises/index}", text)
        self.assertNotIn(r"\LRAExercisesInput", text)


if __name__ == "__main__":
    unittest.main()

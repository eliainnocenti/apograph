import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.apograph.compile import CompilationError, compile_entrypoints


class CompilationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "main.tex").write_text("fixture", encoding="utf-8")
        self.template = {
            "id": "fixture",
            "format": "latex",
            "compiler": "pdflatex",
            "entrypoints": [
                {"path": "main.tex", "role": "starter", "include_in_artifact": True, "preview": True}
            ],
        }

    def tearDown(self):
        self.temporary.cleanup()

    def test_artifact_compile_removes_monorepo_search_environment(self):
        observed = {}

        def fake_run(command, **kwargs):
            observed["command"] = command
            observed["env"] = kwargs["env"]
            outdir = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("-outdir=")))
            if not outdir.is_absolute():
                outdir = Path(kwargs["cwd"]) / outdir
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / "main.pdf").write_bytes(b"pdf")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        environment = {"PATH": os.environ.get("PATH", ""), "TEXINPUTS": "/checkout/shared"}
        with mock.patch("scripts.apograph.compile.subprocess.run", side_effect=fake_run):
            results = compile_entrypoints(
                self.template,
                self.project,
                self.root / "output",
                environment=environment,
            )

        self.assertNotIn("TEXINPUTS", observed["env"])
        self.assertIn("-halt-on-error", observed["command"])
        self.assertEqual(results[0].entrypoint, "main.tex")

    def test_source_compile_may_explicitly_add_shared_search_path(self):
        shared = self.root / "shared/latex"
        shared.mkdir(parents=True)
        observed = {}

        def fake_run(command, **kwargs):
            observed["texinputs"] = kwargs["env"].get("TEXINPUTS")
            outdir = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("-outdir=")))
            if not outdir.is_absolute():
                outdir = Path(kwargs["cwd"]) / outdir
            (outdir / "main.pdf").write_bytes(b"pdf")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with mock.patch("scripts.apograph.compile.subprocess.run", side_effect=fake_run):
            compile_entrypoints(
                self.template,
                self.project,
                self.root / "output",
                source_shared_dir=shared,
            )
        self.assertEqual(observed["texinputs"], f"{shared.resolve()}//:")

    def test_failure_preserves_compiler_output_for_diagnostics(self):
        completed = subprocess.CompletedProcess(
            ["latexmk"], 12, stdout="line one", stderr="fatal fixture error"
        )
        with mock.patch("scripts.apograph.compile.subprocess.run", return_value=completed):
            with self.assertRaises(CompilationError) as raised:
                compile_entrypoints(self.template, self.project, self.root / "output")
        self.assertIn("fatal fixture error", raised.exception.output)


if __name__ == "__main__":
    unittest.main()

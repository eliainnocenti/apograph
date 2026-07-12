import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import catalog as catalog_module
from scripts.apograph.compile import compile_entrypoints


FIXTURES = catalog_module.REPO_ROOT / "tests" / "fixtures" / "latex"
SHARED = catalog_module.REPO_ROOT / "shared" / "latex"


@unittest.skipUnless(shutil.which("latexmk"), "latexmk is required for shared LaTeX fixtures")
class SharedLatexCompatibilityTests(unittest.TestCase):
    def test_shared_modules_compile_for_supported_document_classes(self):
        shared_modules = sorted(SHARED.glob("apograph-*.sty"))
        self.assertIn(SHARED / "apograph-theorems.sty", shared_modules)

        for document_class in ("article", "report", "book", "beamer"):
            with self.subTest(document_class=document_class), tempfile.TemporaryDirectory() as temporary:
                temporary_path = Path(temporary)
                project = temporary_path / "project"
                project.mkdir()
                shutil.copyfile(FIXTURES / document_class / "main.tex", project / "main.tex")
                for module in shared_modules:
                    shutil.copyfile(module, project / module.name)

                template = {
                    "id": f"shared-{document_class}-fixture",
                    "format": "latex",
                    "compiler": "pdflatex",
                    "entrypoints": [
                        {
                            "path": "main.tex",
                            "role": "test",
                            "include_in_artifact": True,
                            "preview": False,
                        }
                    ],
                }
                results = compile_entrypoints(
                    template,
                    project,
                    temporary_path / "output",
                    entrypoints=template["entrypoints"],
                )
                self.assertEqual(len(results), 1)
                self.assertTrue(results[0].pdf_path.is_file())

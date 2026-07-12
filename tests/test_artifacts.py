import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
import shutil
from pathlib import Path
from unittest import mock

from scripts.apograph.artifacts import ArtifactError, build_artifact
from scripts import catalog as catalog_module


def fixture_template() -> dict:
    return {
        "id": "report-fixture-latex",
        "name": "Artifact Fixture",
        "description": "A fixture used to test canonical artifacts.",
        "purpose": "report",
        "variant": "fixture",
        "format": "latex",
        "status": "draft",
        "institution": {
            "id": "generic",
            "name": "Generic / Unaffiliated",
            "relationship": "generic",
            "requirements_url": None,
            "last_verified": None,
        },
        "compiler": "pdflatex",
        "compatibility": {"texlive": [], "overleaf": "untested"},
        "source_dir": "templates/report/fixture/latex",
        "entrypoints": [
            {"path": "main.tex", "role": "starter", "include_in_artifact": True, "preview": True},
            {"path": "showcase.tex", "role": "showcase", "include_in_artifact": False, "preview": False},
        ],
        "shared_deps": ["shared/latex/apograph-fixture.sty"],
        "license": {"expression": "MIT", "status": "declared", "notes": "fixture"},
        "upstream": {"kind": "original", "sources": [], "notes": "fixture"},
        "assets": [
            {
                "id": "institution-logo",
                "description": "Institution logo",
                "local_path": "theme/assets/logo.pdf",
                "mode": "user-provided",
                "required": False,
                "source_url": None,
                "sha256": None,
                "fallback": "text-box",
                "license": {"expression": None, "status": "review-required", "notes": "fixture"},
            }
        ],
        "tags": ["report", "fixture", "latex"],
        "maintainers": [{"name": "Test", "github": None}],
        "readiness_notes": "fixture",
        "created": "2026-01-01",
        "updated": "2026-01-01",
    }


class ArtifactBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "templates/report/fixture/latex"
        self.source.mkdir(parents=True)
        shared = self.root / "shared/latex"
        shared.mkdir(parents=True)
        (self.source / "main.tex").write_text(
            "\\documentclass{article}\n\\usepackage{apograph-fixture}\n\\begin{document}ok\\end{document}\n",
            encoding="utf-8",
        )
        (self.source / "showcase.tex").write_text("source only\n", encoding="utf-8")
        (self.source / "reference.pdf").write_bytes(b"%PDF-1.4 legitimate fixture\n")
        (self.source / "out").mkdir()
        (self.source / "out/main.pdf").write_bytes(b"generated")
        (self.source / "main.aux").write_text("generated", encoding="utf-8")
        (self.source / "theme/assets").mkdir(parents=True)
        (self.source / "theme/assets/.gitkeep").write_text("", encoding="utf-8")
        (self.source / "theme/assets/logo.pdf").write_bytes(b"private logo")
        (self.source / "theme/assets/undeclared.png").write_bytes(b"private background")
        (shared / "apograph-fixture.sty").write_text(
            "\\ProvidesPackage{apograph-fixture}\n", encoding="utf-8"
        )
        self.template = fixture_template()

    def tearDown(self):
        self.temporary.cleanup()

    def build(self, output_name: str, **kwargs):
        return build_artifact(
            self.template,
            self.root / output_name,
            repo_root=self.root,
            release_version="0.1.0-dev",
            source_commit="fixture-commit",
            source_date_epoch=315532800,
            verify=False,
            **kwargs,
        )

    def archive(self, result):
        return zipfile.ZipFile(result.zip_path)

    def test_shared_package_is_at_root_and_source_is_not_rewritten(self):
        result = self.build("first")
        with self.archive(result) as archive:
            names = archive.namelist()
            self.assertIn("apograph-fixture.sty", names)
            self.assertNotIn("shared/apograph-fixture.sty", names)
            self.assertEqual(
                archive.read("main.tex").decode("utf-8"),
                (self.source / "main.tex").read_text(encoding="utf-8"),
            )

    def test_explicit_generated_files_are_excluded_but_pdf_source_survives(self):
        result = self.build("first")
        with self.archive(result) as archive:
            names = set(archive.namelist())
        self.assertIn("reference.pdf", names)
        self.assertNotIn("out/main.pdf", names)
        self.assertNotIn("main.aux", names)
        self.assertNotIn("showcase.tex", names)

    def test_local_user_assets_and_undeclared_theme_assets_never_leak(self):
        result = self.build("first")
        with self.archive(result) as archive:
            names = set(archive.namelist())
            readme = archive.read("README.md").decode("utf-8")
            metadata = json.loads(archive.read("template.json"))
        self.assertNotIn("theme/assets/logo.pdf", names)
        self.assertNotIn("theme/assets/undeclared.png", names)
        self.assertIn("`theme/assets/logo.pdf`", readme)
        self.assertIn("no automatic logo download URL", readme)
        asset = metadata["artifact"]["assets"][0]
        self.assertFalse(asset["included"])
        self.assertEqual(asset["mode"], "user-provided")

    def test_ignored_local_assets_cannot_change_archive_checksum(self):
        first = self.build("first")
        (self.source / "theme/assets/logo.pdf").write_bytes(b"changed private logo")
        (self.source / "theme/assets/new-private.png").write_bytes(b"more private data")
        second = self.build("second")
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(first.zip_path.read_bytes(), second.zip_path.read_bytes())

    def test_two_builds_have_identical_archives_and_sidecars(self):
        first = self.build("first")
        second = self.build("second")
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(first.checksum_path.read_text(), second.checksum_path.read_text())
        first_report = json.loads(first.report_path.read_text())
        second_report = json.loads(second.report_path.read_text())
        self.assertEqual(first_report, second_report)

    def test_safe_output_refuses_overwrite_without_force(self):
        self.build("first")
        with self.assertRaisesRegex(ArtifactError, "refusing to overwrite"):
            self.build("first")
        rebuilt = self.build("first", force=True)
        self.assertTrue(rebuilt.zip_path.is_file())

    def test_missing_shared_dependency_is_fatal(self):
        (self.root / "shared/latex/apograph-fixture.sty").unlink()
        with self.assertRaisesRegex(ArtifactError, "shared dependency does not exist"):
            self.build("first")

    def test_failed_forced_rebuild_preserves_previous_outputs(self):
        first = self.build("first")
        original_zip = first.zip_path.read_bytes()
        (self.root / "shared/latex/apograph-fixture.sty").unlink()
        with self.assertRaises(ArtifactError):
            self.build("first", force=True)
        self.assertEqual(first.zip_path.read_bytes(), original_zip)

    def test_output_may_not_be_nested_inside_template_source(self):
        with self.assertRaisesRegex(ArtifactError, "inside the template source"):
            build_artifact(
                self.template,
                self.source / "release",
                repo_root=self.root,
                verify=False,
            )

    def test_release_mode_requires_clean_commit_check(self):
        template = copy.deepcopy(self.template)
        template["status"] = "beta"
        template["license"] = {"expression": "MIT", "status": "verified", "notes": "fixture"}
        template["compatibility"]["overleaf"] = "compatible"
        with mock.patch("scripts.apograph.artifacts._require_clean_release_checkout") as check:
            result = build_artifact(
                template,
                self.root / "release",
                repo_root=self.root,
                source_commit="0123456789abcdef",
                release_mode=True,
                verify=False,
            )
        check.assert_called_once_with(self.root, "0123456789abcdef")
        self.assertTrue(result.zip_path.is_file())

    def test_bundled_asset_is_included_with_checksum(self):
        template = copy.deepcopy(self.template)
        asset = template["assets"][0]
        asset["mode"] = "bundled"
        asset["license"] = {"expression": "MIT", "status": "verified", "notes": "fixture"}
        expected = hashlib.sha256(b"private logo").hexdigest()
        result = build_artifact(
            template,
            self.root / "bundled",
            repo_root=self.root,
            verify=False,
        )
        with self.archive(result) as archive:
            self.assertEqual(archive.read("theme/assets/logo.pdf"), b"private logo")
            metadata = json.loads(archive.read("template.json"))
        self.assertEqual(metadata["artifact"]["assets"][0]["sha256"], expected)

@unittest.skipUnless(shutil.which("latexmk"), "latexmk is required for isolated integration compilation")
class PoliToArtifactIntegrationTests(unittest.TestCase):
    def test_packed_showcase_compiles_without_user_provided_assets(self):
        catalog = catalog_module.load_catalog()
        template = next(
            item
            for item in catalog["templates"]
            if item["id"] == "presentation-beamer-polito-latex"
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = build_artifact(
                template,
                Path(temporary),
                repo_root=catalog_module.REPO_ROOT,
                release_version=catalog["release_version"],
                source_commit="integration-fixture",
                source_date_epoch=315532800,
                verify=True,
            )
            self.assertEqual(
                [item.entrypoint for item in result.compilation_results],
                ["main.tex", "showcase.tex"],
            )
            self.assertTrue(result.preview_path.is_file())
            with zipfile.ZipFile(result.zip_path) as archive:
                names = set(archive.namelist())
            self.assertIn("README.md", names)
            self.assertIn("NOTICE", names)
            self.assertIn("LICENSES/GPL-3.0-or-later.txt", names)
            self.assertIn("LICENSES/CC-BY-4.0.txt", names)
            self.assertIn("beamerthemeapographpolito.sty", names)
            self.assertIn("content/slides.tex", names)
            self.assertIn("showcase/slides/01-introduction.tex", names)
            self.assertFalse(any(name.startswith("sections/") for name in names))
            self.assertNotIn("theme/beamerthemesintef.sty", names)
            for asset in template["assets"]:
                if asset["mode"] == "user-provided":
                    self.assertNotIn(asset["local_path"], names)


if __name__ == "__main__":
    unittest.main()

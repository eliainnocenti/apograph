import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts import catalog as catalog_module
from scripts import release as release_module


class ReleaseMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog_module.load_catalog()
        cls.template = catalog_module.public_templates(cls.catalog)[0]
        cls.source_commit = "a" * 40

    def test_release_tag_must_match_catalog_and_changelog(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["release_version"] = "0.1.0"

        version = release_module.validate_release_tag(
            catalog, "v0.1.0", "# Changelog\n\n## 0.1.0 — 2026-07-12\n"
        )

        self.assertEqual(version, "0.1.0")
        with self.assertRaisesRegex(release_module.ReleaseError, "does not match"):
            release_module.validate_release_tag(catalog, "v0.2.0", "## 0.1.0\n")
        with self.assertRaisesRegex(release_module.ReleaseError, "no release heading"):
            release_module.validate_release_tag(catalog, "v0.1.0", "## Unreleased\n")

    def test_development_version_cannot_be_published(self):
        with self.assertRaisesRegex(release_module.ReleaseError, "development"):
            release_module.validate_release_tag(
                self.catalog,
                f"v{self.catalog['release_version']}",
                f"## {self.catalog['release_version']}\n",
            )

    def write_candidate(self, build_dir: Path, *, mode: str = "release") -> None:
        template_id = self.template["id"]
        zip_name = f"{template_id}.zip"
        preview_name = f"{template_id}.preview.pdf"
        zip_bytes = b"deterministic zip fixture"
        preview_bytes = b"preview fixture"
        zip_sha256 = hashlib.sha256(zip_bytes).hexdigest()
        preview_sha256 = hashlib.sha256(preview_bytes).hexdigest()
        (build_dir / zip_name).write_bytes(zip_bytes)
        (build_dir / preview_name).write_bytes(preview_bytes)
        (build_dir / f"{zip_name}.sha256").write_text(
            f"{zip_sha256}  {zip_name}\n", encoding="utf-8"
        )
        report = {
            "template_id": template_id,
            "status": self.template["status"],
            "mode": mode,
            "release_version": self.catalog["release_version"],
            "source_commit": self.source_commit,
            "source_date_epoch": 315532800,
            "artifact": {"path": zip_name, "sha256": zip_sha256},
            "preview": {"path": preview_name, "sha256": preview_sha256},
        }
        (build_dir / f"{template_id}.build.json").write_text(
            json.dumps(report), encoding="utf-8"
        )

    def test_assemble_verifies_and_indexes_release_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary)
            self.write_candidate(build_dir)

            index = release_module.assemble_release_candidate(
                self.catalog, build_dir, source_commit=self.source_commit
            )

            self.assertEqual(index["source_commit"], self.source_commit)
            self.assertEqual(
                [template["id"] for template in index["templates"]],
                [self.template["id"]],
            )
            self.assertTrue((build_dir / "CATALOG.json").is_file())
            self.assertTrue((build_dir / "release-index.json").is_file())

    def test_assemble_rejects_nonrelease_or_tampered_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary)
            self.write_candidate(build_dir, mode="developer")

            with self.assertRaisesRegex(release_module.ReleaseError, "release mode"):
                release_module.assemble_release_candidate(
                    self.catalog, build_dir, source_commit=self.source_commit
                )

        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary)
            self.write_candidate(build_dir)
            (build_dir / f"{self.template['id']}.zip").write_bytes(b"tampered")

            with self.assertRaisesRegex(release_module.ReleaseError, "checksum mismatch"):
                release_module.assemble_release_candidate(
                    self.catalog, build_dir, source_commit=self.source_commit
                )


if __name__ == "__main__":
    unittest.main()

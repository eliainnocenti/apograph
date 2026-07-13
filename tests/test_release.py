import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

        version = release_module.validate_release_tag(
            catalog, "v0.1.0", "# Changelog\n\n## 0.1.0 — 2026-07-13\n"
        )

        self.assertEqual(version, "0.1.0")
        with self.assertRaisesRegex(release_module.ReleaseError, "does not match"):
            release_module.validate_release_tag(catalog, "v0.2.0", "## 0.1.0\n")
        with self.assertRaisesRegex(release_module.ReleaseError, "no release heading"):
            release_module.validate_release_tag(catalog, "v0.1.0", "## Unreleased\n")

    def test_development_version_cannot_be_published(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["release_version"] = "0.1.0-dev"
        with self.assertRaisesRegex(release_module.ReleaseError, "development"):
            release_module.validate_release_tag(
                catalog,
                f"v{catalog['release_version']}",
                f"## {catalog['release_version']}\n",
            )

    def test_publication_requires_a_protected_tag(self):
        release_module.validate_protected_ref("true")
        with self.assertRaisesRegex(release_module.ReleaseError, "not protected"):
            release_module.validate_protected_ref("false")

    def test_github_outputs_are_catalog_backed(self):
        values = dict(
            line.split("=", 1)
            for line in release_module.render_github_outputs(self.catalog).splitlines()
        )
        self.assertEqual(values["release_tag"], "v0.1.0")
        self.assertEqual(values["prerelease"], "true")
        self.assertEqual(values["release_notes_path"], "docs/releases/v0.1.0.md")

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
            self.assertEqual(index["release_channel"], "prerelease")
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

    def test_published_release_must_have_exact_catalog_asset_set(self):
        assets = [
            {
                "name": name,
                "state": "uploaded",
                "browser_download_url": catalog_module.release_asset_url(
                    self.catalog, name
                ),
            }
            for name in sorted(
                release_module.expected_release_asset_names(self.catalog)
            )
        ]
        payload = {
            "tag_name": "v0.1.0",
            "draft": False,
            "prerelease": True,
            "html_url": "https://github.com/eliainnocenti/apograph/releases/tag/v0.1.0",
            "assets": assets,
        }

        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        with mock.patch("scripts.release.urlopen", return_value=response):
            url = release_module.verify_published_release(
                self.catalog, "v0.1.0", token="fixture-token"
            )

        self.assertEqual(url, payload["html_url"])


if __name__ == "__main__":
    unittest.main()

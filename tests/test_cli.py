import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from apograph_templates.cli import main as cli_main
from apograph_templates.errors import ApographError
from apograph_templates.install import install_template
from apograph_templates.remote import GitHubReleaseSource


def zip_bytes(files=None, *, symlink=False):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if symlink:
            info = zipfile.ZipInfo("unsafe-link")
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "README.md")
        else:
            for name, content in (files or {"README.md": "Ready\n"}).items():
                archive.writestr(name, content)
    return output.getvalue()


class FakeHTTPClient:
    def __init__(self, *, json_values, byte_values):
        self.json_values = json_values
        self.byte_values = byte_values
        self.downloaded_urls = []

    def read_json(self, url):
        try:
            return self.json_values[url]
        except KeyError as exc:
            raise AssertionError(f"unexpected JSON URL: {url}") from exc

    def read_bytes(self, url, *, limit=10 * 1024 * 1024):
        try:
            data = self.byte_values[url]
        except KeyError as exc:
            raise AssertionError(f"unexpected byte URL: {url}") from exc
        if len(data) > limit:
            raise ApographError("fixture exceeds limit")
        return data

    def download(self, url, destination):
        self.downloaded_urls.append(url)
        data = self.read_bytes(url, limit=1024 * 1024 * 1024)
        destination.write_bytes(data)
        return hashlib.sha256(data).hexdigest()


def release_source(*, archive=None, archive_sha=None, catalog_sha=None):
    archive = archive if archive is not None else zip_bytes()
    template_id = "thesis-polito-latex"
    catalog = {
        "release_version": "0.2.0",
        "templates": [
            {
                "id": template_id,
                "name": "PoliTo Thesis",
                "description": "A verified thesis starter.",
                "purpose": "thesis",
                "format": "latex",
                "status": "beta",
                "institution": {
                    "name": "Politecnico di Torino",
                    "relationship": "unofficial",
                },
                "compiler": "pdflatex",
                "license": {"expression": "CC-BY-4.0 AND MIT"},
            }
        ],
    }
    catalog_bytes = (json.dumps(catalog, sort_keys=True) + "\n").encode()
    expected_archive_sha = archive_sha or hashlib.sha256(archive).hexdigest()
    expected_catalog_sha = catalog_sha or hashlib.sha256(catalog_bytes).hexdigest()
    index = {
        "format_version": "1.0.0",
        "release_version": "0.2.0",
        "release_channel": "prerelease",
        "tag": "v0.2.0",
        "catalog": {"path": "CATALOG.json", "sha256": expected_catalog_sha},
        "templates": [
            {
                "id": template_id,
                "status": "beta",
                "zip": {
                    "path": f"{template_id}.zip",
                    "sha256": expected_archive_sha,
                    "checksum": f"{template_id}.zip.sha256",
                },
                "preview": None,
                "build_report": f"{template_id}.build.json",
            }
        ],
    }
    index_bytes = (json.dumps(index, sort_keys=True) + "\n").encode()
    base = "https://downloads.example"
    assets = [
        {
            "name": "release-index.json",
            "state": "uploaded",
            "browser_download_url": f"{base}/release-index.json",
            "digest": f"sha256:{hashlib.sha256(index_bytes).hexdigest()}",
        },
        {
            "name": "CATALOG.json",
            "state": "uploaded",
            "browser_download_url": f"{base}/CATALOG.json",
            "digest": f"sha256:{hashlib.sha256(catalog_bytes).hexdigest()}",
        },
        {
            "name": f"{template_id}.zip",
            "state": "uploaded",
            "browser_download_url": f"{base}/{template_id}.zip",
            "digest": f"sha256:{hashlib.sha256(archive).hexdigest()}",
        },
    ]
    release = {
        "tag_name": "v0.2.0",
        "html_url": "https://github.com/eliainnocenti/apograph/releases/tag/v0.2.0",
        "draft": False,
        "prerelease": True,
        "published_at": "2026-07-18T12:00:00Z",
        "assets": assets,
    }
    api = "https://api.github.test/repos/eliainnocenti/apograph"
    fake_http = FakeHTTPClient(
        json_values={
            f"{api}/releases?per_page=100": [release],
            f"{api}/releases/tags/v0.2.0": release,
        },
        byte_values={
            f"{base}/release-index.json": index_bytes,
            f"{base}/CATALOG.json": catalog_bytes,
            f"{base}/{template_id}.zip": archive,
        },
    )
    source = GitHubReleaseSource(api_url="https://api.github.test", http=fake_http)
    return source, fake_http


class GitHubReleaseSourceTests(unittest.TestCase):
    def test_latest_published_prerelease_is_resolved_and_verified(self):
        source, _ = release_source()

        release = source.resolve()

        self.assertEqual(release.tag, "v0.2.0")
        self.assertEqual(release.catalog["release_version"], "0.2.0")
        self.assertEqual(release.index["templates"][0]["id"], "thesis-polito-latex")

    def test_explicit_version_accepts_tag_without_v_prefix(self):
        source, _ = release_source()

        release = source.resolve("0.2.0")

        self.assertEqual(release.tag, "v0.2.0")

    def test_catalog_checksum_mismatch_is_rejected(self):
        source, _ = release_source(catalog_sha="0" * 64)

        with self.assertRaisesRegex(ApographError, "Catalog snapshot checksum"):
            source.resolve()

    def test_non_https_release_asset_is_rejected(self):
        source, fake_http = release_source()
        release_url = "https://api.github.test/repos/eliainnocenti/apograph/releases?per_page=100"
        fake_http.json_values[release_url][0]["assets"][0][
            "browser_download_url"
        ] = "file:///tmp/release-index.json"

        with self.assertRaisesRegex(ApographError, "expected an HTTPS URL"):
            source.resolve()

    def test_zip_checksum_mismatch_removes_download(self):
        source, _ = release_source(archive_sha="0" * 64)
        release = source.resolve()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "download.zip"

            with self.assertRaisesRegex(ApographError, "ZIP checksum mismatch"):
                source.download_template(release, "thesis-polito-latex", target)

            self.assertFalse(target.exists())


class InstallerTests(unittest.TestCase):
    def test_verified_template_is_published_atomically(self):
        source, fake_http = release_source(
            archive=zip_bytes({"README.md": "Ready\n", "content/chapter.tex": "Hello\n"})
        )
        release = source.resolve()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "my-thesis"

            result = install_template(
                source, release, "thesis-polito-latex", destination
            )

            self.assertEqual(result, destination.absolute())
            self.assertEqual((destination / "README.md").read_text(), "Ready\n")
            self.assertEqual((destination / "content/chapter.tex").read_text(), "Hello\n")
            self.assertEqual(len(fake_http.downloaded_urls), 1)
            self.assertEqual(list(Path(temporary).glob(".*.apograph-*")), [])

    def test_existing_destination_is_never_overwritten(self):
        source, fake_http = release_source()
        release = source.resolve()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "existing"
            destination.mkdir()

            with self.assertRaisesRegex(ApographError, "already exists"):
                install_template(source, release, "thesis-polito-latex", destination)

            self.assertEqual(fake_http.downloaded_urls, [])

    def test_traversal_member_is_rejected_and_cleaned_up(self):
        source, _ = release_source(archive=zip_bytes({"../escape.tex": "unsafe"}))
        release = source.resolve()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "project"

            with self.assertRaisesRegex(ApographError, "Unsafe ZIP member"):
                install_template(source, release, "thesis-polito-latex", destination)

            self.assertFalse(destination.exists())
            self.assertFalse((Path(temporary) / "escape.tex").exists())
            self.assertEqual(list(Path(temporary).glob(".*.apograph-*")), [])

    def test_symlink_member_is_rejected(self):
        source, _ = release_source(archive=zip_bytes(symlink=True))
        release = source.resolve()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "project"

            with self.assertRaisesRegex(ApographError, "link or special file"):
                install_template(source, release, "thesis-polito-latex", destination)

            self.assertFalse(destination.exists())


class CommandLineTests(unittest.TestCase):
    def test_list_and_info_use_release_catalog(self):
        source, _ = release_source()
        output = io.StringIO()
        errors = io.StringIO()

        self.assertEqual(cli_main(["list"], source=source, stdout=output, stderr=errors), 0)
        self.assertIn("thesis-polito-latex", output.getvalue())
        self.assertEqual(errors.getvalue(), "")

        output = io.StringIO()
        self.assertEqual(
            cli_main(
                ["info", "thesis-polito-latex", "--version", "0.2.0"],
                source=source,
                stdout=output,
                stderr=errors,
            ),
            0,
        )
        self.assertIn("Politecnico di Torino (unofficial)", output.getvalue())
        self.assertIn("CC-BY-4.0 AND MIT", output.getvalue())

    def test_new_and_typo_suggestion(self):
        source, _ = release_source()
        output = io.StringIO()
        errors = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "thesis"

            code = cli_main(
                ["new", "thesis-polito-latex", str(destination)],
                source=source,
                stdout=output,
                stderr=errors,
            )

            self.assertEqual(code, 0)
            self.assertTrue((destination / "README.md").is_file())
            self.assertIn("Created PoliTo Thesis", output.getvalue())

        output = io.StringIO()
        errors = io.StringIO()
        code = cli_main(
            ["info", "thesis-polito-late"],
            source=source,
            stdout=output,
            stderr=errors,
        )
        self.assertEqual(code, 1)
        self.assertIn("Did you mean 'thesis-polito-latex'?", errors.getvalue())


if __name__ == "__main__":
    unittest.main()

import re
import unittest
from pathlib import Path

from scripts import catalog as catalog_module


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class GovernanceDocumentationTests(unittest.TestCase):
    def test_local_markdown_links_exist(self):
        markdown_files = [
            catalog_module.REPO_ROOT / "README.md",
            catalog_module.REPO_ROOT / "AGENTS.md",
            *sorted((catalog_module.REPO_ROOT / "docs").rglob("*.md")),
        ]
        missing = []
        for markdown_file in markdown_files:
            text = markdown_file.read_text(encoding="utf-8")
            for target in LINK_RE.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path_text = target.split("#", 1)[0]
                if not path_text:
                    continue
                target_path = (markdown_file.parent / path_text).resolve()
                if not target_path.exists():
                    missing.append(f"{markdown_file.relative_to(catalog_module.REPO_ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_maintainer_roadmap_records_completed_foundation(self):
        roadmap = (catalog_module.REPO_ROOT / "docs" / "maintainer" / "roadmap.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Phases 0–5", roadmap)
        self.assertIn("Template foundation refactor", roadmap)

    def test_release_notes_are_the_only_release_narrative(self):
        self.assertFalse((catalog_module.REPO_ROOT / "CHANGELOG.md").exists())
        notes_path = (
            catalog_module.REPO_ROOT
            / "docs"
            / "releases"
            / f"v{catalog_module.load_catalog()['release_version']}.md"
        )
        self.assertTrue(notes_path.is_file())

    def test_cli_package_exposes_dependency_free_apograph_command(self):
        pyproject = (catalog_module.REPO_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        readme = (catalog_module.REPO_ROOT / "README.md").read_text(encoding="utf-8")
        launcher = (catalog_module.REPO_ROOT / "scripts" / "use.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('name = "apograph-templates"', pyproject)
        self.assertIn('dependencies = []', pyproject)
        self.assertIn('dynamic = ["version"]', pyproject)
        self.assertIn(
            'apograph = "apograph_templates.cli:entrypoint"', pyproject
        )
        self.assertEqual(
            (catalog_module.REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8"),
            "prune tests\n",
        )
        self.assertIn("pipx install apograph-templates", readme)
        self.assertNotIn("pipx install \"git+", readme)
        self.assertIn('CLI_SPEC="${APOGRAPH_CLI_SPEC:-apograph-templates}"', launcher)
        self.assertIn('pipx run --spec "${CLI_SPEC}"', launcher)

    def test_compile_workflow_uses_tested_catalog_matrix_command(self):
        workflow = (
            catalog_module.REPO_ROOT / ".github" / "workflows" / "compile.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'python3 scripts/catalog.py ci-matrix >> "$GITHUB_OUTPUT"', workflow
        )
        self.assertNotIn("python3 -c", workflow)

    def test_workflows_pin_actions_and_test_the_release_artifact(self):
        workflow_dir = catalog_module.REPO_ROOT / ".github" / "workflows"
        compile_workflow = (workflow_dir / "compile.yml").read_text(encoding="utf-8")
        release_workflow = (workflow_dir / "release.yml").read_text(encoding="utf-8")
        cli_workflow = (workflow_dir / "publish-cli.yml").read_text(encoding="utf-8")

        action_ref = re.compile(r"^\s*-?\s*uses:\s*[^@\s]+@([0-9a-f]{40})(?:\s|$)", re.MULTILINE)
        for name, workflow in (
            ("compile.yml", compile_workflow),
            ("release.yml", release_workflow),
            ("publish-cli.yml", cli_workflow),
        ):
            uses_lines = [line for line in workflow.splitlines() if "uses:" in line]
            pinned_lines = action_ref.findall(workflow)
            self.assertEqual(len(pinned_lines), len(uses_lines), name)
            self.assertNotIn("|| true", workflow, name)

        self.assertIn("xu-cheng/texlive-action@", compile_workflow)
        self.assertIn("python3 -m pip wheel . --no-deps", compile_workflow)
        self.assertIn("scripts/pack.py --all --mode release", compile_workflow)
        self.assertIn("scripts/release.py assemble", compile_workflow)
        self.assertIn("Upload exact tested release candidate", compile_workflow)
        safe_directory_command = (
            'git config --global --add safe.directory "$GITHUB_WORKSPACE"'
        )
        self.assertEqual(
            [
                line.strip()
                for line in compile_workflow.splitlines()
                if "safe.directory" in line
            ],
            [safe_directory_command],
        )

        self.assertIn("workflow_dispatch:", release_workflow)
        self.assertIn("scripts/release.py validate-tag", release_workflow)
        self.assertIn("scripts/release.py assemble", release_workflow)
        self.assertIn("--ref-protected", release_workflow)
        self.assertIn("github.ref_protected", release_workflow)
        self.assertIn("scripts/release.py verify-published", release_workflow)
        self.assertIn("steps.release-metadata.outputs.prerelease", release_workflow)
        self.assertIn("Publish verified tag artifacts", release_workflow)
        self.assertIn("body_path: ${{ steps.release-metadata.outputs.release_notes_path }}", release_workflow)
        self.assertNotIn("generate_release_notes:", release_workflow)
        self.assertIn("environment:", cli_workflow)
        self.assertIn("name: pypi", cli_workflow)
        self.assertIn("id-token: write", cli_workflow)
        self.assertNotIn("PYPI_TOKEN", cli_workflow)
        self.assertIn("gh-action-pypi-publish@", cli_workflow)
        self.assertEqual(
            [
                line.strip()
                for line in release_workflow.splitlines()
                if "safe.directory" in line
            ],
            [safe_directory_command],
        )


if __name__ == "__main__":
    unittest.main()

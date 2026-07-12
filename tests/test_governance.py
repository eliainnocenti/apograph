import re
import unittest
from pathlib import Path

from scripts import catalog as catalog_module


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class GovernanceDocumentationTests(unittest.TestCase):
    def test_local_markdown_links_exist(self):
        markdown_files = [
            catalog_module.REPO_ROOT / "README.md",
            catalog_module.REPO_ROOT / "CONTRIBUTING.md",
            catalog_module.REPO_ROOT / "AGENTS.md",
            *sorted((catalog_module.REPO_ROOT / "docs").glob("*.md")),
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

    def test_implementation_plan_records_phase_progress(self):
        plan = (catalog_module.REPO_ROOT / "docs" / "IMPLEMENTATION_PLAN.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Phase 0 completed on 2026-07-12", plan)
        self.assertIn("Phase 1 completed on 2026-07-12", plan)
        self.assertIn("Phase 2 completed on 2026-07-12", plan)
        self.assertIn("Phase 3 completed on 2026-07-12", plan)
        self.assertIn("Execution:** completed on 2026-07-12", plan)


if __name__ == "__main__":
    unittest.main()

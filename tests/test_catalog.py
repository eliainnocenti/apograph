import copy
import json
import unittest

from scripts import catalog as catalog_module


class CatalogValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog_module.load_catalog()

    def errors_for(self, catalog):
        return catalog_module.validate_catalog(catalog, check_repository=False)

    def test_repository_catalog_is_valid(self):
        self.assertEqual(catalog_module.validate_catalog(self.catalog), [])

    def test_release_notes_match_collection_version(self):
        notes = (
            catalog_module.REPO_ROOT
            / catalog_module.release_notes_path(self.catalog)
        )
        self.assertTrue(notes.is_file())
        self.assertTrue(
            catalog_module.release_notes_heading_matches(
                self.catalog, notes.read_text(encoding="utf-8")
            )
        )
        self.assertFalse(
            catalog_module.release_notes_heading_matches(
                self.catalog, "# Apograph v999.0.0\n"
            )
        )

    def test_schema_and_standard_library_validator_fields_stay_aligned(self):
        schema = catalog_module.load_json(catalog_module.SCHEMA_PATH)
        mappings = [
            (schema["properties"], catalog_module.ROOT_FIELDS),
            (schema["properties"]["repository"]["properties"], catalog_module.REPOSITORY_FIELDS),
            (schema["$defs"]["template"]["properties"], catalog_module.TEMPLATE_FIELDS),
            (schema["$defs"]["institution"]["properties"], catalog_module.INSTITUTION_FIELDS),
            (schema["$defs"]["compatibility"]["properties"], catalog_module.COMPATIBILITY_FIELDS),
            (schema["$defs"]["entrypoint"]["properties"], catalog_module.ENTRYPOINT_FIELDS),
            (schema["$defs"]["license"]["properties"], catalog_module.LICENSE_FIELDS),
            (schema["$defs"]["upstream"]["properties"], catalog_module.UPSTREAM_FIELDS),
            (schema["$defs"]["upstreamSource"]["properties"], catalog_module.UPSTREAM_SOURCE_FIELDS),
            (schema["$defs"]["asset"]["properties"], catalog_module.ASSET_FIELDS),
            (schema["$defs"]["maintainer"]["properties"], catalog_module.MAINTAINER_FIELDS),
        ]
        for properties, expected_fields in mappings:
            self.assertEqual(set(properties), expected_fields)

    def test_duplicate_template_id_is_rejected(self):
        candidate = copy.deepcopy(self.catalog)
        candidate["templates"][1]["id"] = candidate["templates"][0]["id"]

        errors = self.errors_for(candidate)

        self.assertTrue(any("duplicate template ID" in error for error in errors), errors)

    def test_unsafe_source_path_is_rejected(self):
        candidate = copy.deepcopy(self.catalog)
        candidate["templates"][0]["source_dir"] = "../outside"

        errors = self.errors_for(candidate)

        self.assertTrue(any("may not contain '..'" in error for error in errors), errors)

    def test_source_path_matches_flat_purpose_variant_format_layout(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["templates"][0]["source_dir"] = "templates/thesis/polito/latex"

        errors = catalog_module.validate_catalog(catalog, check_repository=False)

        self.assertTrue(
            any("expected templates/thesis/polito-latex" in error for error in errors),
            errors,
        )

    def test_public_template_requires_starter_and_verified_license(self):
        candidate = copy.deepcopy(self.catalog)
        template = next(
            item for item in candidate["templates"]
            if item["id"] == "presentation-beamer-polito-latex"
        )
        template["status"] = "beta"
        template["entrypoints"][0]["role"] = "showcase"
        template["license"]["status"] = "review-required"
        template["compatibility"]["overleaf"] = "untested"

        errors = self.errors_for(candidate)

        self.assertTrue(any("exactly one starter" in error for error in errors), errors)
        self.assertTrue(any("verified license expression" in error for error in errors), errors)
        self.assertTrue(any("Overleaf compatibility" in error for error in errors), errors)

    def test_fetched_asset_requires_url_and_checksum(self):
        candidate = copy.deepcopy(self.catalog)
        asset = candidate["templates"][0]["assets"][0]
        asset["mode"] = "fetched"

        errors = self.errors_for(candidate)

        self.assertTrue(any("fetched assets require source_url" in error for error in errors), errors)
        self.assertTrue(any("fetched assets require sha256" in error for error in errors), errors)

    def test_user_provided_asset_rejects_automated_download_url(self):
        candidate = copy.deepcopy(self.catalog)
        candidate["templates"][0]["assets"][0]["source_url"] = "https://example.edu/logo.pdf"

        errors = self.errors_for(candidate)

        self.assertTrue(any("may not use source_url" in error for error in errors), errors)

    def test_invalid_nested_types_report_errors_instead_of_crashing(self):
        candidate = copy.deepcopy(self.catalog)
        candidate["templates"][0]["compatibility"] = []
        candidate["templates"][0]["shared_deps"] = [{}]
        candidate["templates"][0]["tags"] = [{}]

        errors = self.errors_for(candidate)

        self.assertTrue(any("compatibility: expected an object" in error for error in errors), errors)
        self.assertTrue(any("shared_deps[0]" in error for error in errors), errors)
        self.assertTrue(any("tags[0]" in error for error in errors), errors)

    def test_public_listing_separates_beta_from_drafts(self):
        rendered = catalog_module.render_public_listing(self.catalog)

        self.assertIn("PoliTo Beamer Presentation", rendered)
        self.assertIn("| beta | `presentation-beamer-polito-latex` |", rendered)
        self.assertIn(
            "/releases/download/v0.1.0/presentation-beamer-polito-latex.zip",
            rendered,
        )
        self.assertIn("https://www.overleaf.com/docs?snip_uri=", rendered)
        self.assertIn("Draft inventory", rendered)
        public_ids = [item["id"] for item in catalog_module.public_templates(self.catalog)]
        self.assertEqual(public_ids, ["presentation-beamer-polito-latex"])
        self.assertNotIn("thesis-polito-latex", public_ids)

    def test_release_urls_are_versioned_and_catalog_backed(self):
        template = catalog_module.public_templates(self.catalog)[0]
        urls = catalog_module.template_release_urls(self.catalog, template)

        self.assertEqual(catalog_module.release_tag(self.catalog), "v0.1.0")
        self.assertEqual(
            urls["download"],
            "https://github.com/eliainnocenti/apograph/releases/download/v0.1.0/"
            "presentation-beamer-polito-latex.zip",
        )
        self.assertIn("snip_uri=https%3A%2F%2Fgithub.com%2F", urls["overleaf"])

    def test_ci_matrix_contains_only_public_publishable_entrypoints(self):
        matrices = catalog_module.build_ci_matrices(self.catalog)

        self.assertEqual(matrices["typst"], {"include": []})
        latex_entries = matrices["latex"]["include"]
        self.assertEqual(
            [entry["id"] for entry in latex_entries],
            [
                "presentation-beamer-polito-latex--starter",
                "presentation-beamer-polito-latex--showcase",
            ],
        )
        self.assertTrue(
            all(
                entry["template_id"] == "presentation-beamer-polito-latex"
                for entry in latex_entries
            )
        )
        self.assertTrue(
            all(entry["source_dir"].endswith("-latex") for entry in latex_entries)
        )

    def test_ci_matrix_output_is_github_output_compatible(self):
        output = catalog_module.render_ci_outputs(self.catalog)
        values = dict(line.split("=", 1) for line in output.splitlines())

        self.assertEqual(values["has_latex"], "true")
        self.assertEqual(values["has_typst"], "false")
        self.assertEqual(
            json.loads(values["latex_matrix"]),
            catalog_module.build_ci_matrices(self.catalog)["latex"],
        )
        self.assertEqual(json.loads(values["typst_matrix"]), {"include": []})

    def test_readme_generation_is_idempotent(self):
        current = catalog_module.README_PATH.read_text(encoding="utf-8")
        once = catalog_module.generated_readme(self.catalog, current)
        twice = catalog_module.generated_readme(self.catalog, once)

        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()

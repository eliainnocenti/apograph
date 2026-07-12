import copy
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
        self.assertIn("Draft inventory", rendered)
        public_ids = [item["id"] for item in catalog_module.public_templates(self.catalog)]
        self.assertEqual(public_ids, ["presentation-beamer-polito-latex"])
        self.assertNotIn("thesis-polito-msc-latex", public_ids)

    def test_readme_generation_is_idempotent(self):
        current = catalog_module.README_PATH.read_text(encoding="utf-8")
        once = catalog_module.generated_readme(self.catalog, current)
        twice = catalog_module.generated_readme(self.catalog, once)

        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()

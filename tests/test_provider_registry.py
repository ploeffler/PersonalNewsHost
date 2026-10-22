"""Run with: python3 -m unittest discover -s tests"""
import unittest
from scripts.provider_registry import plan, require_executable_version


class ProviderRegistryTests(unittest.TestCase):
    def test_default_is_free(self):
        result = plan({})
        self.assertFalse(result["paid_requested"])
        self.assertTrue(result["ready"])

    def test_paid_requires_consent_and_budgets(self):
        result = plan({"advanced_services": {"voice_provider": "openai"}})
        self.assertTrue(result["paid_requested"])
        self.assertFalse(result["ready"])
        self.assertEqual(len(result["blockers"]), 4)

    def test_even_consented_paid_is_blocked(self):
        config = {"production_version": "2.0", "advanced_services": {
            "voice_provider": "openai", "allow_paid": True,
            "max_per_video_eur": 1, "max_per_month_eur": 10}}
        self.assertEqual(len(plan(config)["blockers"]), 2)
        with self.assertRaises(RuntimeError):
            require_executable_version(config)

    def test_invalid_provider_and_budget_rejected(self):
        for config in (
            {"advanced_services": {"voice_provider": "unknown"}},
            {"advanced_services": {"max_per_month_eur": -1}},
            {"advanced_services": {"max_per_video_eur": "NaN"}},
        ):
            with self.assertRaises(ValueError):
                plan(config)

    def test_processing_location_validation(self):
        for advanced in (
            {"processing_region": "moon"},
            {"processing_region": "eu", "processing_country": "US"},
            {"processing_country": "ZZ"},
            {"require_verified_region": "yes"},
        ):
            with self.assertRaises(ValueError):
                plan({"advanced_services": advanced})
        location = plan({"advanced_services": {
            "processing_region": "eu", "processing_country": "AT",
            "require_verified_region": True}})["processing_location"]
        self.assertEqual(location["country"], "AT")

    def test_unverified_provider_residency(self):
        strict = plan({"advanced_services": {"voice_provider": "openai", "processing_region": "eu"}})
        self.assertFalse(strict["residency"]["voice"]["allowed"])
        self.assertIsNone(strict["residency"]["voice"]["evidence_url"])
        relaxed = plan({"advanced_services": {"voice_provider": "openai", "require_verified_region": False}})
        self.assertTrue(relaxed["residency"]["voice"]["allowed"])
        self.assertFalse(relaxed["ready"])

    def test_legacy_version_remains_valid(self):
        require_executable_version({})
        require_executable_version({"production_version": "1.0"})
        with self.assertRaises(ValueError):
            require_executable_version({"production_version": "3.0"})


if __name__ == "__main__":
    unittest.main()

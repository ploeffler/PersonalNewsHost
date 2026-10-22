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
        self.assertEqual(len(result["blockers"]), 3)

    def test_even_consented_paid_is_blocked(self):
        config = {"production_version": "2.0", "advanced_services": {
            "voice_provider": "openai", "allow_paid": True,
            "max_per_video_eur": 1, "max_per_month_eur": 10}}
        self.assertEqual(len(plan(config)["blockers"]), 1)
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

    def test_legacy_version_remains_valid(self):
        require_executable_version({})
        require_executable_version({"production_version": "1.0"})
        with self.assertRaises(ValueError):
            require_executable_version({"production_version": "3.0"})


if __name__ == "__main__":
    unittest.main()

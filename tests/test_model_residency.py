import unittest
from scripts.model_residency import validate_candidate


class ModelResidencyTests(unittest.TestCase):
    def test_empty_candidate_is_not_approved(self):
        result = validate_candidate({}, {"eu-central-1"})
        self.assertFalse(result["documentation_complete"])
        self.assertFalse(result["approved"])
        self.assertIn("model_id", result["missing"])

    def test_destination_outside_allowed_regions(self):
        candidate = {
            "provider": "example", "service": "news", "model_id": "test",
            "deployment_type": "geographic", "source_region": "eu-central-1",
            "destination_regions": ["eu-central-1", "us-east-1"],
            "processing_scope": "EU", "data_retention_policy": "reviewed",
            "subprocessors_reviewed": True, "evidence_url": "https://example.org/evidence",
            "checked_on": "2026-10-01",
        }
        result = validate_candidate(candidate, {"eu-central-1"})
        self.assertIn("destination_regions_outside_policy", result["missing"])
        self.assertFalse(result["approved"])

    def test_complete_documentation_still_needs_independent_approval(self):
        candidate = {
            "provider": "example", "service": "news", "model_id": "test",
            "deployment_type": "geographic", "source_region": "eu-central-1",
            "destination_regions": ["eu-central-1"], "processing_scope": "EU",
            "data_retention_policy": "reviewed", "subprocessors_reviewed": True,
            "evidence_url": "https://example.org/evidence", "checked_on": "2026-10-01",
        }
        result = validate_candidate(candidate, {"eu-central-1"})
        self.assertTrue(result["documentation_complete"])
        self.assertFalse(result["approved"])

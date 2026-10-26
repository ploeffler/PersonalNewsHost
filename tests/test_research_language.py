import unittest
from scripts.research_language import normalize_language, research_terms, source_metadata, event_candidate


class ResearchLanguageTests(unittest.TestCase):
    def test_language_codes(self):
        self.assertEqual(normalize_language("en-US"), "en")
        self.assertEqual(normalize_language("de_AT"), "de")
        self.assertEqual(normalize_language("fr"), "de")

    def test_terms_preserve_original_headline(self):
        self.assertEqual(research_terms("Example headline", "en"),
                         {"query": "Example headline", "language": "en"})

    def test_bilingual_event_candidate_requires_review(self):
        result = event_candidate("Ukraine Präsident Wahl 2026", "Ukraine president election 2026")
        self.assertTrue(result["candidate"])
        self.assertTrue(result["review_required"])
        self.assertIn("election", result["shared_terms"])

    def test_generic_headlines_do_not_match(self):
        result = event_candidate("New government announcement", "New climate report")
        self.assertFalse(result["candidate"])

    def test_source_metadata(self):
        self.assertEqual(source_metadata("https://example.org/a", "en")["publisher"], "example.org")


if __name__ == "__main__":
    unittest.main()

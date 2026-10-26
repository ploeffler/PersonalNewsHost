import unittest
from scripts.research_language import normalize_language, research_terms, source_metadata


class ResearchLanguageTests(unittest.TestCase):
    def test_language_codes(self):
        self.assertEqual(normalize_language("en-US"), "en")
        self.assertEqual(normalize_language("de_AT"), "de")
        self.assertEqual(normalize_language("fr"), "de")

    def test_terms_preserve_original_headline(self):
        self.assertEqual(research_terms("Example headline", "en"),
                         {"query": "Example headline", "language": "en"})

    def test_source_metadata(self):
        self.assertEqual(source_metadata("https://example.org/a", "en")["publisher"], "example.org")


if __name__ == "__main__":
    unittest.main()

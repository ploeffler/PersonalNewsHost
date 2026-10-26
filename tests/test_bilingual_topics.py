import unittest

from scripts.analyze_topics import bilingual_candidates, parse_feed


class BilingualTopicsTests(unittest.TestCase):
    def test_cross_language_candidate(self):
        items = [
            {"title": "Ukraine Präsident Wahl 2026", "link": "https://de.example/a",
             "source": "de.example", "language": "de"},
            {"title": "Ukraine president election 2026", "link": "https://en.example/b",
             "source": "en.example", "language": "en"},
        ]
        result = bilingual_candidates(items)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["review_required"])
        self.assertFalse(result[0]["independent_verification"])

    def test_same_language_and_unknown_not_cross_language(self):
        items = [
            {"title": "Ukraine Präsident Wahl 2026", "source": "a", "language": "de"},
            {"title": "Ukraine Präsident Wahl 2026", "source": "b", "language": "de"},
            {"title": "Ukraine president election 2026", "source": "c", "language": "unknown"},
        ]
        self.assertEqual(bilingual_candidates(items), [])

    def test_rss_language_metadata(self):
        xml = b'<rss><channel><language>en-US</language><item><title>Test story</title></item></channel></rss>'
        items = parse_feed(xml, "https://example.com/feed")
        self.assertEqual(items[0]["language"], "en")

    def test_unknown_feed_language_is_not_assumed(self):
        xml = b'<rss><channel><item><title>Test story</title></item></channel></rss>'
        items = parse_feed(xml, "https://example.com/feed")
        self.assertEqual(items[0]["language"], "unknown")


if __name__ == "__main__":
    unittest.main()

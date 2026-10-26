import unittest

from scripts.build_broadcast_plan import build


class BilingualBroadcastPlanTests(unittest.TestCase):
    def setUp(self):
        self.config = {"max_items": 1}
        self.base = {
            "topics": [{"topic": "Test", "articles": [
                {"title": "Deutsche Meldung", "description": "Beschreibung",
                 "link": "https://de.example/1", "source": "de.example"}]}],
            "bilingual_candidates": [{
                "first": {"title": "Ukraine Präsident Wahl 2026",
                          "url": "https://de.example/2", "source": "de.example", "language": "de"},
                "second": {"title": "Ukraine president election 2026",
                           "url": "https://en.example/2", "source": "en.example", "language": "en"},
                "score": 0.8, "shared_terms": ["ukraine", "election"]
            }]
        }

    def test_bilingual_candidate_added_to_review_not_narration(self):
        plan = build(self.base, self.config)
        self.assertEqual(plan["bilingual_review_count"], 1)
        self.assertEqual(plan["status"], "experimental_not_approved_for_publication")
        self.assertFalse(plan["rendering"]["publish_enabled"])
        candidate = plan["review_queue"][0]
        self.assertEqual(candidate["kind"], "cross_language_event_candidate")
        self.assertTrue(candidate["review_required"])
        self.assertFalse(candidate["independent_verification"])
        self.assertFalse(candidate["publication_approved"])
        story = next(segment for segment in plan["segments"] if segment["kind"] == "story")
        self.assertEqual(story["headline"], "Deutsche Meldung")
        self.assertNotIn("Ukraine", story["speech_text"])

    def test_no_bilingual_candidates_backward_compatible(self):
        analysis = dict(self.base, bilingual_candidates=[])
        plan = build(analysis, self.config)
        self.assertEqual(plan["bilingual_review_count"], 0)
        self.assertEqual(plan["review_queue"], [])

    def test_invalid_candidate_does_not_enter_queue(self):
        analysis = dict(self.base, bilingual_candidates=[
            {"first": {"language": "de"}, "second": {"language": "de"}},
            {"first": None, "second": {"language": "en"}}
        ])
        self.assertEqual(build(analysis, self.config)["bilingual_review_count"], 0)


if __name__ == "__main__":
    unittest.main()

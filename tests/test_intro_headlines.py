import unittest

from scripts.generate import intro_headline_slots


class IntroHeadlineTests(unittest.TestCase):
    def test_all_topics_cover_measured_intro_once_in_order(self):
        titles = ['Erstes Thema', 'Zweites Thema', 'Drittes Thema']
        slots = intro_headline_slots(titles, 7.5)
        self.assertEqual(slots, [('Erstes Thema', 0, 2.5),
                                 ('Zweites Thema', 2.5, 5),
                                 ('Drittes Thema', 5, 7.5)])

    def test_single_headline_uses_whole_intro(self):
        self.assertEqual(intro_headline_slots(['Thema'], 3.125), [('Thema', 0, 3.125)])

    def test_no_topics_or_no_intro(self):
        self.assertEqual(intro_headline_slots([], 10), [])
        self.assertEqual(intro_headline_slots(['Thema'], 0), [])
        self.assertEqual(intro_headline_slots(['Thema'], -1), [])

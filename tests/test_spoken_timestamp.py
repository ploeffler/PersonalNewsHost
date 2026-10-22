"""Regression tests for natural German date and time announcements."""
import datetime as dt
import unittest
from zoneinfo import ZoneInfo
from scripts.generate import spoken_timestamp

class SpokenTimestampTests(unittest.TestCase):
    def test_october_example(self):
        date = dt.datetime(2026, 10, 22, 21, 33, tzinfo=ZoneInfo("Europe/Vienna"))
        self.assertEqual(spoken_timestamp(date), "Heute ist zweiundzwanzigsten Oktober. Es ist einundzwanzig Uhr dreiunddreißig. Nachrichten aus dem Jahr zweitausendsechsundzwanzig.")

    def test_midnight(self):
        date = dt.datetime(2026, 1, 1, 0, 0)
        self.assertEqual(spoken_timestamp(date), "Heute ist ersten Jänner. Es ist null Uhr. Nachrichten aus dem Jahr zweitausendsechsundzwanzig.")

    def test_twentieth(self):
        date = dt.datetime(2026, 4, 20, 8, 5)
        self.assertEqual(spoken_timestamp(date), "Heute ist zwanzigsten April. Es ist acht Uhr fünf. Nachrichten aus dem Jahr zweitausendsechsundzwanzig.")

if __name__ == "__main__":
    unittest.main()

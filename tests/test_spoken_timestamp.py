"""Regression tests for natural German date and time announcements."""
import datetime as dt
import unittest
from zoneinfo import ZoneInfo
from scripts.generate import spoken_timestamp

class SpokenTimestampTests(unittest.TestCase):
    def test_october_example(self):
        date = dt.datetime(2026, 10, 22, 21, 33, tzinfo=ZoneInfo("Europe/Vienna"))
        self.assertEqual(spoken_timestamp(date), "Die Nachrichten vom zweiundzwanzigsten Oktober zweitausendsechsundzwanzig, um einundzwanzig Uhr dreiunddreißig.")

    def test_midnight(self):
        date = dt.datetime(2026, 1, 1, 0, 0)
        self.assertEqual(spoken_timestamp(date), "Die Nachrichten vom ersten Jänner zweitausendsechsundzwanzig, um null Uhr.")

    def test_twentieth(self):
        date = dt.datetime(2026, 4, 20, 8, 5)
        self.assertEqual(spoken_timestamp(date), "Die Nachrichten vom zwanzigsten April zweitausendsechsundzwanzig, um acht Uhr fünf.")

if __name__ == "__main__":
    unittest.main()

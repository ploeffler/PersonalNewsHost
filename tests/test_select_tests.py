import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import select_tests  # noqa: E402


class SelectTestsTest(unittest.TestCase):
    def test_nur_doku_keine_tests(self):
        mode, tests, ffmpeg, browser = select_tests.select(['README.md'])
        self.assertEqual((mode, tests, ffmpeg, browser), ('none', [], False, False))

    def test_geaenderter_test_laeuft_selbst(self):
        mode, tests, _, _ = select_tests.select(['tests/test_schedule.py'])
        self.assertEqual((mode, tests), ('subset', ['test_schedule']))

    def test_skript_zieht_seine_tests(self):
        mode, tests, _, _ = select_tests.select(['scripts/check_schedule.py'])
        self.assertEqual(mode, 'subset')
        self.assertIn('test_schedule', tests)

    def test_workflow_und_loeschung_voll(self):
        self.assertEqual(select_tests.select(['.github/workflows/news.yml'])[0], 'full')
        self.assertEqual(select_tests.select(['README.md'], removed=['scripts/x.py'])[0], 'full')

    def test_seite_unter_docs_startet_browsertests(self):
        _, _, _, browser = select_tests.select(['docs/news-list.js'])
        self.assertTrue(browser)
        self.assertFalse(select_tests.select(['scripts/check_schedule.py'])[3])

    def test_unbekannte_datei_voll(self):
        self.assertEqual(select_tests.select(['irgendwas.yml'])[0], 'full')


if __name__ == '__main__':
    unittest.main()

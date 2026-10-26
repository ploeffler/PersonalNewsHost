"""Regression tests for locally extracted article text."""
import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from scripts.generate import extract_article_text


class RdrrExtractionTests(unittest.TestCase):
    @patch("scripts.generate.subprocess.run")
    def test_extracts_article_text(self, run):
        article = "Dies ist ein ausführlicher Nachrichtenartikel. " * 10
        run.return_value = SimpleNamespace(stdout=json.dumps({"content": article}))
        self.assertIn("Nachrichtenartikel", extract_article_text("https://example.org/story"))
        run.assert_called_once()

    @patch("scripts.generate.subprocess.run")
    def test_falls_back_on_failed_extraction(self, run):
        run.side_effect = FileNotFoundError("rdrr missing")
        self.assertIsNone(extract_article_text("https://example.org/story"))

    def test_rejects_invalid_url(self):
        self.assertIsNone(extract_article_text("file:///etc/passwd"))


if __name__ == "__main__":
    unittest.main()

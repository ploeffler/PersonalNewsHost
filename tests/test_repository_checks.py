from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import check_repository as check


class RepositoryCheckTests(unittest.TestCase):
    def test_secret_scan_detects_without_exposing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'test.txt';p.write_text('ghp_'+'A'*35)
            with patch.object(check,'ROOT',root):
                errors=check.secrets([p])
            self.assertEqual(len(errors),1)
            self.assertNotIn('A'*35,errors[0])

    def test_missing_links_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'doc.md';p.write_text('[missing](not-here.md) [web](https://example.org)')
            with patch.object(check,'ROOT',root):self.assertEqual(len(check.links([p])),1)

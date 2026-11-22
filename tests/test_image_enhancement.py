import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import generate  # noqa: E402
from PIL import Image  # noqa: E402


class ImageEnhancementTest(unittest.TestCase):
    def _image(self, tmp, size=(400, 300)):
        path = Path(tmp) / 'bild.jpg'
        Image.new('RGB', size, (120, 90, 60)).save(path)
        return path

    def test_alter_ai_modus_nutzt_einfache_vergroesserung(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, kind = generate.improve_news_image(self._image(tmp), {'enhancement': 'ai'})
            self.assertEqual(kind, 'conservative')
            with Image.open(out) as im:
                self.assertEqual(im.size, (800, 600))

    def test_standard_ist_balanced(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(generate.improve_news_image(self._image(tmp), {})[1], 'conservative')

    def test_off_laesst_bild_unveraendert(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._image(tmp)
            self.assertEqual(generate.improve_news_image(src, {'enhancement': 'off'}), (src, 'original'))


if __name__ == '__main__':
    unittest.main()

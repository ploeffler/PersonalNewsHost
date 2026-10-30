import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('short_updates', Path(__file__).resolve().parents[1] / 'scripts/short_updates.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ShortUpdatesTest(unittest.TestCase):
    now = 2000000
    def candidate(self, **changes):
        return dict(title='Eilmeldung: Parlament beschließt Reform', description='Das Parlament hat die Reform beschlossen. Sie gilt ab morgen.', url='https://example.org/1', source='example.org', published_at=self.now - 120, **changes)

    def test_fresh_significant_item_and_repeat(self):
        c = self.candidate()
        state = m.select_updates([c], {}, self.now)
        self.assertEqual(len(state['updates']), 1)
        c['title'] += ' – aktualisiert'
        c['published_at'] = self.now + 900
        self.assertEqual(len(m.select_updates([c], state, self.now + 1000)['updates']), 1)

    def test_stale_missing_future_and_generic(self):
        for timestamp in [0, self.now - 3601, self.now + 1]:
            c = self.candidate(); c['published_at'] = timestamp
            self.assertFalse(m.select_updates([c], {}, self.now)['updates'])
        c = self.candidate(); c['title'] = 'Ein Hintergrundbericht zur Reform'
        self.assertFalse(m.select_updates([c], {}, self.now)['updates'])

    def test_retention_exact_boundary_and_count(self):
        updates = [dict(self.candidate(), id=str(i), created_at=self.now-i*100) for i in range(8)]
        updates.append(dict(self.candidate(), created_at=self.now-86400))
        result = m.select_updates([], {'updates': updates}, self.now)['updates']
        self.assertEqual(len(result), 5)
        self.assertEqual([u['id'] for u in result], ['0','1','2','3','4'])
        self.assertFalse(m.select_updates([], {'updates': updates}, self.now+86400)['updates'])

    def test_cross_source_duplicate_and_rate_limit(self):
        c = self.candidate()
        state = m.select_updates([c], {}, self.now)
        c['url'] = 'https://other.org/new'
        self.assertEqual(len(m.select_updates([c], state, self.now+901)['updates']), 1)
        c['url'] = 'https://other.org/2'; c['title'] = 'Breaking: President resigns after election defeat'
        self.assertEqual(len(m.select_updates([c], state, self.now+60)['updates']), 1)

if __name__ == '__main__':
    unittest.main()

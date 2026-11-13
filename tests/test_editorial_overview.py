import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('editorial_overview', ROOT / 'scripts/editorial_overview.py')
o = importlib.util.module_from_spec(spec); spec.loader.exec_module(o)
P = o.pipeline()
NOW = 1_800_000_000


def article(i, title, text, host, minutes_ago=30):
    t = NOW - minutes_ago * 60
    return {'id': i, 'title': title, 'text': text, 'url': f'https://www.{host}/{i}', 'published_at': t,
            'first_seen_at': t, 'content_kind': 'news'}


T = 'Zugunglück in München: Zehn Menschen verletzt'
A = article('a', T, 'Bei dem Zugunglück wurden zehn Menschen verletzt. Die Polizei ermittelt.', 'orf.at')
B = article('b', T, 'Die Bahnstrecke bleibt bis zum Abend gesperrt. Ersatzbusse fahren.', 'krone.at')
C = article('c', 'Neue Brücke über die Mur eröffnet', 'Die neue Brücke wurde am Morgen eröffnet. Sie ist 80 Meter lang.', 'orf.at')
D = article('d', 'Hauseinsturz in Linz', 'Beim Hauseinsturz in Linz gab es 2 Tote. Die Feuerwehr sucht weiter.', 'orf.at')
E = article('e', 'Hauseinsturz in Linz', 'Beim Hauseinsturz in Linz gab es 8 Tote. Die Polizei ermittelt.', 'krone.at')


class EditorialOverviewTest(unittest.TestCase):
    def build(self, broadcast_urls=(), events=()):
        broadcasts = {'broadcasts': [{'created_at': NOW - 600, 'title': 'Nachrichten',
                                      'sources': [{'url': u} for u in broadcast_urls]}]}
        return o.build({'articles': [A, B, C, D, E], 'feeds': []}, broadcasts, {'events': list(events)}, {}, NOW, P)

    def test_groups_with_summary_publishers_and_broadcast_flag(self):
        data = self.build(broadcast_urls=['https://orf.at/a?ref=rss'])
        first = data['events'][0]
        self.assertEqual(first['headline'], T)
        self.assertEqual(first['status'], 'sendung')
        self.assertTrue(first['status_label'].startswith('In der Sendung'))
        self.assertEqual(first['publishers'], ['orf.at', 'krone.at'])
        self.assertEqual(first['summary'], 'Bei dem Zugunglück wurden zehn Menschen verletzt. Die Bahnstrecke bleibt bis zum Abend gesperrt.')
        bridge = next(x for x in data['events'] if x['headline'].startswith('Neue Brücke'))
        self.assertEqual(bridge['status'], 'nicht')
        self.assertEqual(bridge['summary'], 'Die neue Brücke wurde am Morgen eröffnet. Sie ist 80 Meter lang.')

    def test_held_events_show_reason_and_breaking_badge(self):
        data = self.build(events=[{'created_at': NOW - 300, 'article_ids': ['c']}])
        held = next(x for x in data['events'] if x['headline'].startswith('Hauseinsturz'))
        self.assertEqual(held['status'], 'zurueckgestellt')
        self.assertIn('abweichende Zahlen', held['status_label'])
        bridge = next(x for x in data['events'] if x['headline'].startswith('Neue Brücke'))
        self.assertEqual(bridge['breaking_at'], NOW - 300)
        self.assertEqual(data['events'][-1]['status'], 'zurueckgestellt')

    def test_html_is_escaped_and_lists_multi_source_events_first(self):
        evil = article('x', '<script>alert(1)</script> Wahl', 'Text <b>fett</b>. Zweiter Satz.', 'derstandard.at')
        data = o.build({'articles': [A, B, evil], 'feeds': []}, {}, {}, {}, NOW, P)
        page = o.render(data)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertLess(page.index(T), page.index('Einzelmeldungen'))
        self.assertIn('Noch keine Sendung', page)


if __name__ == '__main__':
    unittest.main()

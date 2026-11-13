import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('short_updates', ROOT / 'scripts/short_updates.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
P = m.load_pipeline()
NOW = 1_800_000_000  # Fri 15.01.2027 08:00 UTC


def article(i, title, text, host, minutes_ago=10, feed=None):
    t = NOW - minutes_ago * 60
    return {'id': i, 'title': title, 'text': text, 'url': f'https://{host}/{i}', 'published_at': t,
            'first_seen_at': t, 'feed_urls': [feed or f'https://{host}/rss'], 'content_kind': 'news'}


def store(*articles):
    return {'articles': list(articles), 'feeds': []}


def run(*articles, state=None, now=NOW, **settings):
    return m.select_breaking(store(*articles), state or {}, now, m.settings_from({'short_updates': settings}), P)


TITLE = 'Hauseinsturz in New York: Mindestens acht Tote'
A = article('a', TITLE, 'In New York ist ein Wohnhaus eingestürzt. Mindestens acht Menschen kamen ums Leben.', 'orf.at')
B = article('b', TITLE, 'Ein Wohnhaus in New York ist eingestürzt. Die Feuerwehr sucht nach Verschütteten.', 'derstandard.at')


class BreakingDetectionTest(unittest.TestCase):
    def test_serious_event_confirmed_by_two_publishers(self):
        updates = run(A, B)['updates']
        self.assertEqual(len(updates), 1)
        u = updates[0]
        self.assertEqual((u['reason'], u['publishers']), ('Schwere', 2))
        self.assertEqual(u['sources'], ['derstandard.at', 'orf.at'])
        self.assertIn('Quellen: ', u['text'])
        for key in ('id', 'title', 'url', 'source', 'published_at', 'created_at'):
            self.assertIn(key, u)

    def test_single_publisher_is_not_enough(self):
        self.assertFalse(run(A)['updates'])

    def test_explicit_marker_needs_only_one_publisher(self):
        e = article('e', 'Eilmeldung: Nationalrat beschließt Budget', 'Der Nationalrat hat das Budget beschlossen.', 'orf.at')
        self.assertEqual(run(e)['updates'][0]['reason'], 'Kennzeichnung')
        f = article('f', 'Nationalrat beschließt Budget', 'Der Nationalrat hat das Budget beschlossen.', 'sz.de', feed='https://sz.de/eil')
        self.assertEqual(run(f, breaking_feeds=['https://sz.de/eil'])['updates'][0]['reason'], 'Kennzeichnung')

    def test_sports_wins_and_closures_are_not_breaking(self):
        items = [article('s1', 'Salzburg gewinnt Torshow bei Sturm', 'Salzburg gewann 4:3.', 'orf.at'),
                 article('s2', 'Salzburg gewinnt Torshow bei Sturm', 'Salzburg siegte mit 4:3.', 'krone.at'),
                 article('w1', 'Weg zum Wasserfall gesperrt', 'Der Weg ist bis auf Weiteres gesperrt.', 'orf.at'),
                 article('w2', 'Weg zum Wasserfall gesperrt', 'Der Wanderweg bleibt gesperrt.', 'krone.at')]
        self.assertFalse(run(*items)['updates'])

    def test_dead_animals_are_not_deaths(self):
        x = article('x', 'Strafantrag nach Fund von 400 toten Schweinen', 'Im Stall wurden 400 tote Schweine gefunden.', 'orf.at')
        y = article('y', 'Strafantrag nach Fund von 400 toten Schweinen', 'Die Behörde fand 400 tote Schweine.', 'derstandard.at')
        self.assertFalse(run(x, y)['updates'])
        self.assertFalse(m.serious('Zwei Tauben getötet'))
        self.assertTrue(m.serious('Mindestens zwei Tote bei Hauseinsturz'))

    def test_top_office_change(self):
        x = article('x', 'Nvidia-Chef Huang tritt zurück', 'Jensen Huang tritt als Chef von Nvidia zurück.', 'orf.at')
        y = article('y', 'Nvidia-Chef Huang tritt zurück', 'Der Nvidia-Chef Jensen Huang ist zurückgetreten.', 'krone.at')
        self.assertEqual(run(x, y)['updates'][0]['reason'], 'Spitzenamt')

    def test_austria_rule_needs_urgency_and_can_be_disabled(self):
        x = article('x', 'Russland droht Wien mit Vergeltung', 'Russland droht Österreich wegen der Ausweisung von Diplomaten.', 'orf.at')
        y = article('y', 'Russland droht Wien mit Vergeltung', 'Moskau droht Wien nach Ausweisungen mit Konsequenzen.', 'derstandard.at')
        self.assertEqual(run(x, y)['updates'][0]['reason'], 'Österreich')
        self.assertFalse(run(x, y, austria_rule=False)['updates'])
        o = article('o', 'Zuwanderung nach Österreich gesunken', 'Laut OECD ist die Zuwanderung nach Österreich gesunken.', 'orf.at')
        q = article('q', 'Zuwanderung nach Österreich gesunken', 'Die OECD meldet weniger Zuwanderung nach Österreich.', 'krone.at')
        self.assertFalse(run(o, q)['updates'])

    def test_old_or_stale_events_are_ignored(self):
        old = [dict(A, published_at=NOW - 4 * 3600, first_seen_at=NOW - 4 * 3600), dict(B)]
        self.assertFalse(run(*old)['updates'])           # story started more than 3 h ago
        stale = [dict(x, published_at=NOW - 2 * 3600, first_seen_at=NOW - 2 * 3600) for x in (A, B)]
        self.assertFalse(run(*stale)['updates'])         # nothing new in the last hour

    def test_same_event_only_once_and_daily_limit(self):
        state = run(A, B)
        c = article('c', TITLE, 'Rettungskräfte suchen weiter nach Verschütteten in New York.', 'krone.at', 1)
        again = m.select_breaking(store(A, B, c), state, NOW + 900, m.settings_from({}), P)
        self.assertEqual(len(again['updates']), 1)
        limited = run(A, B, max_per_day=0)
        self.assertFalse(limited['updates'])

    def test_retention(self):
        updates = [{'id': str(i), 'title': f'Meldung {i}', 'created_at': NOW - i * 100} for i in range(8)]
        updates.append({'id': 'old', 'title': 'Alt', 'created_at': NOW - 86400})
        result = run(state={'updates': updates})['updates']
        self.assertEqual([u['id'] for u in result], ['0', '1', '2', '3', '4'])

    def test_media_attempts_are_bounded(self):
        self.assertTrue(m.needs_media([{'id': 'a'}]))
        self.assertFalse(m.needs_media([{'id': 'a', 'media_attempts': 2}]))
        self.assertFalse(m.needs_media([{'id': 'a', 'video': 'x.mp4'}]))


if __name__ == '__main__':
    unittest.main()

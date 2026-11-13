import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('llm_pair_judge', ROOT / 'scripts/llm_pair_judge.py')
j = importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
P = j.pipeline()
NOW = 1_800_000_000


def article(i, title, host, text='', minutes_ago=10):
    t = NOW - minutes_ago * 60
    return {'id': i, 'title': title, 'text': text or title + '.', 'url': f'https://{host}/{i}',
            'published_at': t, 'first_seen_at': t, 'content_kind': 'news'}


HUANG = article('a', 'Nvidia-Chef Huang legt alle Ämter zurück', 'orf.at', 'Jensen Huang legt alle Ämter bei Nvidia zurück.')
WHY = article('b', 'Spionage und Affären: Warum Nvidias CEO Jensen Huang zurückgetreten ist', 'derstandard.at',
              'Der Nvidia-Chef ist nach der Spionageaffäre zurückgetreten.')
OTHER = article('c', 'Wetter: Schnee in Tirol', 'krone.at')


class PairJudgeTest(unittest.TestCase):
    def tearDown(self):
        P.use_pair_decisions({})

    def test_pending_pairs_are_borderline_cross_publisher_and_undecided(self):
        store = {'articles': [HUANG, WHY, OTHER, dict(HUANG, id='d', url='https://orf.at/d')]}
        pairs = j.pending_pairs(store, {}, NOW, P)
        self.assertEqual([P.pair_key(a, b) for a, b in pairs], ['a|b', 'b|d'])
        self.assertFalse(j.pending_pairs(store, {'a|b': {}, 'b|d': {}}, NOW, P))

    def test_model_yes_merges_only_borderline_pairs_with_compatible_places(self):
        self.assertFalse(P.same_event(HUANG, WHY))
        P.use_pair_decisions({'a|b': True})
        self.assertTrue(P.same_event(HUANG, WHY))
        P.use_pair_decisions({'a|c': True})          # not borderline: no shared stems
        self.assertFalse(P.same_event(HUANG, OTHER))
        k = article('k', 'Hochwasser in Kärnten: Straßen gesperrt', 'orf.at')
        t = article('t', 'Straßen gesperrt nach Hochwasser in Tirol', 'krone.at')
        P.use_pair_decisions({P.pair_key(k, t): True})
        self.assertFalse(P.same_event(k, t))          # different places always win
        late = dict(WHY, published_at=NOW - 8 * 3600, first_seen_at=NOW - 8 * 3600)
        P.use_pair_decisions({'a|b': True})
        self.assertFalse(P.same_event(HUANG, late))   # more than 6 h apart: follow-up, not the same report

    def test_prepare_uses_stored_decisions(self):
        store = {'articles': [HUANG, WHY], 'feeds': []}
        self.assertEqual(len(P.prepare(store, NOW, pair_decisions={})['groups']), 2)
        self.assertEqual(len(P.prepare(store, NOW, pair_decisions={'a|b': True})['groups']), 1)

    def test_prune_and_settings(self):
        data = j.prune({'pairs': {'a|b': {'same': True}, 'a|x': {'same': False}}}, {'articles': [HUANG, WHY]})
        self.assertEqual(list(data['pairs']), ['a|b'])
        s = j.settings({'editorial': {'pipeline': {'llm_pairs': {'max_pairs_per_run': 999, 'enabled': False}}}})
        self.assertEqual((s['max_pairs_per_run'], s['enabled']), (200, False))

    def test_ask_parses_yes_and_no_from_server(self):
        answers = iter(['Ja', 'nein.', 'vielleicht'])

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                body = json.dumps({'choices': [{'message': {'content': next(answers)}}]}).encode()
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            self.assertIs(j.ask(url, P, HUANG, WHY), True)
            self.assertIs(j.ask(url, P, HUANG, WHY), False)
            self.assertIsNone(j.ask(url, P, HUANG, WHY))
        finally:
            server.shutdown(); server.server_close()


if __name__ == '__main__':
    unittest.main()

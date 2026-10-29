"""Regression tests for RSS date parsing, clustering and balanced selection."""
import importlib.util
import pathlib
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pnh_generate", ROOT / "scripts" / "generate.py")
news = importlib.util.module_from_spec(spec)
spec.loader.exec_module(news)


def story(title, host, number):
    return (title, "Beschreibung", f"https://{host}/story/{number}", [])


class NewsSelectionTests(unittest.TestCase):
    def test_sections_feed_priority_fallback_and_activation(self):
        settings = {'enabled': False, 'default': 'general',
                    'sections': [{'id': 'general', 'label': 'Allgemein'},
                                 {'id': 'economy', 'label': 'Wirtschaft', 'keywords': ['Inflation']},
                                 {'id': 'local', 'label': 'Lokales'}],
                    'feed_sections': {'police': 'local'}}
        local = story('Inflation im Bezirk', 'police.at', 1)
        economy = story('Inflation sinkt', 'news.at', 2)
        general = story('Parlament tagt', 'news.at', 3)
        groups = [[local], [economy], [general]]
        feeds = {(local[0], local[2]): 'police'}
        planned = news.prepare_sections(groups, feeds, settings)
        self.assertEqual([section for _, section in planned], ['local', 'economy', 'general'])
        self.assertEqual([group for group, _ in planned], groups)
        settings['enabled'] = True
        planned = news.prepare_sections(groups, feeds, settings)
        self.assertEqual([group for group, _ in planned], [[general], [economy], [local]])
        self.assertEqual(news.news_section(story('Hyperinflation', 'news.at', 4), '', settings), 'general')


    def setUp(self):
        news.FEED_DATES.clear()

    def test_rss_pubdate(self):
        node = ET.fromstring("<item><pubDate>Mon, 26 Oct 2026 12:00:00 GMT</pubDate></item>")
        self.assertGreater(news.feed_timestamp(node), 0)

    def test_rdf_dc_date(self):
        node = ET.fromstring(
            '<item xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<dc:date>2026-10-26T12:00:00Z</dc:date></item>')
        self.assertGreater(news.feed_timestamp(node), 0)

    def test_diversity_before_second_item_from_same_source(self):
        a = story("Haushaltsdebatte im Parlament beginnt", "standard.at", 1)
        b = story("Neue Vorschriften für Betriebe beschlossen", "standard.at", 2)
        c = story("Straßensperre nach Unwetter in Graz", "orf.at", 3)
        for item, age in [(a, 300), (b, 200), (c, 100)]:
            news.FEED_DATES[item[2]] = age
        chosen = news.select_balanced_groups([[a], [b], [c]], 2)
        self.assertEqual([x[0][2] for x in chosen], [a[2], c[2]])

    def test_undated_items_are_not_prioritized(self):
        old = story("Ohne Datum veröffentlichte Nachricht", "example.at", 1)
        fresh = story("Aktuelle Nachricht mit Datum", "other.at", 2)
        news.FEED_DATES[fresh[2]] = 500
        self.assertEqual(news.select_balanced_groups([[old], [fresh]], 1)[0][0], fresh)

    def test_near_identical_event_keeps_both_sources(self):
        a=story('Hochwasser an der Donau verursacht schwere Schäden', 'first.example', 1)
        b=story('Hochwasser an Donau verursacht schwere Schäden', 'second.example', 2)
        representatives,groups=news.group_news_items([a,b])
        self.assertEqual(len(representatives),1)
        self.assertEqual({entry[2] for entry in groups[0]},{a[2],b[2]})

    def test_clustering_can_be_disabled(self):
        a=story('Hochwasser an der Donau verursacht schwere Schäden', 'first.example', 1)
        b=story('Hochwasser an Donau verursacht schwere Schäden', 'second.example', 2)
        self.assertEqual(len(news.group_news_items([a,b],enabled=False)[1]),2)

    def test_unrelated_stories_stay_separate(self):
        a = story("Unwetter verursacht Schäden in Graz", "orf.at", 1)
        b = story("Regierung beschließt neue Steuerreform", "krone.at", 2)
        _, groups = news.group_news_items([a, b])
        self.assertEqual(len(groups), 2)


if __name__ == "__main__":
    unittest.main()

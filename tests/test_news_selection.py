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

    def test_unrelated_stories_stay_separate(self):
        a = story("Unwetter verursacht Schäden in Graz", "orf.at", 1)
        b = story("Regierung beschließt neue Steuerreform", "krone.at", 2)
        _, groups = news.group_news_items([a, b])
        self.assertEqual(len(groups), 2)




class CardCreditTests(unittest.TestCase):
    def test_on_screen_credit_lists_every_publisher_of_the_group(self):
        group = [story("A", "www.orf.at", 1), story("B", "derstandard.at", 2), story("C", "orf.at", 3)]
        self.assertEqual(news.card_credit(group), "orf.at, derstandard.at")

    def test_single_source_and_overflow(self):
        self.assertEqual(news.card_credit([story("A", "krone.at", 1)]), "krone.at")
        hosts = ["derstandard.at", "kleinezeitung.at", "krone.at", "orf.at", "salzburg24.at", "heute.at"]
        credit = news.card_credit([story("A", host, i) for i, host in enumerate(hosts)])
        self.assertTrue(credit.startswith("derstandard.at, kleinezeitung.at"))
        self.assertRegex(credit, r" \+\d$")
        self.assertLessEqual(len(credit), 60)



class SentenceSplitTests(unittest.TestCase):
    def test_short_update_text_keeps_regnal_numbers_and_abbreviations(self):
        text = news.edit_news("Papst in Peru", "Papst Leo XIV. hat in Lima gesprochen. Dafür wurden 2 Mio. Euro ausgegeben. Dritter Satz.", "classic", 2, 900)
        self.assertEqual(text, "Papst in Peru.\nPapst Leo XIV. hat in Lima gesprochen. Dafür wurden 2 Mio. Euro ausgegeben.")


class SpokenTextTests(unittest.TestCase):
    def test_source_credits_are_not_read_aloud(self):
        self.assertEqual(news.spoken_text("Titel.\nSatz eins.\nQuellen: orf.at, krone.at."), "Titel.\nSatz eins.")
        self.assertEqual(news.spoken_text("Titel.\nSatz.\nQuelle: orf.at."), "Titel.\nSatz.")
        self.assertEqual(news.spoken_text("Titel.\nSatz.\\nÜber dieses Ereignis berichten auch: krone.at."), "Titel.\nSatz.")
        self.assertEqual(news.spoken_text("Die Quellenlage ist unklar."), "Die Quellenlage ist unklar.")

if __name__ == "__main__":
    unittest.main()

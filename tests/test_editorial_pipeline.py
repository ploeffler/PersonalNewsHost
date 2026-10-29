import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('editorial_pipeline',Path(__file__).resolve().parents[1]/'scripts/editorial_pipeline.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
NOW=2000000

def article(id,title,text,host='example.org',published=None):
    return {'id':id,'title':title,'text':text,'url':f'https://{host}/{id}','first_seen_at':NOW-100,
            'published_at':NOW-100 if published is None else published,'feed_urls':[f'https://{host}/rss']}

def stored(articles):return {'updated_at':NOW,'articles':articles,'feeds':[]}

def members():return [article('a','Zugunglück in München: Zehn Menschen verletzt',
    'Bei dem Zugunglück wurden zehn Menschen verletzt. Die Polizei ermittelt zur Ursache.'),
    article('b','Zugunglück in München: Zehn Menschen verletzt – Strecke gesperrt',
    'Bei dem Zugunglück wurden zehn Menschen verletzt. Die Bahnstrecke bleibt bis zum Abend gesperrt.','second.org')]

class EditorialPipelineTests(unittest.TestCase):
    def test_combines_complementary_sentences_from_different_sources(self):
        report=p.prepare(stored(members()),NOW)
        self.assertEqual(len(report['groups']),1)
        group=report['groups'][0]
        self.assertEqual(group['verification']['status'],'approved')
        self.assertEqual(group['used_source_ids'],['a','b'])
        self.assertIn('zehn Menschen verletzt',group['draft']['text'])
        self.assertIn('Bahnstrecke bleibt',group['draft']['text'])
        self.assertFalse(group['verification']['independent_fact_check'])
        self.assertEqual(group['verification']['source_independence'],'not_assessed')

    def test_question_headline_is_not_changed_to_a_statement(self):
        item=article('q','Ist die Strecke in München wieder frei?', 'Die Bahnstrecke bleibt bis zum Abend gesperrt.')
        draft=p.prepare(stored([item]),NOW)['groups'][0]['draft']
        self.assertTrue(draft['text'].startswith(item['title']+'\n'))

    def test_distinct_places_and_broad_topics_are_not_grouped(self):
        a,b=members();b['title']=a['title'].replace('München','Berlin')
        self.assertFalse(p.same_event(a,b))
        self.assertFalse(p.same_event(article('a','Trump gewinnt die Wahl',''),article('b','Trump vor Gericht wegen Betrugsvorwurf','')))

    def test_counter_disagreement_is_held_before_selection(self):
        a,b=members();b['title']=b['title'].replace('Zehn','Zwölf');b['text']=b['text'].replace('zehn','zwölf')
        report=p.prepare(stored([a,b]),NOW)
        self.assertEqual(len(report['groups']),1)
        self.assertIn('conflicting_source_values',report['groups'][0]['verification']['issues'])
        self.assertFalse(p.select(report,5))

    def test_numbers_names_negation_and_modal_qualifiers_cannot_be_changed(self):
        source=article('a','Ermittlungen nach Unfall in München dauern an',
                       'Die Polizei hält einen technischen Defekt möglicherweise nicht für die Ursache. In München wurden zehn Menschen verletzt.')
        report=p.prepare(stored([source]),NOW);group=report['groups'][0]
        self.assertIn('möglicherweise nicht',group['draft']['text'])
        for old,new in [('möglicherweise nicht',''),('München','Berlin'),('zehn','zwölf')]:
            draft=copy.deepcopy(group['draft'])
            for c in draft['claims']:c['text']=c['text'].replace(old,new);c['quote']=c['text']
            draft['text']=p.render_draft(draft,report['sources'])
            self.assertEqual(p.verify(draft,[source],report['sources'])['status'],'held')

    def test_free_text_and_foreign_citation_are_rejected(self):
        report=p.prepare(stored(members()),NOW);group=report['groups'][0]
        draft=copy.deepcopy(group['draft']);draft['text']+=' Erfundenes Zusatzwissen.'
        self.assertIn('unverified_rendered_text',p.verify(draft,members(),report['sources'])['issues'])
        outside=article('outside','Andere Nachricht','Eine vollständig andere Nachricht aus Wien.')
        sources={**report['sources'],'outside':{**outside,'publisher':'outside.org'}}
        draft=copy.deepcopy(group['draft']);draft['claims'][0]['source_id']='outside'
        draft['text']=p.render_draft(draft,sources)
        self.assertEqual(p.verify(draft,members(),sources)['status'],'held')

    def test_one_bounded_repair_pass_is_recorded(self):
        def damaged(m,s,count):
            draft=p.formulate(m,s,count);draft['claims'][0]['text']='Eine frei erfundene Behauptung.';draft['text']=p.render_draft(draft,s);return draft
        report=p.prepare(stored(members()),NOW,writer=damaged)
        attempts=report['groups'][0]['attempts'];self.assertEqual([a['status'] for a in attempts],['held','approved'])

    def test_all_groups_are_checked_before_limit_is_applied(self):
        items=[article('a','Parlament beschließt neue Agrarreform','Das Parlament hat heute eine neue Agrarreform beschlossen.'),
               article('b','Sonderzug erreicht Bahnhof Salzburg','Der Sonderzug erreichte am Vormittag den Bahnhof Salzburg.','second.org'),
               article('c','Museum eröffnet neue Ausstellung','Das Museum eröffnet heute eine neue Ausstellung.','third.org')]
        report=p.prepare(stored(items),NOW);self.assertEqual(len(report['groups']),3)
        self.assertEqual(len(p.select(report,2)),2);self.assertEqual(sum(g['selected'] for g in report['groups']),2)

    def test_expired_future_and_empty_prose_are_not_used(self):
        report=p.prepare(stored([article('old','Ältere Meldung aus Wien','Ein alter Meldungstext.',published=NOW-86401),
                                 article('future','Künftige Meldung aus Wien','Eine künftige Meldung.',published=NOW+1),
                                 article('empty','Meldung ohne Nachrichtentext','')]),NOW)
        self.assertEqual(len(report['groups']),1);self.assertEqual(report['groups'][0]['verification']['status'],'held')
        self.assertFalse(p.select(report,5))

    def test_missing_and_stale_store_fail_without_raw_feed_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'news-store.json'
            with self.assertRaises(RuntimeError):p.production_plan(path,NOW)
            path.write_text(json.dumps({'updated_at':NOW-1801,'articles':[]}))
            with self.assertRaises(RuntimeError):p.production_plan(path,NOW)
            path.write_text(json.dumps(stored([])))
            with self.assertRaises(RuntimeError):p.production_plan(path,NOW)
            self.assertTrue((path.parent/'editorial-report.json').is_file())

    def test_district_cleanup_preserves_locality_and_date(self):
        source=article('p','Verkehrsunfall mit Verletzten','Liezen | Döllach. – Am 26. Oktober ereignete sich ein Verkehrsunfall.')
        group=p.prepare(stored([source]),NOW)['groups'][0]
        self.assertIn('Döllach im Bezirk Liezen',group['draft']['text'])
        self.assertIn('26. Oktober',group['draft']['text'])
        self.assertEqual(group['verification']['status'],'approved')

if __name__=='__main__':unittest.main()

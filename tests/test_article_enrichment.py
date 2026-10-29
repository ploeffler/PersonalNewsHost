import copy
import datetime as dt
import email.utils
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

spec=importlib.util.spec_from_file_location('article_enrichment',Path(__file__).resolve().parents[1]/'scripts/article_enrichment.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
NOW=2000000
TITLE='Polizei bestätigt Sperre nach Vorfall in Wien'
BODY='Die Polizei hat nach dem Vorfall die betroffene Straße gesperrt. Der Verkehr wird nach Angaben der Einsatzkräfte über eine andere Strecke umgeleitet, bis die Arbeiten abgeschlossen sind.'

def doc(title=TITLE,body=BODY,url='https://orf.at/stories/1/',kind='orf'):
    css='story-story' if kind=='orf' else 'article-body'
    return {'status':200,'final_url':url,'content_type':'text/html','body':f'<html><title>{title}</title><nav><p>Navigation nicht übernehmen.</p></nav><div class="{css}"><p>{body}</p></div><footer><p>Footer nicht übernehmen.</p></footer></html>'}

def article(id='a',**changes):
    return {'id':id,'title':TITLE,'text':'','url':f'https://orf.at/stories/{id}/','first_seen_at':NOW-20,'published_at':NOW-30,'feed_urls':['https://rss.orf.at/news.xml'],**changes}

class ArticleEnrichmentTests(unittest.TestCase):
    def test_orf_extracts_article_without_navigation(self):
        result=e.extract(TITLE,'https://orf.at/stories/1/',doc())
        self.assertEqual(result['status'],'success');self.assertEqual(result['method'],'orf_story_story')
        self.assertEqual(result['text'],BODY);self.assertNotIn('Navigation',result['text'])

    def test_generic_and_structured_article_data(self):
        value=doc(url='https://example.org/article',kind='generic')
        self.assertEqual(e.extract(TITLE,value['final_url'],value)['method'],'article_body_dom')
        value['body']=f'<html><title>{TITLE}</title><script type="application/ld+json">'+json.dumps({'@type':'NewsArticle','headline':TITLE,'articleBody':BODY})+'</script></html>'
        self.assertEqual(e.extract(TITLE,value['final_url'],value)['method'],'json_ld_article_body')

    def test_wrong_page_consent_paywall_and_content_types_are_not_sources(self):
        self.assertEqual(e.extract(TITLE,'https://orf.at/stories/1/',doc(title='Andere Seite'))['status'],'title_mismatch')
        value=doc(url='https://orf.at/consent/page');self.assertEqual(e.extract(TITLE,'https://orf.at/stories/1/',value)['status'],'consent_or_login')
        value=doc();value['body']+= '<script type="application/ld+json">{"@type":"NewsArticle","isAccessibleForFree":false}</script>'
        self.assertEqual(e.extract(TITLE,'https://orf.at/stories/1/',value)['status'],'paywall')
        value=doc();value['content_type']='application/pdf';self.assertEqual(e.extract(TITLE,'https://orf.at/stories/1/',value)['status'],'not_html')

    def test_redirect_and_canonical_identity(self):
        self.assertEqual(e.extract(TITLE,'https://orf.at/stories/1/',doc(url='https://evil.test/article'))['status'],'redirect_rejected')
        value=doc();value['body']+='<link rel="canonical" href="https://evil.test/article">'
        self.assertEqual(e.extract(TITLE,'https://orf.at/stories/1/',value)['status'],'canonical_rejected')
        self.assertFalse(e.url_allowed('http://127.0.0.1/a'));self.assertFalse(e.url_allowed('https://user:password@example.org/a'));self.assertFalse(e.url_allowed('file:///etc/passwd'))

    def test_cache_provenance_and_age_preservation(self):
        item=article();fetch=Mock(side_effect=lambda url:doc(url=url))
        e.enrich_articles([item],NOW,fetch=fetch)
        self.assertEqual(item['text_origin'],'linked_article');self.assertEqual(item['rss_text'],'')
        self.assertEqual(item['article_fetch']['method'],'orf_story_story');self.assertEqual(len(item['article_fetch']['text_sha256']),64)
        self.assertEqual((item['first_seen_at'],item['published_at']),(NOW-20,NOW-30))
        e.enrich_articles([item],NOW+60,fetch=fetch);fetch.assert_called_once()
        item['rss_revision_at']=NOW+60
        e.enrich_articles([item],NOW+120,fetch=fetch);self.assertEqual(fetch.call_count,2)

    def test_failure_backoff_and_changed_headline_does_not_use_stale_text(self):
        item=article();fetch=Mock(side_effect=TimeoutError())
        e.enrich_articles([item],NOW,fetch=fetch);e.enrich_articles([item],NOW+60,fetch=fetch);fetch.assert_called_once()
        self.assertEqual(item['article_fetch']['status'],'fetch_error')
        e.enrich_articles([item],NOW+1801,fetch=fetch);self.assertEqual(fetch.call_count,2)
        good=article();e.enrich_articles([good],NOW,fetch=lambda url:doc(url=url))
        good['title']='Völlig neue Meldung aus einer anderen Stadt'
        e.enrich_articles([good],NOW+60,fetch=lambda url:doc(url=url))
        self.assertNotIn('article_text',good);self.assertEqual(good['text'],'');self.assertEqual(good['article_fetch']['status'],'title_mismatch')

    def test_refresh_failure_preserves_same_version_snapshot(self):
        item=article();e.enrich_articles([item],NOW,fetch=lambda url:doc(url=url))
        e.enrich_articles([item],NOW+6*3600+1,fetch=Mock(side_effect=TimeoutError()))
        self.assertEqual(item['text'],BODY);self.assertEqual(item['article_fetch']['fetched_at'],NOW)
        self.assertEqual(item['article_fetch']['last_error'],'fetch_error')

    def test_fetch_budget_and_deferred_retry(self):
        items=[article('a'),article('b')];fetch=Mock(side_effect=lambda url:doc(url=url))
        e.enrich_articles(items,NOW,settings={'max_fetches_per_run':1},fetch=fetch)
        self.assertEqual(fetch.call_count,1);self.assertEqual(items[1]['article_fetch']['status'],'deferred')
        e.enrich_articles(items,NOW+60,settings={'max_fetches_per_run':1},fetch=fetch)
        self.assertEqual(fetch.call_count,2);self.assertTrue(all(i['text_origin']=='linked_article' for i in items))

    def test_puzzles_are_classified_without_fetching_but_news_about_puzzles_is_not(self):
        fetch=Mock();puzzle=article(title='Smart Sudoku sehr schwierig 776b')
        e.enrich_articles([puzzle],NOW,fetch=fetch);fetch.assert_not_called();self.assertEqual(puzzle['content_kind'],'non_news')
        news=article(title='Sudoku-App veröffentlicht neue Datenschutzfunktionen',text=BODY)
        e.enrich_articles([news],NOW,fetch=fetch);self.assertEqual(news['content_kind'],'news');fetch.assert_not_called()

    def test_optional_rdrr_fallback_uses_existing_markup_cleanup(self):
        from types import SimpleNamespace
        with patch.object(e.shutil,'which',return_value='/usr/bin/rdrr'),patch.object(e.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps({'content':'**'+BODY+'**'}))) as command:
            self.assertEqual(e.rdrr_fallback(TITLE,'https://example.org/article'),BODY)
            self.assertIn('--strict',command.call_args.args[0])

    def test_collector_cache_survives_another_empty_rss_poll(self):
        from scripts.collect_news import collect
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config.json').write_text(json.dumps({'feeds':['https://rss.orf.at/news.xml']}))
            stamp=email.utils.format_datetime(dt.datetime.fromtimestamp(NOW-30,dt.timezone.utc))
            xml=f'<rss><channel><title>ORF</title><item><title>{TITLE}</title><link>https://orf.at/stories/a/</link><pubDate>{stamp}</pubDate></item></channel></rss>'.encode()
            fetch=Mock(side_effect=lambda url:doc(url=url))
            first=collect(root,lambda url:xml,NOW,article_fetch=fetch)
            second=collect(root,lambda url:xml,NOW+60,article_fetch=fetch)
            fetch.assert_called_once();self.assertEqual(first['articles'][0]['text'],second['articles'][0]['text'])
            self.assertEqual(second['articles'][0]['published_at'],NOW-30);self.assertEqual(second['articles'][0]['first_seen_at'],NOW)

if __name__=='__main__':unittest.main()

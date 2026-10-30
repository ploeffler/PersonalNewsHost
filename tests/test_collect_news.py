import importlib.util
from pathlib import Path
import json
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('collect_news',Path(__file__).resolve().parents[1]/'scripts/collect_news.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class NewsStoreTests(unittest.TestCase):
    def test_all_feed_entries_and_atom_dates(self):
        data='<rss><channel><title>Mein Feed</title>'+''.join(f'<item><title>Meldung {i}</title><description>&lt;p&gt;Text {i}&lt;/p&gt;</description></item>' for i in range(40))+'</channel></rss>'
        name,items=m.parse_feed(data.encode(),'https://example.org/rss',2000000)
        self.assertEqual(name,'Mein Feed');self.assertEqual(len(items),40);self.assertEqual(items[0]['text'],'Text 0')
        _,items=m.parse_feed(b'<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom</title><entry><title>Alt</title><updated>2026-10-29T10:00:00Z</updated><link rel="self" href="https://example.org/self"/><link href="https://example.org/article"/></entry></feed>','https://example.org/feed',2000000)
        self.assertIsNone(items[0]['published_at']);self.assertEqual(items[0]['url'],'https://example.org/article')

    def test_tracking_dedup_preserves_article_identifiers(self):
        self.assertEqual(m.identity('https://example.org/a?utm_source=x','A'),m.identity('https://example.org/a','A'))
        self.assertNotEqual(m.identity('https://example.org/a?id=1','A'),m.identity('https://example.org/a?id=2','A'))

    def test_age_future_and_original_date(self):
        now=2000000
        old={'id':'a','title':'A','text':'Alt','published_at':now-86401,'first_seen_at':now-90000,'feed_urls':['a']}
        incoming={**old,'published_at':now,'first_seen_at':now,'feed_urls':['b']}
        self.assertFalse(m.merge_articles([old],[incoming],now))
        undated={**old,'published_at':None}
        self.assertFalse(m.merge_articles([undated],[incoming],now))
        self.assertFalse(m.merge_articles([],[{**incoming,'published_at':now+1}],now))
        self.assertFalse(m.merge_articles([],[{**incoming,'published_at':now-86400}],now))

    def test_collection_badges_outage_and_no_undated_resurrection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);docs=root/'docs';docs.mkdir();url='https://example.org/rss';now=2000000
            (root/'config.json').write_text(json.dumps({'feeds':[url]}))
            (docs/'broadcasts.json').write_text(json.dumps({'broadcasts':[{'id':'latest','created_at':now-100}]}))
            (docs/'story-groups.json').write_text(json.dumps([{'headline':'A','sources':[{'url':'https://example.org/a','description':'Beschreibung A'}]}]))
            (docs/'short-updates.json').write_text(json.dumps({'updates':[{'title':'B','url':'https://example.org/b','text':'B Text','created_at':now-10}]}))
            feed=b'<rss><channel><title>RSS Nachrichten</title><item><title>A</title><link>https://example.org/a</link><description>Text A</description></item><item><title>B</title><link>https://example.org/b</link></item></channel></rss>'
            result=m.collect(root,lambda _:feed,now)
            a=next(a for a in result['articles'] if a['title']=='A');b=next(a for a in result['articles'] if a['title']=='B')
            self.assertEqual(a['broadcast_id'],'latest');self.assertEqual(a['broadcast_position'],1);self.assertEqual(b['short_update_at'],now-10)
            def fail(_):raise OSError('offline')
            result=m.collect(root,fail,now+10);self.assertEqual(len(result['articles']),2);self.assertEqual(result['feeds'][0]['name'],'RSS Nachrichten')
            (docs/'short-updates.json').write_text('{"updates":[]}')
            result=m.collect(root,lambda _:feed,now+86401)
            self.assertFalse(result['articles'])
            result=m.collect(root,lambda _:feed,now+86402);self.assertFalse(result['articles'])

    def test_every_member_of_a_combined_broadcast_story_is_marked(self):
        now=2000000
        items=[{'id':key,'title':'Meldung '+key,'url':'https://example.org/'+key,'text':'Nachrichtentext '+key,'published_at':now-100,'first_seen_at':now-100,'feed_urls':[]} for key in ['a','b']]
        group={'headline':items[0]['title'],'sources':[{'title':a['title'],'url':a['url']} for a in items]}
        articles,ids,records=m.annotate(items,[group],{'id':'latest','created_at':now-10},[],now)
        self.assertEqual(len(ids),2)
        self.assertEqual({a['broadcast_position'] for a in articles},{1})
        self.assertTrue(all(a['broadcast_id']=='latest' for a in articles))

    def test_expired_selected_message_is_not_reintroduced(self):
        now=2000000
        old={'id':'a','title':'A','url':'https://example.org/a','text':'old','published_at':now-90000,'first_seen_at':now-90000,'feed_urls':[]}
        articles,selected,records=m.annotate([],[{'headline':'A','sources':[{'url':old['url']}]}],{'id':'latest','created_at':now-100},[],now,[old])
        self.assertFalse(articles);self.assertEqual(selected,['a']);self.assertEqual(records[0]['published_at'],old['published_at'])

if __name__=='__main__':unittest.main()

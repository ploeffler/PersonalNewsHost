#!/usr/bin/env python3
"""Validate researched catalogues and their OPML exports without internet access."""
import argparse
import datetime as dt
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CATALOGUES={'news':'feed-catalog','authorities':'police-feed-catalog'}

def validate(group,root=ROOT):
    stem=CATALOGUES[group]
    data=json.loads((root/'docs'/f'{stem}.json').read_text())
    dt.date.fromisoformat(data['researched_on'])
    rows=data['feeds']
    if not rows:
        raise ValueError('Catalogue is empty: no source was confirmed')
    ids=[r['id'] for r in rows];urls=[r['url'] for r in rows]
    if len(set(ids))!=len(rows) or len(set(urls))!=len(rows):
        raise ValueError('Duplicate source identifiers or URLs')
    if any(r.get('enabled_by_default') is not False for r in rows):
        raise ValueError('Research must not automatically activate sources')
    if any(r['format'] not in ('rss1','rss2','atom') for r in rows):
        raise ValueError('Non-feed source in the feed catalogue')
    eligible={'verified_recent'} if group=='news' else {'verified_recent','verified_warning_feed','available_empty'}
    expected={r['url'] for r in rows if r['status'] in eligible and r['url'].startswith('https://')}
    opml=ET.parse(root/'docs'/f'{stem}.opml')
    actual=[n.get('xmlUrl') for n in opml.findall('.//outline') if n.get('xmlUrl')]
    if len(set(actual))!=len(actual) or set(actual)!=expected:
        raise ValueError('OPML does not match the eligible catalogue entries')
    if group=='news':
        if any(r['language'] not in ('de','en') for r in rows):
            raise ValueError('Unexpected language')
        if data['counts']['feeds']!=len(rows):
            raise ValueError('News feed count does not match')
    else:
        if data['counts']['total_feeds']!=len(rows) or data['counts']['importable_feeds']!=len(actual):
            raise ValueError('Authority feed counts do not match')
        if any(not r.get('requires_warning_adapter') for r in rows if r.get('purpose')=='official_warning'):
            raise ValueError('Warning feed missing adapter requirement')
        if {r['url'] for r in data['mixed_feeds']+data['non_feed_sources']} & set(actual):
            raise ValueError('Mixed or non-feed source in regular import')
    return {'group':group,'researched_on':data['researched_on'],'feeds':len(rows),'opml_feeds':len(actual)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group',choices=CATALOGUES,required=True)
    args=parser.parse_args()
    print(json.dumps(validate(args.group),ensure_ascii=False))

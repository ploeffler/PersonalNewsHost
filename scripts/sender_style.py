"""Versioned sender CI, private SQLite state and atomic preview outbox."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time

ROOT = Path(__file__).resolve().parents[1]
TEXT_FIELDS = {'name':120, 'description':1500, 'audience':700, 'language':80, 'tone':500,
               'visual_direction':1500, 'font_family':120, 'branding':700, 'studio':500, 'avatar':500}
DEFAULT = {'name':'Mein Sender', 'description':'', 'audience':'Allgemeines Publikum', 'language':'de',
           'tone':'Sachlich und verständlich', 'visual_direction':'Klare, ruhige Nachrichtengestaltung',
           'font_family':'sans-serif', 'branding':'', 'studio':'', 'avatar':'',
           'colors':['#123047','#e8b34c','#f5f7fa'], 'size':'1536x1024', 'sources':[]}


class Conflict(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def normalize(value):
    if not isinstance(value, dict) or set(value) - set(DEFAULT):
        raise ValueError('Unbekannte CI-Felder')
    result = deepcopy(DEFAULT)
    result.update(value)
    for key, maximum in TEXT_FIELDS.items():
        text = result[key]
        if not isinstance(text, str) or len(text) > maximum or any(ord(c)<32 and c not in '\n\t' for c in text):
            raise ValueError('Ungültiges CI-Feld: ' + key)
        result[key] = text.strip()
    if not result['name'] or not result['language']:
        raise ValueError('Sendername und Sprache fehlen')
    colors = result['colors']
    if not isinstance(colors, list) or not 1 <= len(colors) <= 8 or any(not isinstance(c,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',c) for c in colors):
        raise ValueError('Ein bis acht Farben im Format #RRGGBB erforderlich')
    result['colors'] = [c.lower() for c in colors]
    if result['size'] not in ('1536x1024','1024x1536','1024x1024'):
        raise ValueError('Ungültiges Vorschauformat')
    sources = result['sources']
    if not isinstance(sources,list) or len(sources)>4:
        raise ValueError('Zu viele Recherchequellen')
    try:
        from .promo_network import validate_feed_url
    except ImportError:
        from promo_network import validate_feed_url
    for source in sources:
        if not isinstance(source,dict) or set(source)!={'url','retrieved_at'} or not isinstance(source['url'],str) or len(source['url'])>2000:
            raise ValueError('Ungültige Recherchequelle')
        validate_feed_url(source['url'],resolve=False)
        if type(source['retrieved_at']) not in (int,float) or not 0 <= source['retrieved_at'] < 100000000000:
            raise ValueError('Ungültiger Quellenzeitpunkt')
    return result


def seed(config):
    """Explicit allowlist, never copy credentials or arbitrary configuration."""
    identity = config.get('editorial_identity',{})
    if not isinstance(identity,dict):identity={}
    value = deepcopy(DEFAULT)
    fields = {'name':config.get('title'), 'description':identity.get('format_description'),
              'audience':identity.get('audience'), 'language':identity.get('language',config.get('language')),
              'tone':identity.get('tone')}
    for key, item in fields.items():
        if isinstance(item,str) and item.strip():value[key]=item[:TEXT_FIELDS[key]]
    value['branding'] = 'Sendername: ' + value['name']
    return normalize(value)


def effective_style(sender_snapshot, override=None):
    """Reusable inheritance contract; production integrations consume a snapshot."""
    if not sender_snapshot:return None
    data = deepcopy(sender_snapshot)
    if override:
        if not isinstance(override,dict):raise ValueError('Ungültige Stilüberschreibung')
        data['style'] = normalize({**data['style'], **override})
        data['override'] = deepcopy(override)
    return data


class Store:
    def __init__(self, state, library=None):
        self.root = Path(state).resolve()
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        os.chmod(self.root,0o700)
        self.path = self.root/'sender-style.sqlite'
        if self.path.is_symlink():raise ValueError('Symlink als Datenbank nicht erlaubt')
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS editor (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, draft TEXT NOT NULL, active TEXT);
            CREATE TABLE IF NOT EXISTS versions (id TEXT PRIMARY KEY, style TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS batches (id TEXT PRIMARY KEY, version TEXT NOT NULL, snapshot TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, batch TEXT NOT NULL, style_id TEXT NOT NULL, status TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', attempts INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS reissues (source TEXT PRIMARY KEY, target TEXT NOT NULL);
            ''')
            db.execute('INSERT OR IGNORE INTO editor VALUES (1,0,?,NULL)',(canonical(DEFAULT),))
        os.chmod(self.path,0o600)
        self.library = library or json.loads((ROOT/'planning/research/video_style_library.json').read_text())
        styles=[s for c in self.library['categories'] for s in c['styles']]
        if len({s['style_id'] for s in styles}) != len(styles):raise ValueError('Doppelte Stil-ID')
        self.styles=styles

    def db(self):
        # Autocommit disabled; context commits or rolls back, then closes.
        class Connection:
            def __init__(self,path):self.path=path
            def __enter__(self):
                self.db=sqlite3.connect(self.path,timeout=15);self.db.row_factory=sqlite3.Row
                self.db.execute('PRAGMA busy_timeout=15000');return self.db
            def __exit__(self,kind,value,trace):
                try:
                    self.db.rollback() if kind else self.db.commit()
                finally:self.db.close()
        return Connection(self.path)

    def state(self):
        with self.db() as db:
            editor=db.execute('SELECT * FROM editor WHERE id=1').fetchone()
            versions=[dict(v) for v in db.execute('SELECT id,created FROM versions ORDER BY created DESC')]
            batches=[]
            for batch in db.execute('SELECT id,version,created FROM batches ORDER BY created DESC'):
                item=dict(batch);item['stale']=item['version']!=editor['active']
                link=db.execute('SELECT target FROM reissues WHERE source=?',(item['id'],)).fetchone()
                item['replacement']=link['target'] if link else None
                link=db.execute('SELECT source FROM reissues WHERE target=?',(item['id'],)).fetchone()
                item['reissued_from']=link['source'] if link else None
                item['jobs']=[dict(j) for j in db.execute('SELECT * FROM jobs WHERE batch=? ORDER BY style_id',(item['id'],))]
                batches.append(item)
            return {'revision':editor['revision'],'draft':json.loads(editor['draft']),'active_version':editor['active'],
                    'active':json.loads(db.execute('SELECT style FROM versions WHERE id=?',(editor['active'],)).fetchone()[0]) if editor['active'] else None,
                    'versions':versions,'batches':batches,'library_version':self.library['version'],
                    'styles':[{'id':s['style_id'],'name':s['name_de']} for s in self.styles]}

    def save_draft(self,value,revision):
        value=normalize(value)
        if type(revision) is not int:raise ValueError('Ungültige Revision')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('UPDATE editor SET draft=?,revision=revision+1 WHERE id=1 AND revision=?',(canonical(value),revision)).rowcount!=1:
                raise Conflict('Entwurf wurde anderweitig geändert. Neu laden.')
        return self.state()

    def reissue(self,batch,provider,allow_uncertain=False):
        """Explicit new consent; retain old context, reservations and attempt history."""
        allowed={'backend','model','quality','format','allow_paid','reservation_eur','monthly_eur','batch_eur'}
        if not isinstance(provider,dict) or set(provider)!=allowed or provider['backend']!='openai' or provider['allow_paid'] is not True:
            raise ValueError('Aktuellen Bildprovider und Kostenfreigabe einrichten')
        if type(allow_uncertain) is not bool:raise ValueError('Ungültige Kostenbestätigung')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            source=db.execute('SELECT * FROM batches WHERE id=?',(batch,)).fetchone()
            if source is None:raise ValueError('Unbekannte Vorschauserie')
            link=db.execute('SELECT target FROM reissues WHERE source=?',(batch,)).fetchone()
            if link is None:
                statuses={r['status'] for r in db.execute('SELECT status FROM jobs WHERE batch=?',(batch,))}
                if 'processing' in statuses:raise Conflict('Laufende Serie zuerst abschließen lassen')
                if not statuses-{'complete'}:raise ValueError('Serie ist bereits vollständig')
                if statuses & {'uncertain','failed'} and not allow_uncertain:
                    raise ValueError('Vor Neubeauftragung Abrechnung bestätigen')
                snapshot=json.loads(source['snapshot'])
                snapshot['provider']=deepcopy(provider)
                snapshot['reissued_from']=batch
                target=digest(snapshot)
                db.execute('INSERT INTO batches VALUES (?,?,?,?)',(target,source['version'],canonical(snapshot),time.time()))
                for category in snapshot['library']['categories']:
                    for entry in category['styles']:
                        job=digest({'batch':target,'style_id':entry['style_id']})
                        db.execute('INSERT INTO jobs(id,batch,style_id,status) VALUES (?,?,?,?)',(job,target,entry['style_id'],'queued'))
                db.execute('INSERT INTO reissues VALUES (?,?)',(batch,target))
                db.execute("UPDATE jobs SET status='superseded',error='Durch ausdrücklich freigegebene Ersatzserie abgelöst' WHERE batch=? AND status='queued'",(batch,))
        return self.state()

    def restore(self,version,revision):
        with self.db() as db:
            row=db.execute('SELECT style FROM versions WHERE id=?',(version,)).fetchone()
        if row is None:raise ValueError('Unbekannte Stilversion')
        return self.save_draft(json.loads(row[0]),revision)

    def adopt(self,revision,provider):
        """Single transaction: immutable version + idempotent outbox + activation."""
        allowed={'backend','model','quality','format','allow_paid','reservation_eur','monthly_eur','batch_eur'}
        if not isinstance(provider,dict) or set(provider)!=allowed or type(revision) is not int:
            raise ValueError('Ungültiger Provider-Snapshot')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM editor WHERE id=1').fetchone()
            if row['revision']!=revision:raise Conflict('Entwurf wurde geändert. Neu laden.')
            style=normalize(json.loads(row['draft']));version=digest(style)
            snapshot={'style':style,'sender_version':version,'library':deepcopy(self.library),
                      'provider':provider,'prompt_version':'sender-ci-v1'}
            batch=digest(snapshot)
            db.execute('INSERT OR IGNORE INTO versions VALUES (?,?,?)',(version,canonical(style),time.time()))
            db.execute('INSERT OR IGNORE INTO batches VALUES (?,?,?,?)',(batch,version,canonical(snapshot),time.time()))
            for entry in self.styles:
                job=digest({'batch':batch,'style_id':entry['style_id']})
                db.execute('INSERT OR IGNORE INTO jobs(id,batch,style_id,status) VALUES (?,?,?,?)',(job,batch,entry['style_id'],'queued'))
            # Repeated adoption is idempotent, including editor revision.
            db.execute('UPDATE editor SET active=? WHERE id=1',(version,))
        return self.state()

    def recover(self):
        from PIL import Image
        with self.db() as db:
            rows=db.execute("SELECT j.id,b.snapshot FROM jobs j JOIN batches b ON j.batch=b.id WHERE j.status='processing'").fetchall()
            for row in rows:
                target=self.root/'images'/(row['id']+'.png')
                complete=False
                try:
                    if target.is_file() and not target.is_symlink() and target.stat().st_size<=20000000:
                        expected=json.loads(row['snapshot'])['style']['size']
                        with Image.open(target) as im:
                            valid=im.format=='PNG' and str(im.width)+'x'+str(im.height)==expected
                            im.verify();complete=valid
                except (OSError,ValueError):pass
                status='complete' if complete else 'uncertain'
                error='' if complete else 'Unterbrochener Provideraufruf; vor Wiederholung Abrechnung prüfen.'
                db.execute('UPDATE jobs SET status=?,error=? WHERE id=?',(status,error,row['id']))

    def retry(self,job,allow_uncertain=False):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT status,batch FROM jobs WHERE id=?',(job,)).fetchone()
            if row and db.execute('SELECT 1 FROM reissues WHERE source=?',(row['batch'],)).fetchone():
                raise ValueError('Serie wurde durch eine neue Beauftragung abgelöst')
            allowed={'failed','waiting_provider','waiting_budget'}
            if allow_uncertain:allowed.add('uncertain')
            if row is None or row['status'] not in allowed:raise ValueError('Job ist nicht wiederholbar oder Kostenbestätigung fehlt')
            db.execute("UPDATE jobs SET status='queued',error='' WHERE id=?",(job,))
        return self.state()

    def job_context(self,job):
        with self.db() as db:
            row=db.execute('SELECT j.*,b.snapshot FROM jobs j JOIN batches b ON b.id=j.batch WHERE j.id=?',(job,)).fetchone()
        if row is None:raise ValueError('Unbekannter Vorschauauftrag')
        return dict(row)


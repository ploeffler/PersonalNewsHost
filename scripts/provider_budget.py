"""Persistent conservative reservations; failed/uncertain attempts remain charged."""
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3
import uuid


class BudgetExceeded(RuntimeError): pass


def money(value):
    if isinstance(value, bool): raise ValueError('Invalid budget')
    try: result = Decimal(str(value))
    except InvalidOperation: raise ValueError('Invalid budget') from None
    if not result.is_finite() or result < 0: raise ValueError('Invalid budget')
    return result


class Budget:
    def __init__(self, path, *, monthly_budget_eur=0, per_run_budget_eur=0, unit_limits=None):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.monthly, self.per_run = money(monthly_budget_eur), money(per_run_budget_eur)
        self.limits = unit_limits or {}
        if any(type(v) is not int or v < 0 for v in self.limits.values()): raise ValueError('Invalid unit limit')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS reservations (id TEXT PRIMARY KEY, namespace TEXT, month TEXT, run TEXT, provider TEXT, cost TEXT, units TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS requests (namespace TEXT, provider TEXT, at REAL)')
        self.path.chmod(0o600)

    def reserve(self, namespace, run, provider, cost, units=None, *, rate_limit=0, now=None):
        cost = money(cost); units = units or {}
        if any(type(v) is not int or v < 0 for v in units.values()): raise ValueError('Invalid usage')
        if type(rate_limit) is not int or rate_limit < 0: raise ValueError('Invalid rate limit')
        at = datetime.now(timezone.utc) if now is None else now
        month = at.astimezone(timezone.utc).strftime('%Y-%m'); stamp = at.timestamp()
        with closing(sqlite3.connect(self.path, timeout=30)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('SELECT cost,units,run FROM reservations WHERE namespace=? AND month=?', (namespace,month)).fetchall()
            total = sum((Decimal(r[0]) for r in rows),Decimal(0))
            run_total = sum((Decimal(r[0]) for r in db.execute('SELECT cost FROM reservations WHERE namespace=? AND run=?',(namespace,run))),Decimal(0))
            if cost and (total+cost>self.monthly or run_total+cost>self.per_run): raise BudgetExceeded('Cost limit reached')
            for unit, limit in self.limits.items():
                used = sum(json.loads(row[1]).get(unit,0) for row in rows)
                if used+units.get(unit,0)>limit: raise BudgetExceeded('Unit limit reached')
            if rate_limit and db.execute('SELECT COUNT(*) FROM requests WHERE namespace=? AND provider=? AND at>?',(namespace,provider,stamp-60)).fetchone()[0]>=rate_limit:
                raise BudgetExceeded('Rate limit reached')
            db.execute('DELETE FROM requests WHERE at<?',(stamp-86400,))
            db.execute('INSERT INTO requests VALUES (?,?,?)',(namespace,provider,stamp))
            ident = uuid.uuid4().hex
            db.execute('INSERT INTO reservations VALUES (?,?,?,?,?,?,?)',(ident,namespace,month,run,provider,str(cost),json.dumps(units,sort_keys=True)))
            return ident

    def summary(self, namespace, run):
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute('SELECT provider,cost,units FROM reservations WHERE namespace=? AND run=?',(namespace,run)).fetchall()
        providers = {}
        for provider,cost,units in rows:
            item = providers.setdefault(provider,{'reserved_eur':Decimal(0),'attempts':0,'units':{}})
            item['reserved_eur'] += Decimal(cost); item['attempts'] += 1
            for unit,value in json.loads(units).items(): item['units'][unit]=item['units'].get(unit,0)+value
        for value in providers.values():value['reserved_eur']=str(value['reserved_eur'])
        return {'run_id':run,'providers':providers,'note':'Conservative reservations, not an external invoice'}

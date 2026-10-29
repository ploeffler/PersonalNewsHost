#!/usr/bin/env python3
"""Retry only transient Presseportal failures once, with a small request budget."""
import concurrent.futures as cf
import json
from pathlib import Path
import time
from collect import probe
OUT=Path(__file__).resolve().parent
p=OUT/'checks.json';data=json.loads(p.read_text())
failed=[(i,r) for i,r in enumerate(data['feeds']) if r['source_type']=='pressportal_station' and r['status']=='unavailable' and '503' in r.get('error','')]
def retry(pair):
 i,r=pair
 time.sleep(0.75)
 result=probe({k:v for k,v in r.items() if k not in ('error','status','checked_at')})
 result['previous_check']={'status':r['status'],'error':r.get('error'),'checked_at':r['checked_at']}
 return i,result
with cf.ThreadPoolExecutor(max_workers=2) as pool:
 for i,row in pool.map(retry,failed):data['feeds'][i]=row
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Retried',len(failed),'transient errors; remaining',sum(r['status']=='unavailable' for r in data['feeds']))

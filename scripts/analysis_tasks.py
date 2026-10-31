"""Strict schemas and deterministic baselines, not independent factual verification."""
STRING={'type':'string','maxLength':1000}

def obj(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}

SCHEMAS={
    'summary':obj({'text':STRING,'source_ids':{'type':'array','items':STRING}}),
    'entities':obj({'entities':{'type':'array','items':obj({'text':STRING,'type':{'enum':['person','place','organization','other']}})}}),
    'classification':obj({'category':STRING}),
    'relevance':obj({'score':{'type':'number','minimum':0,'maximum':1}}),
    'bias':obj({'note':STRING,'assessed':{'const':False}}),
    'duplicates':obj({'candidate_ids':{'type':'array','items':STRING},'assessed':{'const':False}}),
    'headline':obj({'text':STRING}),
}

def baseline(task,payload):
    if task=='summary':return {'text':payload.get('text',payload.get('title',''))[:1000],'source_ids':[payload['source_id']] if payload.get('source_id') else []}
    if task=='entities':return {'entities':[]}
    if task=='classification':return {'category':'general'}
    if task=='relevance':return {'score':0}
    if task=='bias':return {'note':'Not assessed by the deterministic baseline','assessed':False}
    if task=='duplicates':return {'candidate_ids':[],'assessed':False}
    if task=='headline':return {'text':payload.get('title','')[:1000]}
    raise ValueError('Unsupported analysis task')

"""HotpotQA ingestion and deterministic disjoint allocation. No downloads implicit."""
import json, random, hashlib
from .core import normalize, bm25

def load_hotpot(path):
    with open(path) as f: rows=json.load(f)
    ids=set()
    if not isinstance(rows,list): raise ValueError('Expected HotpotQA JSON list')
    for r in rows:
        for key in ('_id','question','answer','context','supporting_facts','type'):
            if key not in r: raise ValueError('Missing '+key)
        if not all(isinstance(r[k],str) and r[k].strip() for k in ('_id','question','answer','type')): raise ValueError('Invalid string field')
        if not isinstance(r['context'],list) or not all(isinstance(x,list) and len(x)==2 and isinstance(x[0],str) and isinstance(x[1],list) and all(isinstance(t,str) for t in x[1]) for x in r['context']): raise ValueError('Invalid paragraphs')
        if r['_id'] in ids: raise ValueError('Duplicate question')
        ids.add(r['_id']); ctx=dict(r['context'])
        if len(ctx)!=len(r['context']): raise ValueError('Duplicate context title')
        if not r['supporting_facts']: raise ValueError('No evidence')
        for t,i in r['supporting_facts']:
            if t not in ctx or not isinstance(i,int) or i<0 or i>=len(ctx[t]):
                raise ValueError('Missing gold evidence')
    return rows

def evidence_keys(r):
    ctx=dict(r['context'])
    return {normalize(t) for t,_ in r['supporting_facts']}, {normalize(ctx[t][i]) for t,i in r['supporting_facts']}

def allocate(rows,counts,seed=20261025):
    """counts maps split -> {bridge:n, comparison:n}; quotas fixed before outcomes."""
    rng=random.Random(seed); pool=list(rows);rng.shuffle(pool)
    used_ids=set();used_titles=set();used_text=set();out={};excluded=[]
    for split,quota in counts.items():
        out[split]=[]
        for typ,n in quota.items():
            if not isinstance(n,int) or n<0: raise ValueError("Invalid allocation quota")
            if n==0: continue
            chosen=0
            for r in pool:
                if r['_id'] in used_ids or r['type']!=typ:continue
                titles,text=evidence_keys(r)
                if titles&used_titles or text&used_text:
                    excluded.append({'id':r['_id'],'reason':'evidence_overlap'});continue
                out[split].append(r);used_ids.add(r['_id']);used_titles|=titles;used_text|=text;chosen+=1
                if chosen==n:break
            if chosen!=n:raise ValueError(f'Insufficient eligible {typ} in {split}')
    return out,excluded

def chunks(r):
    return [{'id':f'{title}:{i}','title':title,'sentence':i,'text':text} for title,ss in r['context'] for i,text in enumerate(ss)]

def donor_candidates(question,answer,donors,excluded_titles,difficulty):
    """Lexical pools only. Human approval is mandatory before construction."""
    forbidden={normalize(x) for x in excluded_titles};a=normalize(answer)
    eligible=[d for d in donors if normalize(d['title']) not in forbidden and (a in ('yes','no','noanswer') or (' '+a+' ') not in (' '+normalize(d['text'])+' '))]
    unique={hashlib.sha256(d['text'].encode()).hexdigest():d for d in eligible}
    eligible=list(unique.values()); scores=bm25(question,[d['text'] for d in eligible])
    order=sorted(range(len(eligible)),key=lambda i:(scores[i],eligible[i]['id']))
    n=len(order)
    keep=order[:max(1,n//4)] if difficulty=='irrelevant' else order[max(0,n-max(1,n//10)):]
    return [dict(eligible[i],lexical_score=scores[i],review_status='pending') for i in keep]

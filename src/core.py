"""CPU research scaffold. Fixtures are software tests, never research results."""
import re, string, math, random, hashlib
from collections import Counter
from itertools import product

CONDITIONS = [dict(id=f'C{i+1}', length=l, position=p, difficulty=d,
                   selection='development' if i in (0,3,5,6) else 'heldout')
              for i,(l,p,d) in enumerate(product((4096,16384),('middle','end'),('irrelevant','similar')))]

def normalize(s):
    s=''.join(c for c in s.lower() if c not in string.punctuation)
    return ' '.join(re.sub(r'\b(a|an|the)\b',' ',s).split())

def answer_metrics(pred,gold):
    p,g=normalize(pred),normalize(gold)
    em=int(p==g)
    if (p in ('yes','no','noanswer') or g in ('yes','no','noanswer')) and p!=g:
        return em,0.0
    a,b=p.split(),g.split(); overlap=sum((Counter(a)&Counter(b)).values())
    if not overlap: return em,0.0
    return em,2*overlap/(len(a)+len(b))

def validate_splits(splits):
    ids=set(); titles=set()
    for name,rows in splits.items():
        local_ids=[r['_id'] for r in rows]
        local_titles={t for r in rows for t,_ in r['supporting_facts']}
        if len(local_ids)!=len(set(local_ids)) or ids.intersection(local_ids):
            raise ValueError('question leakage or duplicates')
        if titles & local_titles: raise ValueError('gold-title leakage')
        ids.update(local_ids); titles.update(local_titles)
    return True

def bm25(query,docs,k1=1.5,b=0.75):
    """Transparent positive-IDF BM25 prototype; NOT rank_bm25 equivalence."""
    tok=lambda s: re.findall(r'\w+',s.lower())
    ds=[tok(x) for x in docs]; n=len(ds)
    if not n:return []
    avg=sum(map(len,ds))/n
    if not avg:return [0.0]*n
    df=Counter(w for d in ds for w in set(d)); q=tok(query)
    out=[]
    for d in ds:
        tf=Counter(d); score=0.0
        for w in q:
            f=tf[w]
            if f: score+=math.log(1+(n-df[w]+.5)/(df[w]+.5))*f*(k1+1)/(f+k1*(1-b+b*len(d)/avg))
        out.append(score)
    return out

def pack(question,chunks,budget,count_tokens):
    scores=bm25(question,[c['text'] for c in chunks])
    rank=sorted(range(len(chunks)),key=lambda i:(-scores[i],i)); chosen=[]
    for i in rank:
        trial=sorted(chosen+[i]); text='\n'.join(chunks[j]['text'] for j in trial)
        if count_tokens(text)<=budget: chosen.append(i)
    return [chunks[i] for i in sorted(chosen)]

def place_evidence(donors,evidence,target,position,count_tokens,tolerance=.02):
    """Input donors are already reviewed, unique, whole sentences. No gold truncation."""
    goal=.5 if position=='middle' else .9
    candidates=[]
    for k in range(len(donors)+1):
        text='\n'.join(donors[:k]+[evidence]+donors[k:]); size=count_tokens(text)
        before=count_tokens('\n'.join(donors[:k]))
        mid=(before+count_tokens(evidence)/2)/size if size else 0
        candidates.append((abs(mid-goal),text,size,mid,k))
    err,text,size,mid,k=min(candidates,key=lambda x:x[0])
    if abs(size-target)>tolerance*target or err>.03:
        raise ValueError('length/position tolerance not met; revise donor pool')
    return dict(text=text,tokens=size,midpoint=mid,insertion_index=k,sha256=hashlib.sha256(text.encode()).hexdigest())

def paired_bootstrap(rows,seed=20261025,repeats=10000):
    """Rows: (question_id, paired difference). Preserve all variants per question."""
    groups={}
    for q,d in rows:groups.setdefault(q,[]).append(d)
    means=[sum(v)/len(v) for v in groups.values()]
    if len(means)<2:raise ValueError('need at least two independent questions')
    rng=random.Random(seed); n=len(means)
    samples=sorted(sum(rng.choices(means,k=n))/n for _ in range(repeats))
    return dict(estimate=sum(means)/n,low=samples[int(.025*repeats)],high=samples[min(repeats-1,int(.975*repeats))],n_questions=n)

if __name__=='__main__':
    import json
    print(json.dumps(CONDITIONS,indent=2))

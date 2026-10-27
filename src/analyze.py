"""Pair by question/model/condition. Incomplete pairs cause an explicit error."""
import json,argparse,csv
from .core import answer_metrics,paired_bootstrap

def score(rows,gold):
    out=[];seen=set()
    for r in rows:
        key=(r['question_id'],r['condition_id'],r['model_id'],r['method'])
        if key in seen:raise ValueError('Duplicate run identity')
        seen.add(key)
        if r['question_id'] not in gold:raise ValueError('Missing gold answer')
        em,f1=answer_metrics(r.get('parsed_answer',''),gold[r['question_id']]['answer']) if r['status']=='ok' else (0,0.)
        out.append(dict(r,em=em,f1=f1))
    return out

def compare(rows,model,method,conditions):
    groups={}
    for r in rows:
        if r['model_id']==model and r['condition_id'] in conditions and r['method'] in ('full',method):
            groups.setdefault((r['question_id'],r['condition_id']),{})[r['method']]=r['em']
    if not groups:raise ValueError('No observations')
    questions={q for q,c in groups}
    if any((q,c) not in groups or set(groups[q,c])!={'full',method} for q in questions for c in conditions):raise ValueError('Missing matched condition/method run')
    return paired_bootstrap([(q,v[method]-v['full']) for (q,c),v in groups.items()])

def select_policy(dev,cells,target):
    """Hamming-neighbor selection. Input is development score rows only."""
    if any(r['split']!='development' or cells[r['condition_id']]['selection']!='development' for r in dev):raise ValueError('Selection leakage')
    distance=lambda c:sum(c[k]!=target[k] for k in ('length','position','difficulty'))
    near=min(distance(cells[r['condition_id']]) for r in dev)
    rows=[r for r in dev if distance(cells[r['condition_id']])==near]
    coverage={}
    for r in rows:coverage.setdefault(r['method'],set()).add((r['question_id'],r['condition_id']))
    if len({frozenset(v) for v in coverage.values()})!=1:raise ValueError('Unequal method coverage')
    methods={r['method'] for r in rows};priority={'full':0,'bm25':1,'evidence':2,'longllmlingua':3}
    def key(m):
        rr=[r for r in rows if r['method']==m]
        return (-sum(r['em'] for r in rr)/len(rr),sum(r['end_to_end_seconds'] for r in rr)/len(rr),priority[m])
    return min(methods,key=key)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('runs');ap.add_argument('gold');ap.add_argument('output');a=ap.parse_args()
    rows=score([json.loads(x) for x in open(a.runs)],json.load(open(a.gold)))
    with open(a.output,'w') as f:
        for r in rows:f.write(json.dumps(r)+'\n')
if __name__=='__main__':main()

def holm(pvalues):
    ordered=sorted(enumerate(pvalues),key=lambda x:x[1]);adjusted=[0.]*len(pvalues);prev=0.
    for rank,(i,p) in enumerate(ordered):
        if not 0<=p<=1:raise ValueError('Invalid p value')
        prev=max(prev,min(1.,(len(pvalues)-rank)*p));adjusted[i]=prev
    return adjusted

def retention(gold_ids,retained_ids):
    gold=set(gold_ids)
    if not gold:raise ValueError('No gold facts')
    present=gold & set(retained_ids)
    return {'fact_recall':len(present)/len(gold),'complete_retention':int(present==gold)}

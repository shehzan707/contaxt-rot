"""Real benchmark allocation and reserved donor pool, without inference."""
import argparse,json,hashlib
from pathlib import Path
from .data import load_hotpot,allocate,evidence_keys,chunks
from .core import normalize,validate_splits

def prepare(path,destination):
    raw=json.loads(Path(path).read_text())
    invalid=[];eligible=[]
    for r in raw:
        ctx=dict(r['context'])
        if any(t not in ctx or type(i) is not int or i<0 or i>=len(ctx[t]) for t,i in r['supporting_facts']):
            invalid.append({'question_id':r['_id'],'reason':'supporting_fact_out_of_bounds'})
        else:eligible.append(r)
    dest=Path(destination);dest.mkdir(parents=True,exist_ok=True)
    (dest/'invalid_records.json').write_text(json.dumps(invalid,indent=2))
    valid_path=dest/'eligible.json';valid_path.write_text(json.dumps(eligible))
    rows=load_hotpot(valid_path)
    quotas={'pilot':{'bridge':1,'comparison':1},'development':{'bridge':9,'comparison':3},'test':{'bridge':32,'comparison':8}}
    splits,excluded=allocate(rows,quotas);validate_splits(splits)
    selected=[r for rr in splits.values() for r in rr];ids={r['_id'] for r in selected}
    titles={normalize(t) for r in selected for t,_ in r['context']}
    texts={normalize(s) for r in selected for _,ss in r['context'] for s in ss}
    pool=[];seen=set()
    for r in rows:
        if r['_id'] in ids:continue
        for c in chunks(r):
            h=hashlib.sha256(c['text'].encode()).hexdigest()
            if normalize(c['title']) in titles or normalize(c['text']) in texts or h in seen:continue
            seen.add(h);pool.append(dict(c,source_question_id=r['_id'],text_sha256=h,review_status='pending'))
    dest=Path(destination);dest.mkdir(parents=True,exist_ok=True)
    for split,rr in splits.items():(dest/(split+'.json')).write_text(json.dumps(rr))
    (dest/'donor_pool.json').write_text(json.dumps(pool))
    report={'dataset_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'records':len(rows),'raw_records':len(raw),'invalid_excluded':invalid,'seed':20261025,'quotas':quotas,'question_ids':{s:[r['_id'] for r in rr] for s,rr in splits.items()},'donor_sentences':len(pool),'question_and_evidence_split_checks':'passed','context_status':'pending tokenizer and human review'}
    (dest/'manifest.json').write_text(json.dumps(report,indent=2))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('hotpot_json');p.add_argument('destination');a=p.parse_args()
    print(json.dumps(prepare(a.hotpot_json,a.destination),indent=2))
if __name__=='__main__':main()

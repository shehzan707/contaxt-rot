"""Construct matched position variants from reviewed sentence pools."""
import hashlib
from .core import place_evidence

def construct_pair(evidence,donors,target,count):
    if any(d.get('review_status')!='approved' for d in donors):raise ValueError('Unreviewed donors')
    seen=set(); selected=[]
    for d in donors:
        if d['id'] in seen: raise ValueError('Duplicate donor ID')
        seen.add(d['id'])
        if count('\n'.join([x['text'] for x in selected]+[d['text'],evidence]))<=target*1.02:
            selected.append(d)
    if not selected:raise ValueError('No donor text fits')
    texts=[d['text'] for d in selected]
    result={pos:place_evidence(texts,evidence,target,pos,count) for pos in ('middle','end')}
    for v in result.values():v['donor_ids']=[d['id'] for d in selected]
    return result

def construct_nested(evidence,donors,count):
    long=construct_pair(evidence,donors,16384,count)
    ids=set(long['middle']['donor_ids'])
    short=construct_pair(evidence,[d for d in donors if d['id'] in ids],4096,count)
    return {'4096':short,'16384':long}

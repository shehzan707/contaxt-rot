"""Fail-closed run planning, gold isolation and append-only resume validation."""
import json, hashlib
from pathlib import Path

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
def no_gold(value):
    if isinstance(value,dict):
        if any(k.lower() in {'answer','gold','gold_answer','supporting_facts','gold_evidence'} for k in value):
            raise ValueError('Gold annotations must remain in scoring files')
        for v in value.values():no_gold(v)
    elif isinstance(value,list):
        for v in value:no_gold(v)

def plan(rows,cfg,spec,method,split,conditions):
    if not spec.get('active',True): raise ValueError('Inactive model')
    if method not in cfg['methods']: raise ValueError('Unknown method')
    if split not in ('pilot','development','test'):raise ValueError('Unknown split')
    valid=set(cfg['conditions_development']+cfg['conditions_heldout'])
    if not conditions or not set(conditions)<=valid:raise ValueError('Unknown condition')
    if split=='development' and not set(conditions)<=set(cfg['conditions_development']):raise ValueError('Held-out development forbidden')
    selected=[];seen=set()
    for r in rows:
        if r['split']!=split or r['condition_id'] not in conditions:continue
        no_gold(r)
        if r.get('review_status')!='approved':raise ValueError('Human context review required')
        if not r.get('question') or not r.get('chunks'):raise ValueError('Empty context/question')
        ids=[c['id'] for c in r['chunks']]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate chunks')
        cell=(r['question_id'],r['condition_id'])
        if cell in seen:raise ValueError('Duplicate context cell')
        seen.add(cell)
        source='\n'.join(c['text'] for c in r['chunks'])
        h=hashlib.sha256(source.encode()).hexdigest()
        if r.get('context_hash')!=h:raise ValueError('Context hash mismatch')
        key=digest([split,*cell,spec,method,digest(cfg),h])
        selected.append((r,dict(run_id=key,experiment_id='context-rot-'+cfg['version'],config_hash=digest(cfg),context_hash=h,source_hash=h,question_id=cell[0],condition_id=cell[1],split=split,model_id=spec['id'],checkpoint=spec.get('handle'),revision=spec.get('revision'),method=method)))
    if not selected:raise ValueError('No matching contexts')
    qs={r['question_id'] for r,_ in selected}
    if len(selected)!=len(qs)*len(conditions):raise ValueError('Incomplete condition grid')
    return selected

def read_log(path,config_hash):
    if not Path(path).exists():return {}
    done={}
    for i,line in enumerate(Path(path).read_text().splitlines(),1):
        try:r=json.loads(line)
        except Exception as e:raise ValueError(f'Malformed JSONL line {i}; preserve file and repair explicitly') from e
        if r.get('config_hash')!=config_hash:raise ValueError('Different config in output')
        if r['run_id'] in done:raise ValueError('Duplicate run ID')
        done[r['run_id']]=r
    return done

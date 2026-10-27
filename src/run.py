"""Explicit Part 2 runner. Default action is planning; --execute is required."""
import argparse,json,time,os,random
from pathlib import Path
from .infer import load,generate
from .methods import prompt,retrieve
from .validation import digest,plan,read_log

def append(path,row):
    with open(path,'a') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--approved-manifest',required=True)
    ap.add_argument('--config',default='configs/protocol.json');ap.add_argument('--contexts',required=True)
    ap.add_argument('--model',type=int,default=0);ap.add_argument('--method',choices=['full','bm25','longllmlingua','evidence'],required=True)
    ap.add_argument('--split',choices=['pilot','development','test'],required=True)
    ap.add_argument('--conditions',nargs='+',required=True);ap.add_argument('--limit',type=int)
    ap.add_argument('--output',required=True);ap.add_argument('--execute',action='store_true')
    a=ap.parse_args();cfg=json.loads(Path(a.config).read_text())
    if a.model!=0:raise ValueError('Only primary Gemma is active')
    from .kaggle_model import file_hash
    approved=json.loads(Path(a.approved_manifest).read_text())
    if approved.get('contexts_sha256')!=file_hash(a.contexts):raise ValueError('Approved context manifest mismatch')
    if not approved.get('review_sha256') or not approved.get('tokenizer_files'):raise ValueError('Incomplete approved manifest')
    spec=cfg['models'][0];rows=[json.loads(s) for s in Path(a.contexts).read_text().splitlines() if s.strip()]
    jobs=plan(rows,cfg,spec,a.method,a.split,a.conditions)
    for _,base in jobs:base['data_manifest_hash']=file_hash(a.approved_manifest)
    random.Random(cfg['seed']).shuffle(jobs)
    if a.limit is not None:
        if a.limit<1:raise ValueError('Positive limit required')
        jobs=jobs[:a.limit]
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    manifest=out.with_suffix('.expected.json');expected=[b for _,b in jobs]
    if manifest.exists() and json.loads(manifest.read_text())!=expected:raise ValueError('Expected manifest changed; choose a new output')
    if not manifest.exists():manifest.write_text(json.dumps(expected,indent=2))
    done=read_log(out,digest(cfg))
    if set(done)-{b['run_id'] for b in expected}:raise ValueError('Unexpected run in output')
    failed=[k for k,v in done.items() if v['status']!='ok']
    if failed:raise ValueError('Previous failed/truncated runs: preserve logs and explicitly plan a separate retry output')
    pending=[(r,b) for r,b in jobs if b['run_id'] not in done]
    print(json.dumps({'expected':len(jobs),'completed':len(done),'pending':len(pending),'execute':a.execute}))
    if not a.execute or not pending:return
    import torch
    torch.manual_seed(cfg['seed']);torch.cuda.manual_seed_all(cfg['seed'])
    model,tok=load(spec);count=lambda s:len(tok.encode(s,add_special_tokens=False))
    from .core import CONDITIONS
    lengths={c['id']:c['length'] for c in CONDITIONS}
    for name,h in approved['tokenizer_files'].items():
        if model.research_manifest['files_sha256'].get(name)!=h:raise ValueError('Context tokenizer/checkpoint mismatch')
    for r,base in pending:
        base.update(native_input_tokens=None,output_tokens=None,raw_output=None,parsed_answer=None,generation_seconds=None,preprocessing_seconds=None,end_to_end_seconds=None,peak_allocated_bytes=None,error=None)
        start=time.perf_counter()
        try:
            used=r['chunks']
            actual=count('\n'.join(c['text'] for c in used))
            if abs(actual-lengths[r['condition_id']])>lengths[r['condition_id']]*.02:raise ValueError('Context reference length mismatch')
            if a.method=='bm25':used=retrieve(r['question'],used,cfg['retrieval_budget'],count)
            context='\n'.join(c['text'] for c in used);prep=time.perf_counter()-start
            if a.method=='longllmlingua':
                cache=r.get('compression')
                if not cache or cache['source_hash']!=base['context_hash'] or cache['config_hash']!=digest(cfg):raise ValueError('Verified compression artifact required')
                context=cache['text'];prep+=cache['preprocessing_seconds']
                if count(context)>cfg['compression_budget']*1.02:raise ValueError('Compression budget exceeded')
            result=generate(model,tok,spec,prompt(r['question'],context,a.method),cfg['max_new_tokens'])
            base.update(result,preprocessing_seconds=prep,end_to_end_seconds=prep+result['generation_seconds'],retained_ids=[i for c in used for i in c.get('source_ids',[c['id']])] if a.method!='longllmlingua' else None)
        except Exception as e:
            base.update(status='error',error=type(e).__name__+': '+str(e),end_to_end_seconds=time.perf_counter()-start)
        append(out,base)
if __name__=='__main__':main()

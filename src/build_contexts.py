"""Two-step human review queue and context construction; no generation."""
import argparse,json,hashlib
from pathlib import Path
from .data import donor_candidates,chunks
from .context import construct_nested
from .core import CONDITIONS
from .validation import no_gold
from .kaggle_model import file_hash

def queue(root, splits=('pilot',)):
 root=Path(root);donors=json.loads((root/'donor_pool.json').read_text());out=[]
 for split in splits:
  for r in json.loads((root/(split+'.json')).read_text()):
   for difficulty in ('irrelevant','similar'):
    candidates=donor_candidates(r['question'],r['answer'],donors,[t for t,_ in r['context']],difficulty)
    out.append({'question_id':r['_id'],'split':split,'difficulty':difficulty,'question':r['question'],'review_status':'pending','reviewer':None,'review_notes':None,'donors':candidates[:2048]})
 path=root/'review_queue.json'
 if path.exists():raise ValueError('Preserve existing human-review queue')
 path.write_text(json.dumps(out));return len(out)

def build(root,tokenizer_path):
 from transformers import AutoTokenizer
 root=Path(root);tok=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True)
 count=lambda s:len(tok.encode(s,add_special_tokens=False))
 reviews=json.loads((root/'review_queue.json').read_text());index={}
 for x in reviews:
  key=(x['question_id'],x['difficulty'])
  if key in index:raise ValueError('Duplicate review')
  index[key]=x
 output=[];gold={};checks=[]
 for split in sorted({x['split'] for x in reviews}):
  for r in json.loads((root/(split+'.json')).read_text()):
   all_chunks=chunks(r);facts={f'{t}:{i}' for t,i in r['supporting_facts']}
   evidence=[c for c in all_chunks if c['id'] in facts]
   if len(evidence)!=len(facts):raise ValueError('Incomplete evidence')
   gold[r['_id']]={'answer':r['answer'],'supporting_facts':r['supporting_facts'],'source_ids':sorted(facts)}
   e={'id':'evidence-block-'+r['_id'],'text':'\n'.join(c['text'] for c in evidence),'source_ids':[c['id'] for c in evidence]}
   for difficulty in ('irrelevant','similar'):
    review=index[(r['_id'],difficulty)]
    if review['review_status']!='approved' or not review.get('reviewer') or not review.get('review_notes'):raise ValueError('Documented human approval required')
    donors=[d for d in review['donors'] if d.get('review_status')=='approved']
    if any(hashlib.sha256(d['text'].encode()).hexdigest()!=d['text_sha256'] for d in donors):raise ValueError('Reviewed donor content changed')
    pairs=construct_nested(e['text'],donors,count);by_id={d['id']:d for d in donors}
    for c in CONDITIONS:
     if c['difficulty']!=difficulty or (split=='development' and c['selection']!='development'):continue
     v=pairs[str(c['length'])][c['position']];ordered=[by_id[i] for i in v['donor_ids']]
     ordered[v['insertion_index']:v['insertion_index']]=evidence
     clean=[{k:d[k] for k in ('id','text','source_ids') if k in d} for d in ordered]
     text='\n'.join(d['text'] for d in clean)
     if text!=v['text']:raise ValueError('Provenance reconstruction failed')
     row=dict(question_id=r['_id'],question=r['question'],split=split,condition_id=c['id'],chunks=clean,context_hash=v['sha256'],reference_tokens=v['tokens'],native_context_tokens=count(text),review_status='approved')
     no_gold(row);output.append(row)
     checks.append(dict(question_id=r['_id'],condition_id=c['id'],midpoint=v['midpoint'],tokens=v['tokens'],context_hash=v['sha256'],evidence_complete=True))
 dest=root/'contexts.jsonl'
 if dest.exists():raise ValueError('Do not overwrite frozen contexts')
 dest.write_text(''.join(json.dumps(r)+'\n' for r in output))
 (root/'gold.json').write_text(json.dumps(gold))
 (root/'context_checks.json').write_text(json.dumps(checks,indent=2))
 tokenizer_files={f.name:file_hash(f) for f in Path(tokenizer_path).glob('*') if f.is_file() and ('token' in f.name or f.name.endswith('.json'))}
 (root/'approved_manifest.json').write_text(json.dumps({'contexts_sha256':file_hash(dest),'review_sha256':file_hash(root/'review_queue.json'),'tokenizer_files':tokenizer_files,'records':len(output)},indent=2))
 return len(output)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['queue','build']);ap.add_argument('root');ap.add_argument('--tokenizer-path');ap.add_argument('--splits',nargs='+',default=['pilot'],choices=['pilot','development','test']);a=ap.parse_args()
 if a.action=='queue':print(queue(a.root,a.splits))
 else:
  if not a.tokenizer_path:ap.error('--tokenizer-path required')
  print(build(a.root,a.tokenizer_path))

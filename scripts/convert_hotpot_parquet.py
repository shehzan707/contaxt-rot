"""Documented fallback: public hotpotqa/hotpot_qa validation distribution."""
import json,hashlib
from pathlib import Path
import pyarrow.parquet as pq
source=Path('data/hotpot_validation.parquet')
rows=pq.read_table(source).to_pylist();out=[]
for r in rows:
 out.append({'_id':r['id'],'question':r['question'],'answer':r['answer'],'type':r['type'],'level':r['level'],'context':list(zip(r['context']['title'],r['context']['sentences'])),'supporting_facts':list(zip(r['supporting_facts']['title'],r['supporting_facts']['sent_id']))})
p=Path('data/hotpot_dev_distractor_v1.json');p.write_text(json.dumps(out))
Path('reports/dataset_source.json').write_text(json.dumps({'source':'https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/distractor/validation-00000-of-00001.parquet','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'converted_json_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'records':len(out),'reason':'CMU original HTTP and HTTPS returned 503; public HotpotQA namespace Parquet distribution used without authentication. Logical schema conversion; not byte-equivalent to original JSON.'},indent=2))

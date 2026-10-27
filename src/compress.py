"""Offline compression phase. Never co-load the answer model."""
import argparse,json,time,hashlib,re
from .methods import compress
from .run import digest

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--contexts',required=True);p.add_argument('--output',required=True);p.add_argument('--scorer-path',required=True);p.add_argument('--reference-path',required=True);p.add_argument('--scorer-manifest',required=True);p.add_argument('--approved-manifest',required=True);a=p.parse_args()
    cfg=json.load(open(a.config));rev=cfg.get('compressor_revision')
    if not rev or not re.fullmatch('[0-9a-f]{40}',rev):raise ValueError('Pin compressor revision')
    from pathlib import Path
    from .kaggle_model import file_hash
    from .validation import no_gold
    approved=json.loads(Path(a.approved_manifest).read_text())
    if approved.get('contexts_sha256')!=file_hash(a.contexts):raise ValueError('Context manifest mismatch')
    output_manifest=Path(a.output).with_suffix('.approved.json')
    if output_manifest.exists():raise ValueError('Preserve existing compression manifest')
    manifest=json.loads(Path(a.scorer_manifest).read_text())
    if manifest.get('id')!=cfg['compressor_model'] or manifest.get('revision')!=rev:raise ValueError('Scorer identity mismatch')
    if not manifest.get('files_sha256'):raise ValueError('Checkpoint checksums required')
    for name,checksum in manifest['files_sha256'].items():
        f=(Path(a.scorer_path)/name).resolve()
        if not f.is_relative_to(Path(a.scorer_path).resolve()) or file_hash(f)!=checksum:raise ValueError('Scorer file checksum mismatch')
    from transformers import AutoTokenizer
    local=a.scorer_path
    tok=AutoTokenizer.from_pretrained(a.reference_path,local_files_only=True);count=lambda x:len(tok.encode(x,add_special_tokens=False))
    with open(a.output,'x') as out:
        for line in open(a.contexts):
            r=json.loads(line);no_gold(r)
            if r.get('review_status')!='approved':raise ValueError('Review required')
            if r['split']=='development' and r['condition_id'] not in cfg['conditions_development']:raise ValueError('Held-out development forbidden')
            passages=[x['text'] for x in r['chunks']];source='\n'.join(passages)
            start=time.perf_counter();text,meta=compress(r['question'],passages,local,cfg['compression_budget'],count)
            r['compression']={'text':text,'source_hash':hashlib.sha256(source.encode()).hexdigest(),'config_hash':digest(cfg),'preprocessing_seconds':time.perf_counter()-start,'compressor_revision':rev,'metadata':meta,'processed_scorer_tokens':None,'forward_passes':None}
            out.write(json.dumps(r)+'\n');out.flush()
    approved.update(contexts_sha256=file_hash(a.output),uncompressed_manifest_sha256=file_hash(a.approved_manifest),compressor_manifest_sha256=file_hash(a.scorer_manifest))
    output_manifest.write_text(json.dumps(approved,indent=2))
if __name__=='__main__':main()

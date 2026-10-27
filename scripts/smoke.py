"""Bounded non-research checks. No HotpotQA question or evaluation execution."""
import json,gc
from pathlib import Path
from src.infer import load,generate
from src.run import append
from src.kaggle_model import file_hash

def main():
 cfg=json.loads(Path('configs/protocol.json').read_text());spec=cfg['models'][0]
 out=Path('results/technical_smoke.jsonl')
 if out.exists():raise ValueError('Preserve existing smoke log; choose another run directory')
 model,tok=load(spec)
 Path('reports/checkpoint_manifest.json').write_text(json.dumps(model.research_manifest,indent=2))
 for target in [32,4096,16384]:
  text='This is a synthetic technical memory check. '
  if target==32:text='Reply with the word READY.'
  else:
   text=text*(target//5+1)
   text=tok.decode(tok.encode(text,add_special_tokens=False)[:target])
  try:r=generate(model,tok,spec,text,128)
  except Exception as e:r={'status':'error','error':type(e).__name__+': '+str(e)}
  r.update(non_research=True,target_context_tokens=target,checkpoint=spec['handle']);append(out,r);print(json.dumps(r))
  if r['status']=='error':break
 del model,tok;gc.collect()
 import torch
 torch.cuda.empty_cache()
if __name__=='__main__':main()

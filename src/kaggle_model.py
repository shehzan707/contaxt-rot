"""Official version-pinned Kaggle Gemma checkpoint; never accepts licences."""
import hashlib, json, re
from pathlib import Path
HANDLE = 'google/gemma-3/transformers/gemma-3-4b-it/1'

def validate_spec(spec):
    if spec.get('provider')!='kaggle' or spec.get('id')!='google/gemma-3-4b-it':
        raise ValueError('Approved Gemma Kaggle model required')
    if not re.fullmatch(r'google/gemma-3/transformers/gemma-3-4b-it/[1-9][0-9]*',spec.get('handle','')):
        raise ValueError('Explicit Kaggle version required')
    if spec.get('dtype')!='bfloat16': raise ValueError('Precision amendment required')

def file_hash(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()

def checkpoint(spec):
    validate_spec(spec)
    import kagglehub
    root=Path(kagglehub.model_download(spec['handle']))
    config=json.loads((root/'config.json').read_text())
    if config.get('model_type')!='gemma3': raise ValueError('Wrong checkpoint architecture')
    files={str(f.relative_to(root)):file_hash(f) for f in sorted(root.rglob('*')) if f.is_file()}
    if not any(f.endswith('.safetensors') for f in files): raise ValueError('Missing weights')
    return root,dict(provider='kaggle',handle=spec['handle'],files_sha256=files,architecture=config.get('architectures'))

def load_kaggle(spec):
    validate_spec(spec)
    import torch
    from transformers import Gemma3ForConditionalGeneration, AutoProcessor
    if not torch.cuda.is_available(): raise RuntimeError('CUDA required')
    if not torch.cuda.is_bf16_supported(): raise RuntimeError('BF16 unsupported: obtain suitable GPU or approve precision amendment')
    root,manifest=checkpoint(spec)
    processor=AutoProcessor.from_pretrained(root,local_files_only=True)
    model=Gemma3ForConditionalGeneration.from_pretrained(root,local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'})
    model.eval()
    model.research_manifest=manifest
    model.research_processor=processor
    return model,processor.tokenizer

"""GPU adapter; real model validation still required. Refuses mutable snapshots and prompt truncation."""
import re, time

def load(model_spec):
    if model_spec.get('provider')=='kaggle':
        from .kaggle_model import load_kaggle
        return load_kaggle(model_spec)
    revision=model_spec.get('revision')
    if not revision or not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Resolve and freeze actual 40-character model commit first')
    import torch, transformers
    if not torch.cuda.is_available():raise RuntimeError('CUDA GPU required by this execution protocol')
    cls=getattr(transformers,model_spec['loader'])
    model=cls.from_pretrained(model_spec['id'],revision=revision,torch_dtype=torch.bfloat16,device_map='auto')
    tokenizer=transformers.AutoTokenizer.from_pretrained(model_spec['id'],revision=revision)
    return model,tokenizer

def generate(model,tokenizer,spec,prompt,max_new_tokens=128):
    import torch
    kw={'enable_thinking':False} if 'Qwen3.5' in spec['id'] else {}
    text=tokenizer.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True,**kw)
    tokens=tokenizer(text,return_tensors='pt',add_special_tokens=False)
    cfg=getattr(model.config,'text_config',model.config)
    limit=getattr(cfg,'max_position_embeddings',None)
    n=tokens['input_ids'].shape[-1]
    if limit is None or n+max_new_tokens>limit:raise ValueError('Unknown or exceeded model context limit')
    tokens={k:v.to(model.device) for k,v in tokens.items()}
    torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
    with torch.inference_mode():out=model.generate(**tokens,do_sample=False,max_new_tokens=max_new_tokens)
    torch.cuda.synchronize();elapsed=time.perf_counter()-start
    ids=out[0,n:];raw=tokenizer.decode(ids,skip_special_tokens=True)
    eos=model.generation_config.eos_token_id
    eos=[eos] if isinstance(eos,int) else (eos or [])
    status='truncated' if len(ids)>=max_new_tokens and int(ids[-1]) not in eos else 'ok'
    if not raw.strip():status='malformed_answer'
    if '<think>' in raw or '</think>' in raw:status='unexpected_thinking'
    return {'raw_output':raw,'parsed_answer':raw.strip(),'native_input_tokens':n,'output_tokens':len(ids),'generation_seconds':elapsed,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'status':status}

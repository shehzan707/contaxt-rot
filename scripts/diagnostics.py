import sys,json,shutil,platform,importlib.metadata as m,subprocess
from pathlib import Path
packages={}
for name in ['torch','transformers','accelerate','kagglehub','sentencepiece','rank-bm25','llmlingua','numpy','pandas','scipy','matplotlib']:
    try:packages[name]=m.version(name)
    except m.PackageNotFoundError:packages[name]=None
info={'python':sys.version,'platform':platform.platform(),'packages':packages,'disk_free':shutil.disk_usage('.').free,'gpu':None}
try:
 import torch
 info.update(cuda=torch.version.cuda,gpu_available=torch.cuda.is_available())
 if torch.cuda.is_available():info.update(gpu=torch.cuda.get_device_name(0),gpu_memory=torch.cuda.get_device_properties(0).total_memory,bf16_supported=torch.cuda.is_bf16_supported())
except ImportError:pass
try:
 import psutil
 info['system_memory']=psutil.virtual_memory().total
except ImportError:pass
Path('reports').mkdir(exist_ok=True)
Path('reports/environment_current.json').write_text(json.dumps(info,indent=2))
print(json.dumps(info,indent=2))

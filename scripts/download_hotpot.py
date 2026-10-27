"""Download only the official distractor development JSON; no model calls."""
import urllib.request,hashlib,json
from pathlib import Path
URL='http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json'
p=Path('data/hotpot_dev_distractor_v1.json');p.parent.mkdir(exist_ok=True)
if not p.exists():
    temp=p.with_suffix('.partial')
    with urllib.request.urlopen(URL,timeout=60) as response,temp.open('wb') as out:
        while chunk:=response.read(1024*1024):out.write(chunk)
    json.loads(temp.read_text());temp.replace(p)
print(json.dumps({'source':URL,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))

import json,argparse

def main():
    import matplotlib.pyplot as plt
    p=argparse.ArgumentParser();p.add_argument('scored_jsonl');p.add_argument('output_png');a=p.parse_args()
    rows=[json.loads(x) for x in open(a.scored_jsonl)]
    if not rows:raise ValueError('No actual results supplied')
    groups={}
    for r in rows:groups.setdefault((r['model_id'],r['method']),[]).append(r)
    fig,ax=plt.subplots(figsize=(10,6))
    for (model,method),rr in groups.items():
        if any('end_to_end_seconds' not in r for r in rr):raise ValueError('Missing latency')
        x=sum(r['end_to_end_seconds'] for r in rr)/len(rr);y=sum(r['em'] for r in rr)/len(rr)
        ax.scatter(x,y,label=model.split('/')[-1]+' / '+method)
    ax.set(xlabel='Mean end-to-end seconds',ylabel='Exact match proportion',ylim=(0,1));ax.legend(fontsize=7);fig.tight_layout();fig.savefig(a.output_png,dpi=200)
if __name__=='__main__':main()

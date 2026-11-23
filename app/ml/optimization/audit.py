"""Source-only bounded clone diagnostics and group construction; no test labels."""
from collections import Counter,defaultdict
import hashlib,re,time
import numpy as np
from app.ml.dataset import load_split, fingerprint
from app.ml.io import read_json,digest

KEYWORDS=set('auto break case char const continue default do double else enum extern float for goto if inline int long register restrict return short signed sizeof static struct switch typedef union unsigned void volatile while _Bool _Complex _Imaginary'.split())
TOKEN=re.compile(r'(?P<comment>/\*[\s\S]*?\*/|//[^\n]*)|(?P<string>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(?P<id>[A-Za-z_][A-Za-z_0-9]*)|(?P<number>\b[0-9][A-Za-z_0-9.]*\b)|(?P<other>==|!=|<=|>=|&&|\|\||->|\+\+|--|\S)')


def shape_tokens(source):
    out=[]
    for m in TOKEN.finditer(source):
        kind=m.lastgroup;s=m.group()
        if kind=='comment':continue
        out.append('I' if kind=='id' and s not in KEYWORDS else 'N' if kind=='number' else 'S' if kind=='string' else s)
    return out


def shape_hash(tokens):return hashlib.sha256(' '.join(tokens).encode()).hexdigest()


def shingles(tokens):
    if len(tokens)<20:return set()
    return {int.from_bytes(hashlib.blake2b(' '.join(tokens[i:i+5]).encode(),digest_size=8).digest(),'big') for i in range(len(tokens)-4)}


def near_matches(train_sets,other_sets,max_posting=64,max_candidates=50):
    """Bottom-24 hash inverted retrieval + verified Jaccard>=.85; bounded lower bound."""
    postings=defaultdict(list)
    for i,s in enumerate(train_sets):
        for h in sorted(s)[:24]:
            if len(postings[h])<=max_posting:postings[h].append(i)
    matched=set();pairs=[];scanned=0;capped=0;frequent=sum(len(v)>max_posting for v in postings.values())
    for j,s in enumerate(other_sets):
        counts=Counter(i for h in sorted(s)[:24] if len(postings.get(h,[]))<=max_posting for i in postings.get(h,[]))
        candidates=sorted(counts,key=lambda i:(-counts[i],i));capped+=len(candidates)>max_candidates
        for i in candidates[:max_candidates]:
            scanned+=1;other=train_sets[i];score=len(s&other)/len(s|other) if s|other else 0
            if score>=.85:
                matched.add(j)
                if len(pairs)<20:pairs.append({'train_index':i,'query_index':j,'jaccard':score})
                break
    return matched,{'matched_query_rows_lower_bound':len(matched),'verified_pairs_sample':pairs,
                    'candidate_comparisons':scanned,'capped_query_rows':capped,'frequent_postings_omitted':frequent,
                    'max_posting':max_posting,'max_candidates_per_query':max_candidates,'threshold':.85}


def grouped_ids(rows,shapes):
    parents=list(range(len(rows)))
    def find(x):
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parents[max(a,b)]=min(a,b)
    seen={}
    for i,(row,shape) in enumerate(zip(rows,shapes)):
        for key in [('shape',shape),('commit',row['project'],row['commit_id'])]:
            if key[0]=='commit' and not row['commit_id']:continue
            if key in seen:union(i,seen[key])
            else:seen[key]=i
    return np.array([find(i) for i in range(len(rows))])


def collect(raw,prepared):
    index=read_json(prepared/'row_index.json');metadata=read_json(prepared/'metadata.json')
    for name,expected in metadata['files'].items():
        if digest(prepared/name)!=expected:raise ValueError('Prepared data checksum mismatch')
    rows={}
    for split in ['train','validation']:
        original=load_split(raw,split);by_id={r['id']:r for r in original}
        rows[split]=[by_id[r['id']] for r in index[split]]
    rows['test_sources']=load_split(raw,'test',include_target=False)
    assert all('target' not in r for r in rows['test_sources'])
    with np.load(prepared/'development.npz',allow_pickle=False) as data:
        for split in ['train','validation']:
            assert np.array_equal(data['y_'+split],[int(r['target']) for r in rows[split]])
    return rows


def audit(rows):
    started=time.perf_counter();tokens={k:[shape_tokens(r['func']) for r in v] for k,v in rows.items()}
    shapes={k:[shape_hash(t) for t in v] for k,v in tokens.items()}
    sets={k:[shingles(t) for t in v] for k,v in tokens.items()}
    near={};matched={}
    for split in ['validation','test_sources']:
        matched[split],near[split]=near_matches(sets['train'],sets[split])
    train_commits={(r['project'],r['commit_id']) for r in rows['train'] if r['commit_id']}
    train_shapes=set(shapes['train']);reasons=Counter();mask=[]
    for i,(r,s) in enumerate(zip(rows['validation'],shapes['validation'])):
        flags=[]
        if (r['project'],r['commit_id']) in train_commits:flags.append('shared_project_commit')
        if s in train_shapes:flags.append('shared_token_shape')
        if i in matched['validation']:flags.append('verified_approximate_near_match')
        reasons.update(flags);mask.append(not flags)
    groups=grouped_ids(rows['train'],shapes['train']);sizes=Counter(groups.tolist())
    result={'test_labels_loaded':False,'scope':'Cleaned development; unchanged official test source-only audit.',
            'warning':'Token-shape/Jaccard are conservative lexical similarity heuristics, not semantic clone or label-error proof.',
            'rows':{k:len(v) for k,v in rows.items()},'groups':{'count':len(sizes),'largest':max(sizes.values())},
            'shape_duplicate_excess':{k:len(v)-len(set(v)) for k,v in shapes.items()},
            'cross_split_shape_rows':{k:sum(s in train_shapes for s in shapes[k]) for k in ['validation','test_sources']},
            'near_clone_search':near,'purged_validation':{'retained':sum(mask),'excluded':len(mask)-sum(mask),'overlapping_exclusion_reasons':dict(reasons)},
            'source_bytes':{},'seconds':time.perf_counter()-started}
    for k,rs in rows.items():
        lengths=np.asarray([len(r['func'].encode()) for r in rs]);result['source_bytes'][k]={str(p):float(np.percentile(lengths,p)) for p in [0,25,50,75,95,100]}
    return result,groups,np.asarray(mask,dtype=bool)

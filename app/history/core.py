"""Shared deterministic history aggregation and literal Git tree comparison."""
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import difflib
import json
import re
from collections import defaultdict
from app.errors import AnalysisError
from .models import LIMITS, Change, Coverage, History, Comparison

SHA = re.compile(r'[0-9a-f]{40}')


def revision(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise AnalysisError('Use a full 40-character Git commit identifier.', 'invalid_revision', 422)
    return value


def path(value):
    if (not isinstance(value, str) or not value or len(value.encode('utf-8')) > 2048
            or value.startswith('/') or '\\' in value or any(p in {'', '.', '..', '.git'} for p in value.split('/'))):
        raise AnalysisError('History contains an unsupported source path.', 'history_metadata', 502)
    return value


def text(value, maximum=512):
    if not isinstance(value, str):
        raise ValueError('Invalid text metadata')
    # Preserve readable evidence without terminal controls / bidi spoofing.
    clean=''.join(c if ord(c)>=32 and ord(c)!=127 and c not in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069' else f'\\u{ord(c):04x}' for c in value)
    return clean[:maximum]


def timestamp(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise ValueError('Timestamp requires timezone')
    return parsed.isoformat()


def aggregate(commits):
    days=defaultdict(int);files={}
    for c in commits:
        days[datetime.fromisoformat(c.committer_date).astimezone(timezone.utc).date().isoformat()]+=1
        for f in c.files:
            row=files.setdefault(f.path,dict(path=f.path,commits=[],additions=0,deletions=0,unmeasured=0,previous_paths=[]))
            if c.sha in row['commits']:continue
            row['commits'].append(c.sha)
            if f.additions is None or f.deletions is None:row['unmeasured']+=1
            else:row['additions']+=f.additions;row['deletions']+=f.deletions
            if f.previous_path and f.previous_path not in row['previous_paths']:row['previous_paths'].append(f.previous_path)
    rows=[]
    for row in files.values():
        row['touches']=len(row['commits']);row['known_additions']=row['additions'];row['known_deletions']=row['deletions']
        if row['unmeasured']:row['additions']=row['deletions']=None
        row['churn']=None if row['unmeasured'] else row['additions']+row['deletions'];rows.append(row)
    return [{'date':d,'commits':n} for d,n in sorted(days.items())],sorted(rows,key=lambda r:(-r['touches'],r['path']))


async def collect(reader, anchor, limits=LIMITS):
    revision(anchor);ids=await reader.list_commits(anchor,limits.commits+1);issues=[];commits=[];count=0
    if len(ids)>limits.commits:issues.append('commit_window_limit')
    for sha in ids[:limits.commits]:
        try:commit=await reader.commit(sha)
        except AnalysisError as error:
            if commits and error.code in {'github_rate_limit','github_size_limit','history_request_limit','history_transfer_limit'}:
                issues.append(error.code);break
            raise
        remaining=min(limits.files_per_commit,max(0,limits.changes-count))
        if len(commit.files)>remaining:commit.files=commit.files[:remaining];commit.files_complete=False
        if not commit.files_complete and 'file_change_limit' not in issues:issues.append('file_change_limit')
        for f in commit.files:f.patch=None  # History snapshots never retain source patches.
        count+=len(commit.files);commits.append(commit)
    retained={c.sha for c in commits};missing=sorted({p for c in commits for p in c.parents if p not in retained})
    if missing:issues.append('ancestry_outside_window')
    if getattr(reader,'shallow',False):issues.append('shallow_source')
    coverage=Coverage(bool(commits) and not missing and len(ids)<=limits.commits and not getattr(reader,'shallow',False),ordering=reader.ordering,issues=issues,missing_parents=missing[:128])
    activity,churn=aggregate(commits)
    result=History(reader.url,anchor,commits,coverage,activity,churn,asdict(limits),source=reader.source)
    # Hard serialized budget. Remove oldest retained records, recomputing all derived values.
    while len(json.dumps(asdict(result),ensure_ascii=False).encode())>limits.response_bytes and result.commits:
        result.commits.pop();result.activity,result.churn=aggregate(result.commits)
        result.coverage.complete_ancestry=False
        if 'serialized_limit' not in result.coverage.issues:result.coverage.issues.append('serialized_limit')
        retained={c.sha for c in result.commits};result.coverage.missing_parents=sorted({p for c in result.commits for p in c.parents if p not in retained})[:128]
    return result


def tree_changes(base, head, maximum):
    a={f.path:f for f in base.files};b={f.path:f for f in head.files};removed=set(a)-set(b);added=set(b)-set(a);changes=[]
    old=defaultdict(list);new=defaultdict(list)
    for p in sorted(removed):old[(a[p].sha,a[p].mode)].append(p)
    for p in sorted(added):new[(b[p].sha,b[p].mode)].append(p)
    for key in sorted(old):
        if len(old[key])==1 and len(new.get(key,[]))==1:
            x,y=old[key][0],new[key][0];changes.append(Change(y,'renamed',x,0,0,'identical_blob'));removed.remove(x);added.remove(y)
    changes.extend(Change(p,'removed') for p in sorted(removed));changes.extend(Change(p,'added') for p in sorted(added))
    changes.extend(Change(p,'modified') for p in sorted(set(a)&set(b)) if (a[p].sha,a[p].mode)!=(b[p].sha,b[p].mode))
    changes.sort(key=lambda f:(f.path,f.status));return changes[:maximum],len(changes)<=maximum,a,b


def line_diff(before,after,maximum):
    if b'\0' in before+after:return None,None,None,'binary'
    try:a=before.decode('utf-8').splitlines(keepends=True);b=after.decode('utf-8').splitlines(keepends=True)
    except UnicodeDecodeError:return None,None,None,'unsupported_encoding'
    if max(len(a),len(b))>LIMITS.text_lines:return None,None,None,'line_limit'
    matcher=difflib.SequenceMatcher(None,a,b,autojunk=False);added=deleted=0
    for op,i,j,k,l in matcher.get_opcodes():
        if op in {'replace','insert'}:added+=l-k
        if op in {'replace','delete'}:deleted+=j-i
    patch=''.join(difflib.unified_diff(a,b,fromfile='base',tofile='head',n=3))
    encoded=patch.encode();clipped=encoded[:maximum].decode('utf-8','ignore')
    return added,deleted,clipped,'text' if len(encoded)<=maximum else 'patch_limit'


async def compare(reader,base,head,limits=LIMITS,patches=True):
    revision(base);revision(head)
    a=await reader.tree(base);b=await reader.tree(head)
    # An incomplete tree cannot establish absence; refuse invented added/removed files.
    if not a.complete or not b.complete:raise AnalysisError('Revision tree is incomplete. Exact comparison is unavailable within the tree limit.','history_tree_limit',422)
    files,complete,old,new=tree_changes(a,b,limits.comparison_files);issues=[] if complete else ['comparison_file_limit'];budget=limits.patch_bytes
    for f in files[:limits.text_files]:
        if f.status=='renamed':continue
        values=[]
        for records,p in [(old,f.previous_path or f.path),(new,f.path)]:
            obj=records.get(p)
            if obj is None:values.append(b'');continue
            if obj.mode not in {'100644','100755'} or obj.size is None or obj.size>limits.blob_bytes:values.append(None)
            else:values.append(await reader.blob(obj.sha,limits.blob_bytes))
        if None in values:f.line_status='binary_size_or_special_entry';continue
        f.additions,f.deletions,f.patch,status=await asyncio.to_thread(line_diff,*values,min(16384,budget))
        f.line_status=status;f.patch_truncated=status=='patch_limit'
        budget-=len((f.patch or '').encode())
        if not patches:f.patch=None
    if len(files)>limits.text_files:issues.append('text_measurement_limit')
    return Comparison(reader.url,base,head,files,complete,issues)

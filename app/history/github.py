"""Fixed-host GitHub REST reader. Public commits only; no clone, credentials or cache."""
import asyncio
import base64
import json
from app.errors import AnalysisError
from app.ingestion.github import parse_github_url,upstream_error,read_limited
import httpx
from .models import LIMITS,Commit,Change,TreeFile,RevisionTree
from .core import revision,path,text,timestamp


class GitHubReader:
    source='github-rest'
    ordering='GitHub list-commits order, pinned at anchor; not assumed chronological or complete branch topology'

    def __init__(self,client,url,limits=LIMITS):
        self.client=client;self.repo=parse_github_url(url);self.url=self.repo.url
        self.base=f'https://api.github.com/repos/{self.repo.owner}/{self.repo.name}'
        self.limits=limits;self.requests=0;self.bytes=0;self.trees={}

    async def get(self,suffix,params=None,maximum=None):
        self.requests+=1
        if self.requests>self.limits.requests:raise AnalysisError('History request budget reached. Narrow the operation.','history_request_limit',422)
        maximum=min(maximum or self.limits.response_bytes,self.limits.transfer_bytes-self.bytes)
        if maximum<=0:raise AnalysisError('History transfer budget reached.','history_transfer_limit',413)
        async with self.client.stream('GET',self.base+suffix,params=params) as response:
            upstream_error(response)  # Includes rate limits; redirects never followed.
            raw=await read_limited(response,maximum);self.bytes+=len(raw)
            try:return json.loads(raw)
            except (ValueError,RecursionError):raise AnalysisError('GitHub returned invalid history metadata.','history_metadata',502) from None

    async def verify_public(self):
        metadata=await self.get('',maximum=256*1024)
        if not isinstance(metadata,dict) or metadata.get('private') is not False:raise AnalysisError('Use a public GitHub repository.','history_unavailable',404)

    async def list_commits(self,anchor,count):
        raw=await self.get('/commits',{'sha':revision(anchor),'per_page':min(count,100),'page':1})
        if not isinstance(raw,list):raise ValueError('Invalid commit list')
        ids=[revision(c['sha']) for c in raw]
        if not ids or ids[0]!=anchor:raise ValueError('Pinned history mismatch')
        return ids

    async def commit(self,sha):
        raw=await self.get('/commits/'+revision(sha),{'per_page':self.limits.files_per_commit,'page':1})
        if raw['sha']!=sha:raise ValueError('Commit mismatch')
        c=raw['commit'];files=[]
        if len(raw['parents'])>128:raise ValueError('Parent evidence limit')
        for f in raw.get('files',[])[:self.limits.files_per_commit]:
            status={'deleted':'removed'}.get(f['status'],f['status'])
            # No patch means GitHub may have omitted binary/large text evidence. No invented zero.
            measured=isinstance(f.get('patch'),str)
            adds=f.get('additions') if measured else None;deletes=f.get('deletions') if measured else None
            if measured and (type(adds)!=int or type(deletes)!=int or min(adds,deletes)<0):raise ValueError('Invalid line statistics')
            files.append(Change(path(f['filename']),text(status,32),path(f['previous_filename']) if 'previous_filename' in f else None,adds,deletes,'github_text' if measured else 'unavailable'))
        # Exactly a page is conservatively incomplete: additional pages are not fetched.
        return Commit(revision(sha),[revision(p['sha']) for p in raw['parents']],text(c['author']['name'],128),timestamp(c['author']['date']),timestamp(c['committer']['date']),text(c['message'].split('\n')[0]),revision(c['tree']['sha']),files,len(raw.get('files',[]))<self.limits.files_per_commit)

    async def tree(self,sha):
        revision(sha)
        if sha in self.trees:return self.trees[sha]
        commit=await self.get('/git/commits/'+sha,maximum=256*1024)
        if commit['sha']!=sha:raise ValueError('Revision mismatch')
        raw=await self.get('/git/trees/'+revision(commit['tree']['sha']),{'recursive':'1'})
        files=[];issues=['upstream_tree_truncated'] if raw.get('truncated') else []
        for f in raw['tree']:
            if f['type']=='tree':continue
            if len(files)>=self.limits.tree_files:issues.append('tree_file_limit');break
            name=path(f['path']);size=f.get('size')
            if size is not None and (type(size)!=int or size<0):raise ValueError('Invalid size')
            files.append(TreeFile(name,revision(f['sha']),f['mode'],size))
        result=RevisionTree(sha,sorted(files,key=lambda f:f.path),not issues,issues);self.trees[sha]=result;return result

    async def blob(self,sha,maximum):
        raw=await self.get('/git/blobs/'+revision(sha),maximum=maximum*2+2048)
        if raw['sha']!=sha or raw.get('encoding')!='base64' or raw['size']>maximum:return None
        data=base64.b64decode(raw['content'],validate=False)
        return data if len(data)<=maximum else None


async def operation(url,work,*,transport=None,limits=LIMITS):
    try:
        async with httpx.AsyncClient(transport=transport,follow_redirects=False,trust_env=False,
                                    timeout=httpx.Timeout(10,connect=5),headers={
             'User-Agent':'Codebase-Archaeologist','Accept':'application/vnd.github+json',
             'Accept-Encoding':'identity','X-GitHub-Api-Version':'2022-11-28'}) as client:
            reader=GitHubReader(client,url,limits)
            async def run():await reader.verify_public();return await work(reader)
            return await asyncio.wait_for(run(),limits.seconds)
    except (asyncio.TimeoutError,httpx.TimeoutException):raise AnalysisError('GitHub history retrieval timed out. Retry a smaller operation.','history_timeout',504) from None
    except httpx.HTTPError:raise AnalysisError('GitHub history is unreachable. Check network access and retry.','history_network',502) from None
    except (KeyError,ValueError,TypeError,AttributeError,UnicodeError,RecursionError):raise AnalysisError('GitHub returned unsupported history metadata.','history_metadata',502) from None

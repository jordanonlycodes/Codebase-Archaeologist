"""Operator/test-only Git object reader. Never exposed as a filesystem-path API."""
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import re
import selectors
import subprocess
import time
from app.errors import AnalysisError
from .core import revision,path,text,compare
from .models import Commit,RevisionTree,TreeFile,LIMITS


class LocalReader:
    source='local-git-fixture'
    ordering='git rev-list --topo-order, newest first'
    url='local-fixture'  # Never serialize the actual server filesystem path.

    def __init__(self,root):
        self.root=Path(root).resolve();self.cache={};self.shallow=False

    def _run(self,*args,maximum=2*1024*1024):
        env={'PATH':os.defpath,'HOME':'/nonexistent','GIT_CONFIG_NOSYSTEM':'1',
             'GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0','GIT_NO_REPLACE_OBJECTS':'1',
             'GIT_OPTIONAL_LOCKS':'0','GIT_LITERAL_PATHSPECS':'1'}
        command=['git','--no-pager','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false',
                 '-c','core.attributesFile=/dev/null','-C',str(self.root),*args]
        try:
            with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env) as process:
                output=bytearray();deadline=time.monotonic()+5
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout,selectors.EVENT_READ)
                    while True:
                        if time.monotonic()>deadline:process.kill();raise ValueError()
                        if not selector.select(.05):continue
                        chunk=os.read(process.stdout.fileno(),min(65536,maximum-len(output)+1))
                        if not chunk:break
                        output.extend(chunk)
                        if len(output)>maximum:process.kill();raise ValueError()
                try:code=process.wait(timeout=1)
                except subprocess.TimeoutExpired:process.kill();raise ValueError()
                if code:raise ValueError()
                return bytes(output)
        except (OSError,ValueError,subprocess.SubprocessError):
            raise AnalysisError('Git fixture is invalid or exceeded its bounded read budget.','history_git',422) from None

    async def run(self,*args,**options):return await asyncio.to_thread(self._run,*args,**options)

    async def list_commits(self,anchor,count):
        revision(anchor)
        if (await self.run('cat-file','-t',anchor)).strip()!=b'commit':raise AnalysisError('Object is not a commit.','invalid_revision',422)
        self.shallow=(await self.run('rev-parse','--is-shallow-repository')).strip()==b'true'
        result=await self.run('rev-list','--topo-order',f'--max-count={count}',anchor)
        return [revision(s) for s in result.decode('ascii').splitlines()]

    async def commit(self,sha):
        revision(sha);raw=await self.run('cat-file','commit',sha,maximum=256*1024)
        headers,_,body=raw.partition(b'\n\n');pairs={};parents=[]
        for line in headers.decode('utf-8','replace').splitlines():
            key,_,value=line.partition(' ')
            if key=='parent':parents.append(revision(value))
            else:pairs[key]=value
        def identity(value):
            match=re.fullmatch(r'(.*) <.*> (-?\d+) ([+-])(\d{2})(\d{2})',value)
            if not match:raise ValueError('Invalid author metadata')
            name,epoch,sign,hours,minutes=match.groups();delta=timedelta(hours=int(hours),minutes=int(minutes))*(1 if sign=='+' else -1)
            return text(name,128),datetime.fromtimestamp(int(epoch),timezone(delta)).isoformat()
        try:
            author,date=identity(pairs['author']);_,committer=identity(pairs['committer']);tree=revision(pairs['tree'])
        except (KeyError,ValueError,OverflowError):raise AnalysisError('Unsupported Git commit metadata.','history_metadata',422) from None
        result=Commit(sha,parents,author,date,committer,text(body.decode('utf-8','replace').split('\n')[0]),tree)
        try:
            diff=await compare(self,parents[0] if parents else '0'*40,sha,patches=False)
            result.files=diff.files;result.files_complete=diff.complete_file_list
        except AnalysisError:
            if not self.shallow:raise
            result.files_complete=False  # Missing shallow parent is not an initial commit.
        return result

    async def tree(self,sha):
        if sha=='0'*40:return RevisionTree(sha,[],True)
        revision(sha)
        if sha in self.cache:return self.cache[sha]
        if (await self.run('cat-file','-t',sha)).strip()!=b'commit':raise AnalysisError('Object is not a commit.','invalid_revision',422)
        raw=await self.run('ls-tree','-r','-z','--long',sha);files=[];issues=[]
        for record in raw.split(b'\0'):
            if not record:continue
            info,name=record.split(b'\t',1);mode,kind,oid,size=info.decode('ascii').split()
            try:name=path(name.decode('utf-8'))
            except (UnicodeError,AnalysisError):issues.append('unsupported_path');continue
            if len(files)>=LIMITS.tree_files:issues.append('tree_file_limit');break
            files.append(TreeFile(name,revision(oid),mode,None if size=='-' else int(size)))
        result=RevisionTree(sha,files,not issues,sorted(set(issues)));self.cache[sha]=result;return result

    async def blob(self,sha,maximum):
        revision(sha)
        if int((await self.run('cat-file','-s',sha)).strip())>maximum:return None
        return await self.run('cat-file','blob',sha,maximum=maximum)

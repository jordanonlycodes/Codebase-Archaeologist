"""Authentic object/commit fixtures; public HTTP is mocked, never history ground truth."""
import asyncio
from dataclasses import asdict,replace
import json
import os
from pathlib import Path
import subprocess
import pytest
import httpx
from app.history.local import LocalReader
from app.history.core import collect,compare,aggregate,line_diff
from app.history.models import LIMITS
from app.history.github import operation
from app.errors import AnalysisError


def git(root,*args,env=None):
    return subprocess.check_output(['git','-C',str(root),*args],env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null',**(env or {})},stderr=subprocess.DEVNULL).decode().strip()


@pytest.fixture
def history_repo(tmp_path):
    root=tmp_path/'history';root.mkdir();git(root,'init','-b','main');git(root,'config','user.name','Fixture Engineer');git(root,'config','user.email','fixture@example.invalid')
    shas=[]
    def commit(message,day,author='Fixture Engineer'):
        git(root,'add','--all');git(root,'commit','-m',message,env={'GIT_AUTHOR_DATE':f'2025-01-{day:02}T12:00:00+0500','GIT_COMMITTER_DATE':f'2025-01-{day:02}T13:00:00+0500','GIT_AUTHOR_NAME':author});sha=git(root,'rev-parse','HEAD');shas.append(sha);return sha
    (root/'a.py').write_text('def one():\n    return 1\n');commit('First evidence',1)
    (root/'a.py').write_text('def one():\n    return 2\n');commit('Edit a function',3,'Second Engineer')
    git(root,'checkout','-b','side');(root/'side.txt').write_text('side\n');commit('Side branch',4)
    git(root,'checkout','main');(root/'main.txt').write_text('main\n');commit('Main branch',5)
    git(root,'merge','--no-ff','side','-m','Merge observed parents',env={'GIT_AUTHOR_DATE':'2025-01-06T12:00:00+0500','GIT_COMMITTER_DATE':'2025-01-06T13:00:00+0500'});merge=git(root,'rev-parse','HEAD');shas.append(merge)
    git(root,'mv','a.py','renamed.py');commit('Rename literal blob',7)
    (root/'main.txt').unlink();(root/'binary.dat').write_bytes(b'\0\xffdata');(root/'--looks-like-command.txt').write_text('not a command\n');commit('<script>alert(1)</script> \x1b[31m',9)
    return root,shas,merge


def test_real_commits_parents_dates_files_churn_and_controls(history_repo):
    root,shas,merge=history_repo;reader=LocalReader(root);result=asyncio.run(collect(reader,shas[-1]))
    assert len(result.commits)==7 and result.coverage.complete_ancestry
    assert next(c for c in result.commits if c.sha==merge).parents==[shas[3],shas[2]]
    assert all(c.author_date.endswith('+05:00') for c in result.commits)
    assert {c.author for c in result.commits}=={'Fixture Engineer','Second Engineer'}
    assert any(f.status=='renamed' and f.previous_path=='a.py' for c in result.commits for f in c.files)
    assert any(f.path=='binary.dat' and f.additions is None for c in result.commits for f in c.files)
    assert '\x1b' not in result.commits[0].subject and '\\u001b' in result.commits[0].subject
    assert '<script>' in result.commits[0].subject  # Kept as text, not HTML.
    assert sum(r['commits'] for r in result.activity)==7
    assert all(f.patch is None for c in result.commits for f in c.files)
    assert str(root) not in json.dumps(asdict(result))


def test_window_limits_detached_head_and_shallow(history_repo,tmp_path):
    root,shas,_=history_repo;git(root,'checkout','--detach',shas[-1]);reader=LocalReader(root)
    result=asyncio.run(collect(reader,shas[-1],replace(LIMITS,commits=2)))
    assert len(result.commits)==2 and not result.coverage.complete_ancestry
    assert 'ancestry_outside_window' in result.coverage.issues
    shallow=tmp_path/'shallow';subprocess.run(['git','clone','--depth','2','--no-local',root.as_uri(),str(shallow)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    result=asyncio.run(collect(LocalReader(shallow),shas[-1]));assert 'shallow_source' in result.coverage.issues


def test_genuine_exact_tree_comparison_both_directions_and_rename(history_repo):
    root,shas,_=history_repo;reader=LocalReader(root)
    diff=asyncio.run(compare(reader,shas[0],shas[1]));assert len(diff.files)==1
    f=diff.files[0];assert (f.status,f.additions,f.deletions)==('modified',1,1);assert '+    return 2' in f.patch
    rename=asyncio.run(compare(reader,shas[4],shas[5]));assert rename.files[0].status=='renamed'
    assert rename.files[0].previous_path=='a.py'
    reverse=asyncio.run(compare(reader,shas[-1],shas[0]));assert any(f.status=='removed' and f.path=='binary.dat' for f in reverse.files)
    divergent=asyncio.run(compare(reader,shas[2],shas[3]));assert {(f.path,f.status) for f in divergent.files}=={('side.txt','removed'),('main.txt','added')}


@pytest.mark.parametrize('value',['HEAD','--help','main;echo','a'*7,'../main','g'*40])
def test_invalid_revisions_never_become_commands(history_repo,value):
    with pytest.raises(AnalysisError):asyncio.run(compare(LocalReader(history_repo[0]),value,history_repo[1][0]))


def test_no_hooks_no_filters_no_submodule_execution(history_repo):
    root,shas,_=history_repo;sentinel=root/'EXECUTED'
    hook=root/'.git/hooks/post-checkout';hook.write_text('#!/bin/sh\ntouch '+str(sentinel));hook.chmod(0o755)
    git(root,'config','diff.external','touch '+str(sentinel));git(root,'config','filter.evil.smudge','touch '+str(sentinel))
    asyncio.run(collect(LocalReader(root),shas[-1]));assert not sentinel.exists()


def test_binary_size_line_and_patch_limits(history_repo):
    root,shas,_=history_repo;f=asyncio.run(compare(LocalReader(root),shas[0],shas[-1],replace(LIMITS,comparison_files=1)))
    assert not f.complete_file_list and 'comparison_file_limit' in f.issues
    assert line_diff(b'\0',b'abc',20)[3]=='binary'
    assert line_diff(b'\xff',b'abc',20)[3]=='unsupported_encoding'
    assert line_diff(b'1\n'*2001,b'',20)[3]=='line_limit'
    assert line_diff(b'a\n',b'b\n',3)[3]=='patch_limit'


def test_repeated_results_and_empty_git_are_explicit(history_repo,tmp_path):
    root,shas,_=history_repo
    assert asdict(asyncio.run(collect(LocalReader(root),shas[-1])))==asdict(asyncio.run(collect(LocalReader(root),shas[-1])))
    empty=tmp_path/'empty';empty.mkdir();git(empty,'init')
    with pytest.raises(AnalysisError):asyncio.run(collect(LocalReader(empty),'a'*40))


def test_public_adapter_consumes_genuine_git_fixture_metadata(history_repo):
    root,shas,_=history_repo;facts=asyncio.run(collect(LocalReader(root),shas[-1]));byid={c.sha:c for c in facts.commits}
    requests=[]
    def handler(request):
        requests.append(str(request.url));p=request.url.path
        if p=='/repos/owner/repo':body={'private':False}
        elif p.endswith('/commits'):body=[{'sha':c.sha} for c in facts.commits]
        else:
            c=byid[p.rsplit('/',1)[-1]];body={'sha':c.sha,'parents':[{'sha':s} for s in c.parents],'commit':{'author':{'name':c.author,'date':c.author_date},'committer':{'date':c.committer_date},'message':c.subject,'tree':{'sha':c.tree}},'files':[{'filename':f.path,'status':f.status,'additions':f.additions,'deletions':f.deletions,**({'patch':'actual patch omitted in fixture adapter'} if f.additions is not None else {}),**({'previous_filename':f.previous_path} if f.previous_path else {})} for f in c.files]}
        return httpx.Response(200,stream=httpx.ByteStream(json.dumps(body).encode()))
    async def run():return await operation('https://github.com/owner/repo',lambda r:collect(r,shas[-1]),transport=httpx.MockTransport(handler))
    result=asyncio.run(run());assert [c.sha for c in result.commits]==[c.sha for c in facts.commits]
    assert len(requests)==9 and all(u.startswith('https://api.github.com/repos/owner/repo') for u in requests)


@pytest.mark.parametrize('status,code',[(404,'github_unavailable'),(429,'github_rate_limit'),(302,'github_upstream')])
def test_network_errors_and_redirects_are_controlled(status,code):
    async def run():return await operation('https://github.com/owner/repo',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(lambda _:httpx.Response(status,headers={'Location':'http://localhost/private'})))
    with pytest.raises(AnalysisError) as e:asyncio.run(run())
    assert e.value.code==code

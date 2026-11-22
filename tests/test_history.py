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
    (root/'src/nested').mkdir(parents=True);(root/'src/nested/helper.c').write_text('int helper(void){return 1;}\n')
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


def test_history_api_scoped_identity_and_no_local_paths(monkeypatch,history_repo):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routes import history as route
    root,shas,_=history_repo
    async def local(url,work):
        assert url=='https://github.com/owner/repo'
        return await work(LocalReader(root))
    monkeypatch.setattr(route,'operation',local)
    body={'url':'https://github.com/owner/repo','anchor':shas[-1]}
    with TestClient(app) as client:
        result=client.post('/api/history/load',json=body);assert result.status_code==200,result.text
        assert len(result.json()['commits'])==7 and str(root) not in result.text
        diff=client.post('/api/history/compare',json={**body,'base':shas[0],'head':shas[1]})
        assert diff.status_code==200 and diff.json()['files'][0]['additions']==1
        tree=client.post('/api/history/tree',json={**body,'revision':shas[0]})
        assert tree.status_code==200 and tree.json()['files'][0]['path']=='a.py'
        assert client.post('/api/history/tree',json={**body,'revision':'f'*40}).status_code==422
        assert client.post('/api/history/load',json={**body,'root':str(root)}).status_code==422
        assert client.post('/api/history/load',content=b'x'*4097,headers={'content-type':'application/json'}).status_code==413
        assert client.post('/api/history/compare',json={**body,'base':'HEAD','head':shas[0]}).status_code==422


@pytest.mark.parametrize('url',['http://github.com/a/b','https://github.com.evil/a/b','file:///tmp/repo','https://127.0.0.1/repo','https://github.com/a/b/../c'])
def test_history_arbitrary_remote_rejected_before_network(url):
    calls=[]
    with pytest.raises(AnalysisError):
        asyncio.run(operation(url,lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(lambda request:calls.append(request))))
    assert not calls


def test_incomplete_tree_cannot_create_false_deletions(history_repo):
    reader=LocalReader(history_repo[0]);original=reader.tree
    async def tree(sha):
        result=await original(sha);result.complete=False;return result
    reader.tree=tree
    with pytest.raises(AnalysisError) as e:asyncio.run(compare(reader,history_repo[1][0],history_repo[1][-1]))
    assert e.value.code=='history_tree_limit'


def test_response_budget_and_first_parent_merge_changes(history_repo):
    root,shas,merge=history_repo;result=asyncio.run(collect(LocalReader(root),shas[-1],replace(LIMITS,response_bytes=4000)))
    assert len(json.dumps(asdict(result),ensure_ascii=False).encode())<=4000
    assert not result.coverage.complete_ancestry
    full=asyncio.run(collect(LocalReader(root),merge))
    current=full.commits[0];assert current.sha==merge and [f.path for f in current.files]==['side.txt']


def test_http_revision_tree_and_blob_adapter_matches_real_git_objects(history_repo):
    import base64
    root,shas,_=history_repo;local=LocalReader(root)
    async def facts():
        commits={sha:await local.commit(sha) for sha in shas};trees={c.tree:await local.tree(c.sha) for c in commits.values()};blobs={}
        for tree in trees.values():
            for f in tree.files:
                if f.mode in {'100644','100755'}:blobs[f.sha]=await local.blob(f.sha,65536)
        expected=await compare(local,shas[2],shas[3]);return commits,trees,blobs,expected
    commits,trees,blobs,expected=asyncio.run(facts());seen=[]
    def handler(request):
        seen.append(request.url);p=request.url.path
        if p=='/repos/owner/repo':body={'private':False}
        elif '/git/commits/' in p:
            sha=p.rsplit('/',1)[-1];body={'sha':sha,'tree':{'sha':commits[sha].tree}}
        elif '/git/trees/' in p:
            sha=p.rsplit('/',1)[-1];body={'sha':sha,'truncated':False,'tree':[{'path':f.path,'sha':f.sha,'mode':f.mode,'size':f.size,'type':'blob'} for f in trees[sha].files]}
        elif '/git/blobs/' in p:
            sha=p.rsplit('/',1)[-1];body={'sha':sha,'size':len(blobs[sha]),'encoding':'base64','content':base64.b64encode(blobs[sha]).decode()}
        else:raise AssertionError(p)
        return httpx.Response(200,stream=httpx.ByteStream(json.dumps(body).encode()))
    async def run():return await operation('https://github.com/owner/repo',lambda r:compare(r,shas[2],shas[3]),transport=httpx.MockTransport(handler))
    actual=asyncio.run(run());assert [(f.path,f.status,f.additions,f.deletions,f.patch) for f in actual.files]==[(f.path,f.status,f.additions,f.deletions,f.patch) for f in expected.files]
    assert all(u.host=='api.github.com' and u.scheme=='https' for u in seen)


def test_genuine_git_special_entries_are_never_followed(history_repo):
    root,shas,_=history_repo;os.symlink('/etc/passwd',root/'outside-link')
    git(root,'update-index','--add','--cacheinfo','160000,'+shas[0]+',submodule');git(root,'add','outside-link');git(root,'commit','-m','Metadata only special entries')
    sha=git(root,'rev-parse','HEAD');reader=LocalReader(root);tree=asyncio.run(reader.tree(sha));assert next(f for f in tree.files if f.path=='outside-link').mode=='120000';assert next(f for f in tree.files if f.path=='submodule').mode=='160000'
    result=asyncio.run(compare(reader,shas[-1],sha));assert all(f.additions is None for f in result.files)


def test_actual_month_gaps_are_zero_only_in_retained_activity(history_repo,tmp_path):
    root,shas,_=history_repo;(root/'april.txt').write_text('new month\n');git(root,'add','april.txt');git(root,'commit','-m','April evidence',env={'GIT_AUTHOR_DATE':'2025-04-01T00:30:00+1400','GIT_COMMITTER_DATE':'2025-04-01T00:30:00+1400'})
    history=asyncio.run(collect(LocalReader(root),git(root,'rev-parse','HEAD')))
    assert any(d['date']=='2025-03-31' for d in history.activity)  # Correct UTC day, not local author date.
    file=tmp_path/'activity.json';file.write_text(json.dumps(asdict(history)))
    run=subprocess.run(['node','-e',"const d=require('./app/static/time_machine/data.js'),h=JSON.parse(require('fs').readFileSync(process.argv[1]));const m=d.months(h.commits);require('assert').equal(m.find(x=>x.month==='2025-02').count,0);require('assert').equal(m.find(x=>x.month==='2025-03').count,1);",str(file)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr


@pytest.mark.parametrize('failure,code',[(httpx.ReadTimeout('private error'),'history_timeout'),(httpx.ConnectError('private error'),'history_network')])
def test_history_network_exceptions_do_not_leak_details(failure,code):
    def handler(request):raise failure
    with pytest.raises(AnalysisError) as e:asyncio.run(operation('https://github.com/a/b',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(handler)))
    assert e.value.code==code and 'private error' not in e.value.message


def test_transfer_and_request_budgets_are_enforced_before_parsing():
    response=lambda _:httpx.Response(200,stream=httpx.ByteStream(b'x'*1000))
    with pytest.raises(AnalysisError) as e:asyncio.run(operation('https://github.com/a/b',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(response),limits=replace(LIMITS,transfer_bytes=50)))
    assert e.value.code=='github_size_limit'
    public=lambda _:httpx.Response(200,stream=httpx.ByteStream(b'{"private":false}'))
    with pytest.raises(AnalysisError) as e:asyncio.run(operation('https://github.com/a/b',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(public),limits=replace(LIMITS,requests=1)))
    assert e.value.code=='history_request_limit'


def test_local_git_output_bound_and_cross_repository_object_isolation(history_repo,tmp_path):
    root,shas,_=history_repo;reader=LocalReader(root)
    with pytest.raises(AnalysisError):reader._run('cat-file','commit',shas[0],maximum=2)
    other=tmp_path/'other';other.mkdir();git(other,'init')
    with pytest.raises(AnalysisError):asyncio.run(LocalReader(other).tree(shas[0]))


def test_ambiguous_identical_blob_renames_are_not_arbitrarily_paired(history_repo):
    root,_,_=history_repo
    for name in ['old-one.txt','old-two.txt']:(root/name).write_text('shared exact blob\n')
    git(root,'add','--all');git(root,'commit','-m','Duplicate blobs');base=git(root,'rev-parse','HEAD')
    git(root,'mv','old-one.txt','new-one.txt');git(root,'mv','old-two.txt','new-two.txt');git(root,'commit','-m','Ambiguous rename identities');head=git(root,'rev-parse','HEAD')
    result=asyncio.run(compare(LocalReader(root),base,head));assert len(result.files)==4 and all(f.status!='renamed' for f in result.files)


def test_partial_tree_limit_and_midstream_rate_limit_are_explicit(history_repo,monkeypatch):
    from app.history import local
    root,shas,_=history_repo
    monkeypatch.setattr(local,'LIMITS',replace(LIMITS,tree_files=1));reader=LocalReader(root)
    tree=asyncio.run(reader.tree(shas[0]));assert not tree.complete and tree.issues==['tree_file_limit']
    monkeypatch.setattr(local,'LIMITS',LIMITS);reader=LocalReader(root);original=reader.commit;count=0
    async def commit(sha):
        nonlocal count
        count+=1
        if count>2:raise AnalysisError('rate limited','github_rate_limit',429)
        return await original(sha)
    reader.commit=commit;result=asyncio.run(collect(reader,shas[-1]));assert len(result.commits)==2
    assert 'github_rate_limit' in result.coverage.issues and not result.coverage.complete_ancestry


def test_history_transport_shares_two_operation_admission_and_releases_capacity():
    from app.middleware import UploadBoundary
    async def check():
        release=asyncio.Event();started=asyncio.Event();sent=[]
        async def inner(scope,receive,send):await receive();started.set();await release.wait()
        middleware=UploadBoundary(inner)
        scope={'type':'http','method':'POST','path':'/api/history/load','headers':[]}
        async def receive():return {'type':'http.request','body':b'{}','more_body':False}
        async def send(message):sent.append(message)
        first=asyncio.create_task(middleware(scope,receive,send));await started.wait();second=asyncio.create_task(middleware(scope,receive,send));await asyncio.sleep(0)
        await middleware(scope,receive,send);assert sent[0]['status']==429
        release.set();await asyncio.gather(first,second);assert middleware.active==0
    asyncio.run(check())

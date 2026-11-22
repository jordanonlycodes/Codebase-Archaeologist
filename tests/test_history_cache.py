"""Deterministic cache/single-flight tests; no GitHub connection or credentials."""
import asyncio
import json
from dataclasses import replace
import httpx
import pytest
from app.history.cache import EvidenceCache
from app.history.github import operation
from app.history.models import LIMITS
from app.errors import AnalysisError


def run(coro):return asyncio.run(coro)

def response(body):return httpx.Response(200,headers={"content-type":"application/json"},stream=httpx.ByteStream(json.dumps(body).encode()))


def test_cache_hit_copies_expiration_eviction_and_diagnostics():
    now=[0];cache=EvidenceCache(entries=2,byte_limit=100,entry_bytes=50,clock=lambda:now[0]);calls=[]
    async def value():calls.append(1);return {'n':[1]}
    async def scenario():
        a,state=await cache.obtain('a',value,10);assert state=='miss';a['n'].append(2)
        assert (await cache.obtain('a',value,10))==({'n':[1]},'hit')
        await cache.obtain('b',value,10);await cache.obtain('c',value,10)
        assert cache.diagnostics()['evictions']==1
        now[0]=11;assert cache.diagnostics()['entries']==0
        await cache.obtain('c',value,10)
    run(scenario());assert len(calls)==4


def test_cache_oversized_and_total_bytes_remain_bounded():
    cache=EvidenceCache(entries=10,byte_limit=30,entry_bytes=20)
    async def scenario():
        for i in range(4):await cache.obtain(i,lambda:asyncio.sleep(0,result='x'*15),10)
        assert cache.diagnostics()['entries']==1 and cache.diagnostics()['bytes']<=30
        for _ in range(2):assert (await cache.obtain('large',lambda:asyncio.sleep(0,result='x'*100),10))[1]=='miss'
    run(scenario())


def test_single_flight_independence_failure_recovery_and_consumer_cancellation():
    cache=EvidenceCache();calls=[]
    async def scenario():
        started=asyncio.Event();release=asyncio.Event()
        async def slow():calls.append(1);started.set();await release.wait();return [42]
        first=asyncio.create_task(cache.obtain('same',slow,10));await started.wait()
        second=asyncio.create_task(cache.obtain('same',slow,10));await asyncio.sleep(0)
        assert (await cache.obtain('other',lambda:asyncio.sleep(0,result=3),10))[0]==3
        first.cancel()
        with pytest.raises(asyncio.CancelledError):await first
        release.set();assert (await second)==([42],'coalesced')
        assert (await cache.obtain('same',slow,10))[1]=='hit'
        async def bad():raise ValueError('transient')
        with pytest.raises(ValueError):await cache.obtain('bad',bad,10)
        assert (await cache.obtain('bad',lambda:asyncio.sleep(0,result='recovered'),10))[0]=='recovered'
    run(scenario());assert calls==[1];assert cache.diagnostics()['flights']==0


def test_identical_http_resources_coalesce_and_are_repository_sha_parameter_scoped():
    cache=EvidenceCache();seen=[]
    async def handler(request):
        seen.append(str(request.url));await asyncio.sleep(.01)
        return response({'private':False} if request.url.path.count('/')==3 else [{'sha':request.url.params['sha']}])
    transport=httpx.MockTransport(handler)
    async def fetch(repo='repo',sha='a'*40,count=2):
        return await operation('https://github.com/owner/'+repo,lambda r:r.list_commits(sha,count),transport=transport,cache=cache)
    async def scenario():
        assert await asyncio.gather(fetch(),fetch())==[['a'*40],['a'*40]]
        assert len(seen)==2
        await fetch();assert len(seen)==2
        await fetch(sha='b'*40);await fetch(count=3);await fetch(repo='other')
        assert len(seen)==6
    run(scenario());assert cache.diagnostics()['coalesced']>=1


def test_invalid_parsed_evidence_is_not_cached():
    cache=EvidenceCache();seen=[]
    def handler(request):
        seen.append(1)
        return response({'private':False} if len(seen)==1 else [{'sha':'wrong'}] if len(seen)==2 else [{'sha':'a'*40}])
    async def fetch():return await operation('https://github.com/o/r',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(handler),cache=cache)
    with pytest.raises(AnalysisError):run(fetch())
    assert run(fetch())==['a'*40] and len(seen)==3


@pytest.mark.parametrize('status,headers,message,code,kind',[
 (403,{'x-ratelimit-remaining':'0','x-ratelimit-reset':'2000000000'},'API rate limit exceeded','github_rate_limit','primary'),
 (403,{'retry-after':'90'},'secondary rate limit','github_rate_limit','secondary'),
 (403,{},'You exceeded a secondary rate limit.','github_rate_limit','secondary'),
 (429,{},'Too many requests','github_rate_limit','unspecified'),
 (403,{},'Resource not accessible','github_forbidden',None),
 (401,{},'Bad credentials','github_authentication',None),
 (404,{},'Not found','github_unavailable',None),
 (503,{},'Service unavailable','github_upstream',None),
])
def test_precise_upstream_failure_categories_and_safe_metadata(status,headers,message,code,kind):
    def handler(request):return httpx.Response(status,headers={**headers,'content-type':'application/json'},stream=httpx.ByteStream(json.dumps({'message':message}).encode()))
    with pytest.raises(AnalysisError) as error:run(operation('https://github.com/o/r',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(handler)))
    assert error.value.code==code and error.value.api.get('kind')==kind
    if kind:assert error.value.api['retry_at']>error.value.api['observed_at']
    if 'x-ratelimit-reset' not in headers:assert error.value.api['reset_at'] is None


def test_cooldown_blocks_network_but_cached_evidence_stays_usable_and_requires_reverification():
    from app.history.status import RateLedger
    now=[1000];cache=EvidenceCache();cache.rates=RateLedger(clock=lambda:now[0]);seen=[]
    def handler(request):
        seen.append(str(request.url));params=request.url.params
        if not params:return response({'private':False})
        if params['sha']=='a'*40:return response([{'sha':'a'*40}])
        return httpx.Response(403,headers={'x-ratelimit-remaining':'0','x-ratelimit-reset':'1100'},stream=httpx.ByteStream(b'{}'))
    async def fetch(sha):return await operation('https://github.com/o/r',lambda r:r.list_commits(sha,2),transport=httpx.MockTransport(handler),cache=cache)
    assert run(fetch('a'*40))==['a'*40]
    with pytest.raises(AnalysisError):run(fetch('b'*40))
    assert run(fetch('a'*40))==['a'*40]  # cache may serve during cooldown
    with pytest.raises(AnalysisError):run(fetch('c'*40))
    assert len(seen)==3
    now[0]=1101;assert cache.rates.status('anonymous')['state']=='limited'
    assert run(fetch('a'*40))==['a'*40]  # no promise of reset without another response
    with pytest.raises(AnalysisError):run(fetch('c'*40))
    assert len(seen)==4


def test_headers_are_parsed_defensively_and_http_date_retry_is_respected():
    from app.history.status import response_metadata,RateLedger
    headers=httpx.Headers({'x-ratelimit-limit':'oops','x-ratelimit-remaining':'-1','x-ratelimit-reset':'nan','retry-after':'not a date','x-github-request-id':'unsafe<>','x-ratelimit-resource':'a<script>'})
    meta=response_metadata(headers,0);assert all(meta[k] is None for k in ['limit','remaining','reset_at','retry_after','request_id','resource'])
    meta=response_metadata(httpx.Headers({'retry-after':'Thu, 01 Jan 1970 00:02:00 GMT'}),60)
    assert meta['retry_after']>=60
    ledger=RateLedger(clock=lambda:60)
    with pytest.raises(AnalysisError) as error:ledger.record('a',headers,429,{})
    assert error.value.api['retry_at']>=120 and error.value.api['reset_at'] is None


def test_token_server_only_scope_rotation_and_private_repository_rejection(monkeypatch):
    cache=EvidenceCache();seen=[];token='test-only-operator-credential'
    def handler(request):
        seen.append(request)
        return response({'private':False} if not request.url.params else [{'sha':request.url.params['sha']}])
    async def fetch():return await operation('https://github.com/o/r',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(handler),cache=cache)
    monkeypatch.delenv('CODEBASE_GITHUB_TOKEN',raising=False);assert run(fetch())==['a'*40]
    assert all('authorization' not in r.headers for r in seen)
    monkeypatch.setenv('CODEBASE_GITHUB_TOKEN',token);assert run(fetch())==['a'*40]
    assert len(seen)==4 and all(r.headers['authorization']=='Bearer '+token for r in seen[2:])
    assert all(r.url.host=='api.github.com' and r.url.scheme=='https' for r in seen)
    assert token not in repr(cache.values) and token not in repr(cache.diagnostics())
    monkeypatch.setenv('CODEBASE_GITHUB_TOKEN','rotated-operator-credential');run(fetch());assert len(seen)==6
    async def private():return await operation('https://github.com/private/repo',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(lambda _:response({'private':True})),cache=cache)
    with pytest.raises(AnalysisError) as error:run(private())
    assert error.value.code=='history_unavailable'


@pytest.mark.parametrize('body,content_type',[(b'not-json','application/json'),(b'{}','text/html'),(b'{}','')])
def test_invalid_json_or_content_type_is_rejected_without_cache_poison(body,content_type):
    cache=EvidenceCache()
    async def fetch():return await operation('https://github.com/o/r',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(lambda _:httpx.Response(200,headers={'content-type':content_type},stream=httpx.ByteStream(body))),cache=cache)
    with pytest.raises(AnalysisError) as error:run(fetch())
    assert error.value.code=='history_metadata' and cache.diagnostics()['entries']==0


def test_token_error_payload_and_response_diagnostics_never_expose_credentials(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routes import history as route
    from app.history.github import operation as real
    token='test-only-secret-that-must-not-leak';monkeypatch.setenv('CODEBASE_GITHUB_TOKEN',token)
    def handler(request):return httpx.Response(401,headers={'content-type':'application/json'},stream=httpx.ByteStream(json.dumps({'message':token}).encode()))
    async def adapter(url,work):return await real(url,work,transport=httpx.MockTransport(handler))
    monkeypatch.setattr(route,'operation',adapter)
    with TestClient(app) as client:
        r=client.post('/api/history/load',json={'url':'https://github.com/o/r','anchor':'a'*40})
        assert r.status_code==502 and r.json()['error']['code']=='github_authentication'
        assert token not in r.text and token not in str(r.headers)


@pytest.fixture
def real_history_rest(history_repo):
    """HTTP records derived from actual Git objects, including divergent trees."""
    import base64
    from dataclasses import asdict
    from app.history.local import LocalReader
    from app.history.core import collect
    root,shas,_=history_repo;local=LocalReader(root)
    async def facts():
        history=await collect(local,shas[-1]);commits={c.sha:c for c in history.commits};trees={sha:await local.tree(sha) for sha in shas};blobs={}
        for tree in trees.values():
            for f in tree.files:
                if f.mode in {'100644','100755'}:blobs[f.sha]=await local.blob(f.sha,65536)
        return history,commits,trees,blobs
    history,commits,trees,blobs=run(facts());seen=[]
    def handler(request):
        seen.append(str(request.url));p=request.url.path;sha=p.rsplit('/',1)[-1]
        if p=='/repos/owner/repo':body={'private':False}
        elif p.endswith('/commits'):body=[{'sha':c.sha} for c in history.commits]
        elif '/git/commits/' in p:body={'sha':sha,'tree':{'sha':commits[sha].tree}}
        elif '/git/trees/' in p:
            t=next(t for k,t in trees.items() if commits[k].tree==sha)
            body={'sha':sha,'truncated':False,'tree':[{'path':f.path,'sha':f.sha,'mode':f.mode,'size':f.size,'type':'blob'} for f in t.files]}
        elif '/git/blobs/' in p:body={'sha':sha,'size':len(blobs[sha]),'encoding':'base64','content':base64.b64encode(blobs[sha]).decode()}
        else:
            c=commits[sha];body={'sha':sha,'parents':[{'sha':s} for s in c.parents],'commit':{'author':{'name':c.author,'date':c.author_date},'committer':{'date':c.committer_date},'message':c.subject,'tree':{'sha':c.tree}},'files':[{'filename':f.path,'status':f.status,'additions':f.additions,'deletions':f.deletions,**({'patch':'fixture text availability'} if f.additions is not None else {}),**({'previous_filename':f.previous_path} if f.previous_path else {})} for f in c.files]}
        return httpx.Response(200,headers={'content-type':'application/json','x-ratelimit-limit':'5000','x-ratelimit-remaining':'4999','x-ratelimit-reset':'2000000000','x-ratelimit-resource':'core','x-github-request-id':'fixture-request'},stream=httpx.ByteStream(json.dumps(body).encode()))
    return shas,seen,httpx.MockTransport(handler)


# Explicit fixture reuse follows the existing product integration-test convention.
from test_history import history_repo


def test_real_api_repeated_load_comparison_tree_and_diagnostics_avoid_upstream(monkeypatch,real_history_rest):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routes import history as route
    shas,seen,transport=real_history_rest;cache=EvidenceCache()
    async def adapter(url,work):return await operation(url,work,transport=transport,cache=cache)
    monkeypatch.setattr(route,'operation',adapter)
    body={'url':'https://github.com/owner/repo','anchor':shas[-1]}
    with TestClient(app) as client:
        first=client.post('/api/history/load',json=body);assert first.status_code==200,first.text
        assert len(first.json()['commits'])==7 and len(seen)==9
        assert json.loads(first.headers['x-history-api'])['upstream_requests']==9
        second=client.post('/api/history/load',json=body);assert second.json()==first.json() and len(seen)==9
        assert json.loads(second.headers['x-history-api'])['cache']=='hit'
        pair={**body,'base':shas[2],'head':shas[3]}
        first_pair=client.post('/api/history/compare',json=pair);assert first_pair.status_code==200,first_pair.text
        assert {(f['path'],f['status']) for f in first_pair.json()['files']}=={('main.txt','added'),('side.txt','removed')}
        count=len(seen);assert count==13  # cached commit→tree evidence avoids two redundant Git-commit calls
        again=client.post('/api/history/compare',json=pair)
        assert again.json()==first_pair.json() and len(seen)==count
        assert json.loads(again.headers['x-history-api'])['upstream_requests']==0
        tree=client.post('/api/history/tree',json={**body,'revision':shas[2]})
        assert tree.status_code==200 and tree.json()['revision']==shas[2] and len(seen)==count
        repeat=client.post('/api/history/tree',json={**body,'revision':shas[2]})
        assert repeat.json()==tree.json() and len(seen)==count
        assert json.loads(repeat.headers['x-history-api'])['remaining']==4999
        rejected=client.post('/api/history/tree',json={**body,'revision':'e'*40})
        assert rejected.status_code==422 and len(seen)==count


def test_shared_http_producer_survives_operation_consumer_cancellation():
    cache=EvidenceCache();seen=[]
    async def scenario():
        started=asyncio.Event();release=asyncio.Event()
        async def handler(request):
            seen.append(str(request.url))
            if request.url.params:started.set();await release.wait();return response([{'sha':'a'*40}])
            return response({'private':False})
        async def fetch():return await operation('https://github.com/o/r',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(handler),cache=cache)
        first=asyncio.create_task(fetch());await started.wait();second=asyncio.create_task(fetch());await asyncio.sleep(.01)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):await first
        release.set();assert await second==['a'*40]
        assert await fetch()==['a'*40] and len(seen)==2
    run(scenario())


def test_remaining_zero_success_prevents_next_uncached_call_without_failing_result():
    from app.history.status import RateLedger
    ledger=RateLedger(clock=lambda:100)
    ledger.record('a',httpx.Headers({'x-ratelimit-remaining':'0','x-ratelimit-reset':'200','retry-after':'150'}),200,{})
    assert ledger.status('a')['retry_at']==250
    with pytest.raises(AnalysisError):ledger.before('a')
    # An already in-flight reply cannot shorten the wait.
    ledger.record('a',httpx.Headers({'x-ratelimit-remaining':'1'}),200,{})
    assert ledger.status('a')['retry_at']==250


def test_invalid_token_configuration_is_safe_and_performs_no_http(monkeypatch):
    monkeypatch.setenv('CODEBASE_GITHUB_TOKEN','invalid\ncredential');seen=[]
    with pytest.raises(AnalysisError) as error:run(operation('https://github.com/o/r',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(lambda r:seen.append(r))))
    assert error.value.code=='github_authentication' and 'credential\n' not in error.value.message and not seen


def test_upstream_503_retry_after_is_respected_without_labeling_it_a_rate_limit():
    from app.history.status import RateLedger
    ledger=RateLedger(clock=lambda:100)
    with pytest.raises(AnalysisError) as error:ledger.record('a',httpx.Headers({'retry-after':'120'}),503,{})
    assert error.value.code=='github_upstream' and error.value.api['state']=='unavailable'
    with pytest.raises(AnalysisError) as cooldown:ledger.before('a')
    assert cooldown.value.code=='github_upstream' and cooldown.value.api['retry_at']==220


def test_flight_limit_is_bounded_without_serializing_unrelated_work():
    cache=EvidenceCache(flights=2)
    async def scenario():
        release=asyncio.Event();started=[asyncio.Event(),asyncio.Event()]
        async def wait(index):started[index].set();await release.wait();return index
        tasks=[asyncio.create_task(cache.obtain(i,lambda i=i:wait(i),10)) for i in range(2)]
        await asyncio.gather(*(event.wait() for event in started))
        with pytest.raises(AnalysisError) as error:await cache.obtain(2,lambda:asyncio.sleep(0,result=2),10)
        assert error.value.code=='busy'
        release.set();assert [v for v,_ in await asyncio.gather(*tasks)]==[0,1]
        assert (await cache.obtain(2,lambda:asyncio.sleep(0,result=2),10))[0]==2
    run(scenario())


def test_detached_producer_deadline_releases_flight_and_does_not_poison_cache():
    cache=EvidenceCache()
    async def scenario():
        async def stalled(request):await asyncio.sleep(10)
        with pytest.raises(AnalysisError) as error:await operation('https://github.com/o/r',lambda r:r.list_commits('a'*40,2),transport=httpx.MockTransport(stalled),cache=cache,limits=replace(LIMITS,seconds=.03))
        assert error.value.code=='history_timeout'
        await asyncio.sleep(.03);assert cache.diagnostics()['flights']==0
    run(scenario())

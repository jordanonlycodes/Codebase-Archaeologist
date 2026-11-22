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

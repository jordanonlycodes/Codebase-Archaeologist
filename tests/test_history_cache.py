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

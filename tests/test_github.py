"""Network-free GitHub acquisition and shared analysis integration tests."""
import asyncio
from dataclasses import asdict, replace
import io
import inspect
from pathlib import Path
from tempfile import TemporaryDirectory as RealTemporaryDirectory, TemporaryFile as RealTemporaryFile

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import GITHUB_LIMITS
from app.errors import AnalysisError
from app.ingestion import github
from app.main import app
from app.routes import analysis

COMMIT = 'a' * 40
METADATA = {'owner': {'login': 'octocat'}, 'name': 'sample', 'private': False, 'default_branch': 'main'}


@pytest.mark.parametrize('value', ['https://github.com/octocat/sample', ' https://github.com/octocat/sample/ ',
                                   'https://github.com/octocat/sample.git', 'https://GITHUB.COM/octocat/sample.git/'])
def test_normalized_url(value):
    repo = github.parse_github_url(value)
    assert (repo.owner, repo.name, repo.url) == ('octocat', 'sample', 'https://github.com/octocat/sample')


@pytest.mark.parametrize('value', [
    'http://github.com/o/r', 'ftp://github.com/o/r', 'git@github.com:o/r',
    'https://github.com.evil.test/o/r', 'https://evilgithub.com/o/r',
    'https://github.com@evil.test/o/r', 'https://user:pass@github.com/o/r',
    'https://github.com:443/o/r', 'https://github.com:123/o/r',
    'https://localhost/o/r', 'https://127.0.0.1/o/r', 'https://10.0.0.1/o/r',
    'https://github.com/o/r/issues', 'https://github.com/o/r/pull/1',
    'https://github.com/o/r/releases', 'https://github.com/o/r/blob/main/a.c',
    'https://github.com/o/r?x=1', 'https://github.com/o/r#ref',
    'https://github.com/o/r?', 'https://github.com/o/r#',
    'https://github.com/-bad/r', 'https://github.com/bad-/r', 'https://github.com/a--b/r',
    'https://github.com/o/.', 'https://github.com/o/..', 'https://github.com/o/.git',
    'https://github.com/o/r.git.git', 'https://github.com/o/%2e%2e',
    'https://github.com/o%2fr/r', 'https://github.com/o/r%2fissues',
    'https://github.com/o/r\\x', 'https://github.com//r', 'https://github.com/o/r//',
    'https://github.com/o/é', 'https://github.com/o/rep\no', 'https://github.com./o/r',
    'https://github.com/o/'+'x'*101, 'https://github.com/'+'a'*40+'/r', '', None,
])
def test_rejected_urls(value):
    with pytest.raises(AnalysisError) as error:
        github.parse_github_url(value)
    assert error.value.code == 'invalid_github_url'


class Chunks(httpx.AsyncByteStream):
    def __init__(self, chunks): self.chunks = chunks
    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk


def handler_for(archive, *, redirect=None, status=None, headers=None, stream=None):
    seen = []
    def handler(request):
        seen.append(request)
        if status:
            return httpx.Response(status, headers=headers or {})
        if request.url.path == '/repos/octocat/sample':
            return httpx.Response(200, json=METADATA)
        if '/commits/' in request.url.path:
            assert request.headers['accept'] == 'application/vnd.github.sha'
            return httpx.Response(200, text=COMMIT)
        if '/zipball/' in request.url.path:
            return httpx.Response(302, headers={'location': redirect or 'https://codeload.github.com/octocat/sample/legacy.zip/'+COMMIT})
        assert request.url.host == 'codeload.github.com'
        return httpx.Response(200, stream=stream or Chunks([archive]), headers=headers or {})
    return handler, seen


def network_transport(handler):
    # Model actual streamed network responses, not pre-consumed convenience
    # responses produced by httpx.Response(json=...) in fixture handlers.
    async def streamed(request):
        response = handler(request)
        if inspect.isawaitable(response):
            response = await response
        if response.is_stream_consumed:
            return httpx.Response(response.status_code, headers=response.headers,
                                  stream=Chunks([response.content]))
        return response
    return httpx.MockTransport(streamed)


def acquire(handler, limits=GITHUB_LIMITS):
    output = io.BytesIO()
    source = asyncio.run(github.download_repository(github.parse_github_url('https://github.com/octocat/sample'), output,
                                                   limits=limits, transport=network_transport(handler)))
    return source, output


def test_stream_download_success(make_zip):
    archive = make_zip({'repo/main.c': 'int main(void){return 0;}'}).getvalue()
    handler, seen = handler_for(archive)
    source, output = acquire(handler)
    assert output.read() == archive
    assert source.snapshot_commit == COMMIT and source.default_branch == 'main'
    assert source.url == 'https://github.com/octocat/sample'
    assert [r.url.host for r in seen] == ['api.github.com']*3+['codeload.github.com']
    assert all('authorization' not in r.headers for r in seen)


@pytest.mark.parametrize('status,headers,code', [(404,{},'github_unavailable'), (403,{},'github_unavailable'),
    (429,{},'github_rate_limit'), (403,{'x-ratelimit-remaining':'0'},'github_rate_limit'),
    (403,{'retry-after':'60'},'github_rate_limit'), (409,{},'github_empty'), (500,{},'github_upstream')])
def test_upstream_failures(status, headers, code):
    handler,_ = handler_for(b'',status=status,headers=headers)
    with pytest.raises(AnalysisError) as error: acquire(handler)
    assert error.value.code == code


@pytest.mark.parametrize('location', ['http://codeload.github.com/octocat/sample/zip/'+COMMIT,
    'https://127.0.0.1/x', 'https://api.github.com/repos/evil/repo',
    'https://codeload.github.com.evil.test/octocat/sample/zip/'+COMMIT,
    'https://user@codeload.github.com/octocat/sample/zip/'+COMMIT,
    'https://codeload.github.com:443/octocat/sample/zip/'+COMMIT,
    'https://codeload.github.com/other/repo/zip/'+COMMIT,
    'https://codeload.github.com/octocat/sample/zip/'+'b'*40,
    'https://codeload.github.com/octocat/sample/zip/'+COMMIT+'?x',
    'https://codeload.github.com/octocat/sample/%2e%2e/zip/'+COMMIT, '//localhost/x',
    'https://[bad'])
def test_untrusted_redirect_not_followed(location):
    handler,seen=handler_for(b'',redirect=location)
    with pytest.raises(AnalysisError) as error: acquire(handler)
    assert error.value.code == 'github_redirect'
    assert len(seen) == 3


@pytest.mark.parametrize('headers,stream', [({'content-length':'999'},Chunks([b'123'])),
    ({},Chunks([b'12345', b'67890', b'1'])), ({'content-length':'2'},Chunks([b'12345678901']))])
def test_size_limit_enforced(headers,stream):
    handler,_=handler_for(b'',headers=headers,stream=stream)
    with pytest.raises(AnalysisError) as error: acquire(handler,replace(GITHUB_LIMITS,download_bytes=10))
    assert error.value.code == 'github_size_limit'


@pytest.mark.parametrize('kind', ['timeout','network','deadline'])
def test_network_and_deadline_failures(kind):
    async def handler(request):
        if kind=='deadline': await asyncio.sleep(.05)
        if kind=='timeout': raise httpx.ReadTimeout('sensitive internal detail')
        raise httpx.ConnectError('sensitive internal detail')
    with pytest.raises(AnalysisError) as error: acquire(handler,replace(GITHUB_LIMITS,total_seconds=.01))
    assert error.value.code == ('github_network' if kind=='network' else 'github_timeout')
    assert 'sensitive' not in error.value.message


def test_redirect_limit():
    handler,seen=handler_for(b'')
    def loop(request):
        if request.url.host=='codeload.github.com':
            seen.append(request)
            return httpx.Response(302,headers={'location':str(request.url)})
        return handler(request)
    with pytest.raises(AnalysisError) as error: acquire(loop,replace(GITHUB_LIMITS,redirects=1))
    assert error.value.code=='github_redirect'
    assert len(seen)==4


@pytest.mark.parametrize('metadata', [[], {}, {**METADATA,'private':True}, {**METADATA,'default_branch':None},
                                      {**METADATA,'owner':{'login':'../../local'}}])
def test_bad_metadata(metadata):
    with pytest.raises(AnalysisError) as error: acquire(lambda r: httpx.Response(200,json=metadata))
    assert error.value.code=='github_metadata'


@pytest.fixture
def mock_download(monkeypatch):
    def install(archive):
        handler,seen=handler_for(archive)
        real=github.download_repository
        async def mocked(repo,output):
            return await real(repo,output,transport=network_transport(handler))
        monkeypatch.setattr(analysis,'download_repository',mocked)
        return seen
    return install


@pytest.mark.parametrize('content,status', [('valid',200),('corrupt',400),('traversal',400)])
def test_shared_api_and_cleanup(content,status,client,make_zip,tmp_path,monkeypatch,mock_download):
    archive=make_zip({'repo/a.py':'x=1','repo/a.c':'int first(void){return 0;}\nint second(int x){return x;}'}).getvalue()
    if content=='corrupt': archive=b'not a zip'
    if content=='traversal': archive=make_zip({'../escape':'x'}).getvalue()
    mock_download(archive)
    created=[];handles=[]
    def directory(**kwargs):
        d=RealTemporaryDirectory(dir=tmp_path,**kwargs);created.append(Path(d.name));return d
    def file(**kwargs):
        f=RealTemporaryFile(dir=tmp_path,**kwargs);handles.append(f);return f
    monkeypatch.setattr(analysis,'TemporaryDirectory',directory)
    monkeypatch.setattr(analysis,'TemporaryFile',file)
    response=client.post('/api/analyze/github',json={'url':'https://github.com/octocat/sample.git/'})
    assert response.status_code==status,response.text
    assert handles and all(h.closed for h in handles)
    assert created and all(not p.exists() for p in created)
    if status==200:
        data=response.json()
        zipped=client.post('/api/analyze',files={'file':('same.zip',archive)}).json()
        assert data['source']=={'type':'github','filename':None,'owner':'octocat','name':'sample',
            'url':'https://github.com/octocat/sample','default_branch':'main','snapshot_commit':COMMIT}
        assert zipped['source']['type']=='zip' and zipped['source']['filename']=='same.zip'
        for field in ['summary','files','languages','skipped','defect_risk','structural']:
            assert data[field]==zipped[field],field
        # Only the repository node carries ingestion-specific display/provenance.
        for graph in (data['knowledge_graph'],zipped['knowledge_graph']):
            for node in graph['nodes']:
                if node['type']=='repository':
                    node['name']='repository'
                    node['metadata']['source']=None
        assert data['knowledge_graph']==zipped['knowledge_graph']
        assert '/tmp/' not in response.text


@pytest.fixture
def client():
    with TestClient(app) as client: yield client


def test_invalid_api_before_download(client,monkeypatch):
    async def no_download(*args): pytest.fail('Invalid URL fetched')
    monkeypatch.setattr(analysis,'download_repository',no_download)
    for payload in [{'url':'https://localhost/x/y'}, {'url':1}, {'url':'https://github.com/o/r','branch':'secret'}, {}]:
        assert client.post('/api/analyze/github',json=payload).status_code==422
    assert client.post('/api/analyze/github',content=b'x'*4097,headers={'content-type':'application/json'}).status_code==413


def test_download_failure_closes_temporary_file(client,tmp_path,monkeypatch):
    handles=[]
    def temporary(**kwargs):
        f=RealTemporaryFile(dir=tmp_path,**kwargs);handles.append(f);return f
    async def failed(*args): raise AnalysisError('Download timed out','github_timeout',504)
    monkeypatch.setattr(analysis,'TemporaryFile',temporary)
    monkeypatch.setattr(analysis,'download_repository',failed)
    assert client.post('/api/analyze/github',json={'url':'https://github.com/o/r'}).status_code==504
    assert handles and all(h.closed for h in handles)


def test_missing_model_github_still_analyzes(client,make_zip,mock_download,tmp_path,monkeypatch):
    from app.ml.repository import ModelService
    monkeypatch.setattr('app.ml.repository.SERVICE',ModelService(tmp_path/'absent'))
    mock_download(make_zip({'repo/a.c':'int a(void){return 0;}'}).getvalue())
    data=client.post('/api/analyze/github',json={'url':'https://github.com/octocat/sample'}).json()
    assert data['summary']['files']==1 and data['defect_risk']['status']=='unavailable'


def test_dashboard_contract(client):
    html=client.get('/').text
    for id in ['mode-zip','mode-github','github-form','github-url','analyze-github','source-meta','choose-file']:
        assert f'id="{id}"' in html
    js=client.get('/static/app.js').text
    assert "request.open('POST', '/api/analyze/github')" in js
    assert 'JSON.stringify(result, null, 2)' in js
    assert "link.rel = 'noopener noreferrer'" in js


def test_read_deadline_even_with_stream_progress():
    class SlowStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(20):
                await asyncio.sleep(.01)
                yield b'x'
    handler,_=handler_for(b'',stream=SlowStream())
    with pytest.raises(AnalysisError) as error: acquire(handler,replace(GITHUB_LIMITS,total_seconds=.035))
    assert error.value.code=='github_timeout'


def test_github_uses_shared_admission_limit():
    from app.middleware import UploadBoundary
    async def scenario():
        sent=[]
        async def app(*args): pytest.fail('Admission limit bypassed')
        async def receive(): pytest.fail('Busy request read')
        async def send(message): sent.append(message)
        boundary=UploadBoundary(app)
        boundary.active=2
        await boundary({'type':'http','method':'POST','path':'/api/analyze/github','headers':[]},receive,send)
        assert sent[0]['status']==429
        assert boundary.active==2
    asyncio.run(scenario())


def test_github_request_stream_limit_without_content_length():
    from app.middleware import UploadBoundary
    async def scenario():
        sent=[]
        async def app(*args): pytest.fail('Oversized body reached JSON parser')
        async def receive(): return {'type':'http.request','body':b'x'*4097,'more_body':False}
        async def send(message): sent.append(message)
        boundary=UploadBoundary(app)
        await boundary({'type':'http','method':'POST','path':'/api/analyze/github','headers':[]},receive,send)
        assert sent[0]['status']==413 and boundary.active==0
    asyncio.run(scenario())


def test_default_branch_is_encoded_and_snapshot_is_pinned(make_zip):
    handler,seen=handler_for(make_zip({'a.py':'x=1'}).getvalue())
    def branch_response(request):
        if request.url.path=='/repos/octocat/sample':
            seen.append(request)
            return httpx.Response(200,json={**METADATA,'default_branch':'release/stable'})
        return handler(request)
    source,_=acquire(branch_response)
    assert source.default_branch=='release/stable'
    assert b'release%2Fstable' in seen[1].url.raw_path
    assert seen[2].url.path.endswith('/zipball/'+COMMIT)


def test_real_model_github_inference(client,make_zip,mock_download):
    pytest.importorskip('sklearn')
    pytest.importorskip('tree_sitter')
    from app.ml.repository import SERVICE
    if SERVICE.load() is None:
        pytest.skip('Compatible local trusted model unavailable')
    mock_download(make_zip({'src/a.c':'int identity(int x){return x;}'}).getvalue())
    response=client.post('/api/analyze/github',json={'url':'https://github.com/octocat/sample'})
    assert response.status_code==200
    risk=response.json()['defect_risk']
    assert risk['analyzed_functions']==1
    assert risk['functions'][0]['path']=='src/a.c'
    assert 0<=risk['functions'][0]['model_probability']<=1

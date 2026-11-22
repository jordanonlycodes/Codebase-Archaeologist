"""Public GitHub acquisition. Only constructed API URLs and checked codeload redirects.

No credentials, proxy environment, shell commands or uploaded executable content.
"""
import asyncio
from dataclasses import dataclass
import json
import re
from urllib.parse import quote, urlsplit

import httpx

from app.analysis.models import RepositorySource
from app.config import GITHUB_LIMITS
from app.errors import AnalysisError

OWNER = r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?'
REPO = r'[A-Za-z0-9_.-]{1,100}'
SHA = re.compile(r'[0-9a-f]{40}')


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str

    @property
    def url(self):
        return f'https://github.com/{self.owner}/{self.name}'


def identifiers(owner, name):
    return (isinstance(owner, str) and isinstance(name, str)
            and re.fullmatch(OWNER, owner) and '--' not in owner
            and re.fullmatch(REPO, name) and name not in {'.', '..'}
            and not name.endswith('.git'))


def parse_github_url(value: str) -> GitHubRepository:
    message = 'Use https://github.com/owner/repository without credentials, ports, query parameters or extra paths.'
    if not isinstance(value, str) or len(value) > 2048:
        raise AnalysisError(message, 'invalid_github_url', 422)
    value = value.strip()
    # Raw grammar rejects percent escapes, Unicode confusables, backslashes,
    # empty query/fragment markers, authority ambiguity and URL parser repairs.
    match = re.fullmatch(r'https://(?i:github\.com)/('+OWNER+r')/('+REPO+r')/?', value)
    if not match:
        raise AnalysisError(message, 'invalid_github_url', 422)
    owner, name = match.groups()
    if name.endswith('.git'):
        name = name[:-4]
    if not identifiers(owner, name):
        raise AnalysisError(message, 'invalid_github_url', 422)
    return GitHubRepository(owner, name)


def upstream_error(response):
    status = response.status_code
    if status == 429 or (status == 403 and (response.headers.get('x-ratelimit-remaining') == '0' or 'retry-after' in response.headers)):
        raise AnalysisError('GitHub rate limit reached. Please try again later.', 'github_rate_limit', 429)
    if status in (401, 403, 404):
        raise AnalysisError('Repository not found, empty, private or inaccessible. Use a public repository with commits.', 'github_unavailable', 404)
    if status == 409:
        raise AnalysisError('This repository has no downloadable commits.', 'github_empty', 422)
    if status != 200:
        raise AnalysisError('GitHub could not provide the repository. Please retry later.', 'github_upstream', 502)


def redirect_url(value, repo):
    """Public API zipball redirects only to the exact codeload repository path."""
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 33 or ord(c) > 126 for c in value):
        raise AnalysisError('GitHub returned an unsupported archive redirect.', 'github_redirect', 502)
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise AnalysisError("GitHub returned an unsupported archive redirect.", "github_redirect", 502) from None
    prefix = f'/{repo.owner}/{repo.name}/'
    if (parsed.scheme != 'https' or parsed.netloc != 'codeload.github.com'
            or parsed.query or parsed.fragment or '?' in value or '#' in value
            or not parsed.path.startswith(prefix)
            or not re.fullmatch(r'(?:legacy\.zip|zip)/[0-9a-f]{40}', parsed.path[len(prefix):])):
        raise AnalysisError('GitHub returned an unsupported archive redirect.', 'github_redirect', 502)
    return value


async def read_limited(response, maximum, output=None):
    # Raw bytes prevent a compressed HTTP envelope from bypassing the bound.
    if response.headers.get('content-encoding', 'identity').lower() != 'identity':
        raise AnalysisError('GitHub returned an unsupported content encoding.', 'github_upstream', 502)
    length = response.headers.get('content-length')
    if length is not None:
        try:
            if int(length) < 0:
                raise ValueError
            oversized = int(length) > maximum
        except ValueError:
            raise AnalysisError('GitHub returned an invalid response.', 'github_upstream', 502) from None
        if oversized:
            raise AnalysisError('GitHub response exceeds the download size limit.', 'github_size_limit', 413)
    data = bytearray()
    size = 0
    async for chunk in response.aiter_raw():
        size += len(chunk)
        if size > maximum:
            raise AnalysisError('GitHub response exceeds the download size limit.', 'github_size_limit', 413)
        if output is None:
            data.extend(chunk)
        else:
            output.write(chunk)
    return bytes(data)


async def _download(repo, output, client, limits):
    base = f'https://api.github.com/repos/{repo.owner}/{repo.name}'
    async with client.stream('GET', base) as response:
        upstream_error(response)
        try:
            metadata = json.loads(await read_limited(response, limits.metadata_bytes))
            owner, name = metadata['owner']['login'], metadata['name']
            branch = metadata['default_branch']
            if (metadata.get('private') is not False or not identifiers(owner, name)
                    or not isinstance(branch, str) or not branch or len(branch) > 255
                    or any(ord(c) < 32 or ord(c) == 127 for c in branch)):
                raise ValueError
        except (KeyError, TypeError, ValueError, RecursionError):
            raise AnalysisError('GitHub returned unsupported repository metadata.', 'github_metadata', 502) from None
    # Use verified canonical identifiers; never follow metadata-provided URLs.
    repo = GitHubRepository(owner, name)
    base = f'https://api.github.com/repos/{owner}/{name}'
    async with client.stream('GET', base+'/commits/'+quote(branch, safe=''), headers={'Accept': 'application/vnd.github.sha'}) as response:
        upstream_error(response)
        try:
            commit = (await read_limited(response, 128)).decode('ascii').strip()
        except UnicodeDecodeError:
            commit = ''
        if not SHA.fullmatch(commit):
            raise AnalysisError('GitHub returned an invalid snapshot identifier.', 'github_metadata', 502)
    url = base+'/zipball/'+commit
    for hop in range(limits.redirects + 1):
        async with client.stream('GET', url) as response:
            if response.status_code in (301, 302, 303, 307, 308):
                if hop == limits.redirects:
                    raise AnalysisError('GitHub archive redirected too many times.', 'github_redirect', 502)
                url = redirect_url(response.headers.get('location'), repo)
                # A redirect must still address exactly the resolved snapshot.
                if not url.endswith('/'+commit):
                    raise AnalysisError('GitHub archive snapshot changed.', 'github_redirect', 502)
                continue
            upstream_error(response)
            await read_limited(response, limits.download_bytes, output)
            output.seek(0)
            return RepositorySource('github', owner=owner, name=name, url=repo.url,
                                    default_branch=branch, snapshot_commit=commit)
    raise AssertionError('Unreachable download state')


async def download_repository(repo, output, *, limits=GITHUB_LIMITS, transport=None):
    """Streaming acquisition deadline includes all API requests and redirects.

    transport is a test seam; production always uses verified TLS and no proxies.
    """
    timeout = httpx.Timeout(limits.read_seconds, connect=limits.connect_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, trust_env=False,
                                     transport=transport, headers={
                                         'User-Agent': 'Codebase-Archaeologist',
                                         'Accept': 'application/vnd.github+json',
                                         'Accept-Encoding': 'identity',
                                         'X-GitHub-Api-Version': '2022-11-28',
                                     }) as client:
            return await asyncio.wait_for(_download(repo, output, client, limits), limits.total_seconds)
    except (asyncio.TimeoutError, httpx.TimeoutException):
        raise AnalysisError('GitHub download timed out. Try a smaller repository or retry later.', 'github_timeout', 504) from None
    except (httpx.HTTPError, OSError):
        raise AnalysisError('Could not download from GitHub. Check server network access and retry.', 'github_network', 502) from None

# Public GitHub ingestion

`POST /api/analyze/github` accepts only a JSON object with `url` (up to 2,048 characters). Example: `{"url":"https://github.com/owner/repository"}`. Extra keys are rejected; no authentication or branch/ref parameter is accepted. `POST /api/analyze` remains the existing multipart ZIP endpoint.

## Contract and shared pipeline

The response is `AnalysisResult` (schema 1.0) with an additive optional `source` field. Both ingress paths call `analyze_archive` in `app/routes/analysis.py`: existing secure extraction → static scanner → cached C-function inference → serialized results. Archive wrapper directories are retained just as with uploaded ZIPs. A GitHub snapshot and an uploaded copy of that same archive have identical inventory/static/ML results; display identity, timestamps and provenance differ. GitHub names its own archive wrapper, so unrelated manually packaged ZIPs may have different relative paths.

| Source field | ZIP | GitHub |
| --- | --- | --- |
| type | `zip` | `github` |
| filename | Sanitized upload filename | null |
| owner / name | null | Verified repository API identity |
| url | null | Constructed canonical HTTPS GitHub link |
| default_branch | null | Repository API default branch |
| snapshot_commit | null | Full commit SHA resolved before downloading |

Top-level `analyzed_at` remains the analysis timestamp. These fields are exported with the complete JSON result. There is no Git history traversal, project-level risk probability or ML prediction for unsupported languages.

## Verified endpoint contracts

The implementation uses GitHub's documented APIs:

1. [Get a repository](https://docs.github.com/en/rest/repos/repos#get-a-repository): `GET https://api.github.com/repos/{owner}/{repo}` for public/default-branch metadata.
2. [Get a commit](https://docs.github.com/en/rest/commits/commits#get-a-commit): the encoded default branch is resolved using `application/vnd.github.sha`.
3. [Download a ZIP archive](https://docs.github.com/en/rest/repos/contents#download-a-repository-archive-zip): `GET /repos/{owner}/{repo}/zipball/{sha}` redirects to the snapshot archive. The default branch is pinned to its resolved SHA to avoid reporting a branch/commit inconsistent with downloaded contents.

No user URL is fetched directly. Repository and owner identifiers use bounded ASCII grammar. Percent escapes, backslashes, arbitrary hosts, credentials, all explicit ports (including 443), queries/fragments (including empty markers), non-HTTPS schemes and extra path components are rejected before acquisition. A final `.git` suffix and trailing slash may be removed. The parser is independent of network access.

Outbound requests use only constructed `api.github.com` URLs and validated `codeload.github.com` archive redirects. The exact repository path and commit are checked on every redirect; unexpected destinations, relative redirects, ports or URL encodings fail closed. API metadata redirects are deliberately not followed. Submit the canonical current URL for a moved/renamed repository. Fixed trusted hostnames, TLS certificate validation and no environment proxies prevent user-selected network destinations. The server relies on the normal trusted DNS/CA configuration for these fixed GitHub hosts.

`httpx` was already a project dependency. Its async streaming client has automatic redirects and environment credentials/proxies disabled. API version `2022-11-28` is explicitly selected. No access token is sent. Rate limits therefore apply to the server's unauthenticated IP. Successful metadata must say `private: false`; source identity is validated again before constructing further requests. No upstream response body or internal exception is shown as an error message.

## Limits and failure behavior

`GITHUB_LIMITS` in `app/config.py` holds 10-second connection/read timeouts, a 60-second acquisition deadline across all requests and redirects, at most three archive redirects, 256 KiB metadata, 128-byte commit response, 25 MiB archive and 4 KiB JSON request body. The acquisition deadline cancels stalled or continually progressing downloads; repository extraction/inference then uses the existing workload limits. This deadline is not an overall analysis CPU deadline. HTTP content encoding other than identity is rejected, and downloaded bytes are capped during streaming even with absent or false Content-Length.

Both POST routes share two concurrent analysis slots per process; a third receives `429 busy`. Existing ZIP transport/body limits remain intact. Archives use a temporary file and analysis uses an isolated temporary directory. Normal completion, upstream failure, invalid archive and analysis failure close/delete these resources. Process crashes retain the same OS temporary-file cleanup limitations as ZIP uploads.

| Error | Status | Meaning |
| --- | --- | --- |
| invalid_github_url / invalid_request | 422 | Unsupported URL or JSON schema |
| github_unavailable | 404 | Not found, private, inaccessible or empty archive |
| github_empty | 422 | No downloadable commits |
| github_rate_limit | 429 | Retry later; no automatic retry loop |
| github_timeout | 504 | Read/connect/total acquisition timeout |
| github_size_limit | 413 | Metadata or archive exceeds its byte bound |
| github_network | 502 | Network/TLS/transport failure |
| github_metadata / github_redirect / github_upstream | 502 | Unsupported or failed upstream response |

Existing archive errors preserve their established codes/statuses. Shared extraction rejects unsafe paths, symlinks/special entries, bombs and corruption. Downloaded content is never executed, cloned through shell commands or installed. Uploaded or downloaded repositories cannot supply model artifacts. Missing compatible trusted artifacts still yield static results plus a truthful model-unavailable state.

## Local verification

```bash
cd /home/jordan/Projects/codebase-archaeologist
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Select **Import from GitHub**, submit a small public repository, and confirm the source link, branch and full commit appear. A candidate for C inference is `https://github.com/antirez/kilo` (availability/size is an external dependency; choose any small public C repository if it exceeds limits). Verify extracted C function locations and probabilities when trusted local artifacts load. Unsupported languages receive static results. Use **Export JSON**, inspect `source`, `summary` and `defect_risk`, then upload the same snapshot ZIP through **Upload ZIP** to compare contents. Check the controls at desktop/tablet/mobile widths and keyboard focus.

```bash
curl --fail-with-body -H 'Content-Type: application/json' \
  -d '{"url":"https://github.com/octocat/Hello-World"}' \
  http://127.0.0.1:8000/api/analyze/github > github-analysis.json
curl -H 'Content-Type: application/json' \
  -d '{"url":"http://localhost/private"}' \
  http://127.0.0.1:8000/api/analyze/github
curl -H 'Content-Type: application/json' \
  -d '{"url":"https://github.com/octocat/CodebaseArchaeologistMissingRepositoryExample"}' \
  http://127.0.0.1:8000/api/analyze/github
python -m pytest -q tests/test_github.py
python -m pytest -q
```

Network calls are mocked in tests and need no credentials. The full suite retains Task 2's two small authentic-data serialization/reproducibility fitting tests; it does not rerun benchmark training or held-out evaluation. No model changes are part of this feature. For socket-restricted sandbox testing, use the selector wrapper already documented in `ml_pipeline.md`. Live GitHub/browser verification could not be completed in the development sandbox because DNS/socket access is restricted; mocked integration is not represented as live verification.

Task 4A.1 verification: **228 passed, 0 failed, 0 skipped** (140 prior tests plus 88 new cases). The new tests use mocked network responses, including a genuine saved-model prediction through the GitHub endpoint. JavaScript syntax checks passed. One pre-existing Starlette/httpx deprecation warning remains.

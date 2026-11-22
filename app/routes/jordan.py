"""Stateless evidence explanation. Browser snapshots never become a shared server cache."""
import json
from fastapi import APIRouter, Request
from app.errors import AnalysisError
from app.jordan.provider import Configuration, OpenAIProvider
from app.jordan.schemas import Capabilities, ExplainRequest, Explanation

router = APIRouter(prefix='/api/jordan', tags=['jordan'])


@router.get('/capabilities', response_model=Capabilities)
async def capabilities():
    return Capabilities(cloud_available=Configuration.load() is not None)


@router.post('/explain', response_model=Explanation)
async def explain(body: ExplainRequest, request: Request):
    origin = request.headers.get('origin')
    if request.headers.get('sec-fetch-site') == 'cross-site' or (origin and origin != str(request.base_url).rstrip('/')):
        raise AnalysisError('Cloud requests must originate from this application.', 'origin_rejected', 403)
    if not body.consent:
        raise AnalysisError('Explicit consent to disclose this question and evidence is required for every cloud request.', 'consent_required', 403)
    config = Configuration.load()
    if config is None:
        raise AnalysisError('AI enhancement is not configured. Local intelligence remains available.', 'provider_unconfigured', 503)
    evidence = [{'id': 'E' + str(i + 1), **e.model_dump()} for i, e in enumerate(body.evidence)]
    if len(json.dumps(evidence, ensure_ascii=False).encode()) > 24576:
        raise AnalysisError('Selected evidence exceeds 24 KiB. Narrow the investigation.', 'evidence_limit', 413)
    generated = await OpenAIProvider(config).explain(body.question, evidence)
    selected = set(generated.citation_ids)
    return Explanation(answer=generated.answer, citations=[e for e in evidence if e['id'] in selected],
                       limitations=['AI-generated interpretation of client-supplied analysis facts; not independently verified source code.',
                                    'Static relationships are not runtime guarantees. C-model scores are uncalibrated research estimates.',
                                    'No source bodies supplied. Valid citations do not prove every generated claim is supported.'
                                    if selected else 'The provider supplied no evidence citations; treat this explanation as unsupported.'])

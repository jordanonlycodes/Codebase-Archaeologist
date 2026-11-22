from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import LIMITS

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")


@router.get("/", include_in_schema=False)
async def landing(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html")


PAGES = {
    'time-machine': dict(title='Codebase Time Machine', subtitle='AUTHENTIC HISTORY / OBSERVABLE EVOLUTION', description='Travel through real commits, inspect historical change and compare the evidence between revisions.', feature='time-machine'),
    'jordan': dict(title='Jordan', subtitle='YOUR REPOSITORY / TRACEABLE INTELLIGENCE', description='Ask precise questions. Follow real evidence. An engineering companion grounded in your active snapshot.', feature='jordan'),
    'overview': dict(title='Repository overview', subtitle='THE BIG PICTURE', description='An editorial map of your snapshot, its composition and the evidence worth exploring.', feature='overview'),
    'risk': dict(title='Defect risk intelligence', subtitle='C FUNCTIONS / RESEARCH MODEL', description='Model-estimated defect-related patterns. A review signal, never a vulnerability verdict.', feature='risk'),
    'structure': dict(title='Structural intelligence', subtitle='C + PYTHON / DETERMINISTIC METRICS', description='Inspect the decisions, depth and dimensions of real function definitions.', feature='structure'),
    'graph': dict(title='Knowledge explorer', subtitle='HIERARCHY / CALLS / DEPENDENCIES', description='One source-grounded graph. Explore its relationships in analytical 2D or spatial 3D.', feature='graph'),
    'architecture': dict(title='Architecture atlas', subtitle='DIRECTORY COMPONENTS / OBSERVED RELATIONSHIPS', description='Read the architectural shape supported by your files and resolved static relationships.', feature='architecture'),
    'heatmaps': dict(title='Repository heatmaps', subtitle='SIX METRICS / NESTED SOURCE LANDSCAPES', description='See where size, complexity and review signals concentrate. Missing measurements stay explicit.', feature='architecture'),
    'blast-radius': dict(title='Blast radius explorer', subtitle='POTENTIAL IMPACT / INSPECTABLE EVIDENCE', description='Follow upstream dependents and downstream dependencies from a precise change origin.', feature='blast-radius'),
}

ASSETS = {
    'time-machine': (['time_machine/workspace.css'], ['time_machine/data.js','time_machine/timeline.js','time_machine/landscape.js','time_machine/studio.js','time_machine/workspace.js']),
    'jordan': (['jordan/workspace.css'], ['impact/engine.js','jordan/retrieval.js','jordan/local.js','jordan/workspace.js']),
    'overview': ([], ['product/overview.js']),
    'risk': ([], ['risk.js']),
    'structure': ([], ['structural.js']),
    'graph': (['graph/explorer.css'], ['graph/data.js','graph/layouts.js','graph/svg.js','graph/quality.js','graph/three.js','graph/explorer.js']),
    'architecture': (['architecture/explorer.css'], ['graph/data.js','graph/layouts.js','architecture/data.js','architecture/scene.js','architecture/explorer.js']),
    'heatmaps': (['architecture/explorer.css'], ['graph/data.js','graph/layouts.js','architecture/data.js','architecture/scene.js','architecture/explorer.js']),
    'blast-radius': (['impact/explorer.css'], ['architecture/scene.js','impact/engine.js','impact/explorer.js']),
}


@router.get('/explore', include_in_schema=False)
async def explore(request: Request):
    return templates.TemplateResponse(request=request, name='explore.html', context={'upload_limit':LIMITS.upload_bytes})


@router.get('/workspace/{page}', include_in_schema=False)
async def workspace(request: Request, page: str):
    from fastapi import HTTPException
    if page not in PAGES:
        raise HTTPException(404, 'Workspace not found.')
    styles, scripts = ASSETS[page]
    return templates.TemplateResponse(request=request, name='workspace.html', context={
        **PAGES[page], 'page':page, 'pages':PAGES, 'number':f'{list(PAGES).index(page)+1:02}',
        'styles':styles, 'scripts':scripts})


@router.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "codebase-archaeologist"}

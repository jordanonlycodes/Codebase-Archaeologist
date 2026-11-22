"""Stateless public history operations; no server paths, session store or source cache."""
from typing import Annotated
from pydantic import BaseModel,ConfigDict,Field,StringConstraints
from fastapi import APIRouter
from app.errors import AnalysisError
from app.history.core import collect,compare
from app.history.github import operation
from app.history.models import History,RevisionTree,Comparison,LIMITS

router=APIRouter(prefix='/api/history',tags=['time-machine'])
SHA=Annotated[str,StringConstraints(pattern=r'^[0-9a-f]{40}$')]


class Source(BaseModel):
    model_config=ConfigDict(extra='forbid')
    url: str=Field(min_length=1,max_length=2048)
    anchor: SHA


class Revision(Source):
    revision: SHA


class Pair(Source):
    base: SHA
    head: SHA


async def retained(reader,anchor,*ids):
    commits=await reader.list_commits(anchor,LIMITS.commits+1)
    if not set(ids)<=set(commits[:LIMITS.commits]):
        raise AnalysisError('Select revisions from this pinned retained history window.','revision_outside_window',422)


@router.post('/load',response_model=History)
async def load(body:Source):
    return await operation(body.url,lambda r:collect(r,body.anchor))


@router.post('/tree',response_model=RevisionTree)
async def tree(body:Revision):
    async def work(reader):
        await retained(reader,body.anchor,body.revision)
        return await reader.tree(body.revision)
    return await operation(body.url,work)


@router.post('/compare',response_model=Comparison)
async def comparison(body:Pair):
    async def work(reader):
        await retained(reader,body.anchor,body.base,body.head)
        return await compare(reader,body.base,body.head)
    return await operation(body.url,work)

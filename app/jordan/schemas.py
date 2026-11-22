"""Small fact-only contract. No source bodies, arbitrary metadata or analysis payloads."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Short = Annotated[str, StringConstraints(max_length=256)]


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Fact(Strict):
    label: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    value: Short


class Evidence(Strict):
    entity_id: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    kind: Literal['repository', 'directory', 'file', 'function', 'component', 'relationship']
    name: Short
    path: Short | None = None
    line: Annotated[int, Field(ge=1, le=10_000_000)] | None = None
    facts: Annotated[list[Fact], Field(max_length=16)]


class ExplainRequest(Strict):
    question: Annotated[str, StringConstraints(min_length=1, max_length=1600)]
    consent: bool
    evidence: Annotated[list[Evidence], Field(min_length=1, max_length=12)]

    @field_validator('question')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('Question must not be blank')
        return value.strip()


class Generated(Strict):
    answer: Annotated[str, StringConstraints(min_length=1, max_length=6000)]
    citation_ids: Annotated[list[Annotated[str, StringConstraints(pattern=r'^E[1-9][0-9]?$')]], Field(max_length=12)]


class Citation(Evidence):
    id: str


class Explanation(Strict):
    mode: Literal['cloud'] = 'cloud'
    answer: str
    citations: list[Citation]
    limitations: list[str]


class Capabilities(Strict):
    local: bool = True
    cloud_available: bool
    configuration_issues: list[Literal['cloud_disabled', 'missing_key', 'invalid_key', 'missing_model', 'invalid_model']] = Field(default_factory=list)
    provider: str = 'OpenAI Responses API'
    request_bytes: int = 32768
    evidence_records: int = 12
    source_bodies_retained: bool = False

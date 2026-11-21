"""Public response contracts for optional C-function inference."""
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class FunctionResult:
    name: str | None
    path: str
    start_line: int
    end_line: int
    status: str
    predicted_class: int | None = None
    model_probability: float | None = None
    features: dict[str, float | None] = field(default_factory=dict)


@dataclass
class FileIssue:
    path: str
    reason: str


@dataclass
class DefectRisk:
    status: Literal['ready', 'partial', 'unavailable', 'no_functions']
    message: str
    model_version: str | None = None
    schema_version: str = '1.0'
    analyzed_functions: int = 0
    defect_related: int = 0
    non_defect_related: int = 0
    skipped_functions: int = 0
    eligible_files: int = 0
    unsupported_source_files: int = 0
    functions: list[FunctionResult] = field(default_factory=list)
    file_issues: list[FileIssue] = field(default_factory=list)

"""Versioned, source-free contracts for structural analysis and future node links."""
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Composition:
    physical_lines: int
    blank_lines: int
    comment_lines: int | None = None
    code_lines: int | None = None
    comment_density: float | None = None
    status: str = 'unavailable'


@dataclass
class FunctionStructure:
    id: str
    file_id: str
    name: str | None
    qualified_name: str | None
    path: str
    language: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    span_lines: int
    status: str
    parameter_count: int | None = None
    cyclomatic_complexity: int | None = None
    max_nesting_depth: int | None = None
    decision_points: int | None = None
    loop_count: int | None = None
    conditional_count: int | None = None
    complexity_band: str | None = None
    ml_result_index: int | None = None
    ml_status: str = 'unavailable'


@dataclass
class ComplexitySummary:
    analyzed_functions: int = 0
    average_complexity: float | None = None
    maximum_complexity: int | None = None
    total_complexity: int | None = None
    maximum_nesting: int | None = None
    high_complexity_functions: int = 0
    large_functions: int = 0
    deeply_nested_functions: int = 0
    complexity_bands: dict[str, int] = field(default_factory=lambda: dict.fromkeys(['low', 'moderate', 'high', 'very_high'], 0))


@dataclass
class FileStructure:
    id: str
    path: str
    language: str
    status: str
    composition: Composition
    summary: ComplexitySummary = field(default_factory=ComplexitySummary)
    reasons: list[str] = field(default_factory=list)


@dataclass
class HotspotReason:
    metric: str
    value: int
    threshold: int
    explanation: str


@dataclass
class StructuralHotspot:
    function_id: str
    file_id: str
    path: str
    name: str | None
    start_line: int
    end_line: int
    reasons: list[HotspotReason]


@dataclass
class StructuralCoverage:
    supported_languages: list[str] = field(default_factory=lambda: ['C (.c)', 'Python (.py, .pyi)'])
    included_files: int = 0
    supported_files: int = 0
    analyzed_files: int = 0
    unsupported_files: int = 0
    skipped_files: int = 0
    partial_files: int = 0
    invalid_functions: int = 0
    parsed_bytes: int = 0
    visited_nodes: int = 0
    composition_files: int = 0
    composition_physical_lines: int = 0
    truncated: bool = False
    complete: bool = False


@dataclass
class StructuralIntelligence:
    status: Literal['complete', 'partial', 'no_supported_files', 'no_functions']
    summary: ComplexitySummary
    coverage: StructuralCoverage
    composition: Composition
    files: list[FileStructure]
    functions: list[FunctionStructure]
    hotspots: list[StructuralHotspot]
    thresholds: dict[str, int]
    limits: dict[str, int]
    definitions: dict[str, str]
    schema_version: str = '1.0'

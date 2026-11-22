"""Source-free, versioned architecture contracts; absent measurements stay null."""
from dataclasses import dataclass, field


@dataclass
class Metrics:
    files: int = 0
    source_files: int = 0
    physical_lines: int = 0
    bytes: int = 0
    functions: int | None = None
    max_complexity: int | None = None
    total_complexity: int | None = None
    hotspots: int | None = None
    max_c_function_score: float | None = None
    scored_functions: int = 0
    measured_files: dict[str, int] = field(default_factory=dict)


@dataclass
class HeatNode:
    id: str
    parent_id: str | None
    name: str
    path: str
    type: str
    metrics: Metrics
    graph_id: str | None = None
    component_id: str | None = None
    language: str | None = None
    structural_status: str = 'unavailable'
    ml_status: str = 'unavailable'


@dataclass
class Component:
    id: str
    name: str
    path: str
    metrics: Metrics
    file_ids: list[str]
    function_ids: list[str]
    graph_id: str | None = None
    incoming_components: list[str] = field(default_factory=list)
    outgoing_components: list[str] = field(default_factory=list)
    unresolved_ids: list[str] = field(default_factory=list)
    unresolved_count: int = 0
    unresolved_truncated: bool = False
    intra_component_edges: int = 0
    intra_component_occurrences: int = 0


@dataclass
class ComponentEdge:
    id: str
    source: str
    target: str
    type: str
    graph_edges: int = 0
    occurrences: int = 0
    edge_ids: list[str] = field(default_factory=list)
    evidence_truncated: bool = False


@dataclass
class Coverage:
    inventory_files: int = 0
    retained_files: int = 0
    graph_mapped_files: int = 0
    structural_measured_files: int = 0
    retained_graph_edges_observed: int = 0
    semantic_edges: int = 0
    unmapped_semantic_edges: int = 0
    omitted_component_edges: int = 0
    unmapped_references: int = 0
    truncated: bool = False
    graph_truncated: bool = False
    structural_truncated: bool = False
    graph_complete: bool = False
    structural_complete: bool = False
    issues: list[str] = field(default_factory=list)


@dataclass
class Architecture:
    components: list[Component]
    edges: list[ComponentEdge]
    heatmap: list[HeatNode]
    dependency_cycles: list[list[str]]
    findings: list[dict[str, str]]
    summary: dict[str, int]
    coverage: Coverage
    definitions: dict[str, str]
    limits: dict[str, int]
    schema_version: str = '1.0'

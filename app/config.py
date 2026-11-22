from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    upload_bytes: int = 25 * 1024 * 1024
    expanded_bytes: int = 100 * 1024 * 1024
    file_bytes: int = 2 * 1024 * 1024
    entries: int = 5000
    depth: int = 30
    path_bytes: int = 240
    compression_ratio: int = 200


LIMITS = Limits()


@dataclass(frozen=True)
class GitHubLimits:
    download_bytes: int = LIMITS.upload_bytes
    metadata_bytes: int = 256 * 1024
    request_bytes: int = 4096
    connect_seconds: float = 10
    read_seconds: float = 10
    total_seconds: float = 60
    redirects: int = 3


GITHUB_LIMITS = GitHubLimits()


@dataclass(frozen=True)
class StructuralLimits:
    file_bytes: int = 512 * 1024
    total_bytes: int = 8 * 1024 * 1024
    function_bytes: int = 128 * 1024
    functions: int = 2000
    nodes_per_file: int = 100_000
    total_nodes: int = 400_000


STRUCTURAL_LIMITS = StructuralLimits()


@dataclass(frozen=True)
class StructuralThresholds:
    low_max: int = 5
    moderate_max: int = 10
    high_max: int = 20
    high_complexity: int = 11
    large_span: int = 80
    deep_nesting: int = 4
    many_parameters: int = 6


STRUCTURAL_THRESHOLDS = StructuralThresholds()


@dataclass(frozen=True)
class GraphLimits:
    file_bytes: int = STRUCTURAL_LIMITS.file_bytes
    total_bytes: int = STRUCTURAL_LIMITS.total_bytes
    nodes_per_file: int = 100_000
    traversal_nodes: int = 400_000
    nodes: int = 12_000
    edges: int = 20_000
    symbols: int = 4_000
    references: int = 12_000
    unresolved: int = 4_000
    evidence_per_edge: int = 8
    reference_chars: int = 256
    output_bytes: int = 12 * 1024 * 1024

    def __post_init__(self):
        if self.output_bytes < 16384 or any(value < 0 for value in vars(self).values()):
            raise ValueError("Graph limits must be nonnegative, with at least 16 KiB for the output envelope.")


GRAPH_LIMITS = GraphLimits()


@dataclass(frozen=True)
class ArchitectureLimits:
    heat_nodes: int = 10_000
    components: int = 1_000
    component_edges: int = 8_000
    evidence_ids: int = 8
    reference_ids: int = 16

    def __post_init__(self):
        if self.heat_nodes < 1 or any(value < 0 for value in vars(self).values()):
            raise ValueError("Architecture limits must be nonnegative and retain at least the heatmap root.")


ARCHITECTURE_LIMITS = ArchitectureLimits()


def github_history_token():
    """Optional operator credential; validated without reflecting its contents."""
    import os
    token=os.environ.get('CODEBASE_GITHUB_TOKEN','').strip()
    if len(token)>512 or any(ord(c)<33 or ord(c)>126 for c in token):
        raise ValueError('Invalid server GitHub credential configuration.')
    return token

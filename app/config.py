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

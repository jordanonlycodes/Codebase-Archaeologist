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

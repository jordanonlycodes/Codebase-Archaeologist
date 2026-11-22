from dataclasses import dataclass, field


@dataclass(frozen=True)
class HistoryLimits:
    commits: int = 24
    files_per_commit: int = 100
    changes: int = 4000
    tree_files: int = 5000
    comparison_files: int = 200
    text_files: int = 8
    blob_bytes: int = 65536
    text_lines: int = 2000
    patch_bytes: int = 65536
    response_bytes: int = 2 * 1024 * 1024
    transfer_bytes: int = 12 * 1024 * 1024
    requests: int = 90
    seconds: int = 60


LIMITS = HistoryLimits()


@dataclass
class Change:
    path: str
    status: str
    previous_path: str | None = None
    additions: int | None = None
    deletions: int | None = None
    line_status: str = 'unavailable'
    patch: str | None = None
    patch_truncated: bool = False


@dataclass
class Commit:
    sha: str
    parents: list[str]
    author: str
    author_date: str
    committer_date: str
    subject: str
    tree: str
    files: list[Change] = field(default_factory=list)
    files_complete: bool = True


@dataclass
class TreeFile:
    path: str
    sha: str
    mode: str
    size: int | None = None


@dataclass
class RevisionTree:
    revision: str
    files: list[TreeFile]
    complete: bool
    issues: list[str] = field(default_factory=list)


@dataclass
class Coverage:
    complete_ancestry: bool = False
    scope: str = 'Ancestors of the pinned snapshot; bounded retained window, not all repository branches.'
    ordering: str = 'upstream commit-list order; timeline separately orders committer dates'
    issues: list[str] = field(default_factory=list)
    missing_parents: list[str] = field(default_factory=list)


@dataclass
class History:
    repository_url: str
    anchor: str
    commits: list[Commit]
    coverage: Coverage
    activity: list[dict]
    churn: list[dict]
    limits: dict
    source: str = 'github-rest'
    schema_version: str = '1.0'


@dataclass
class Comparison:
    repository_url: str
    base: str
    head: str
    files: list[Change]
    complete_file_list: bool
    issues: list[str]
    semantics: str = 'Exact base tree → head tree; unique identical-blob renames only. Text statistics use bounded SequenceMatcher line diffs.'

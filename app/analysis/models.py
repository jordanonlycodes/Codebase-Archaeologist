from dataclasses import dataclass


@dataclass
class FileMetrics:
    path: str
    language: str
    is_source: bool
    bytes: int
    lines: int
    blank_lines: int
    nonblank_lines: int
    comment_lines: int | None
    code_lines: int | None


@dataclass
class LanguageMetrics:
    language: str
    files: int
    bytes: int
    lines: int
    percentage: float


@dataclass
class Summary:
    files: int
    source_files: int
    directories: int
    languages: int
    bytes: int
    total_lines: int
    source_lines: int
    blank_lines: int
    known_comment_lines: int
    comment_counted_files: int
    comment_uncounted_files: int
    skipped_files: int


@dataclass
class AnalysisResult:
    repository: str
    analyzed_at: str
    archive_entries: int
    summary: Summary
    languages: list[LanguageMetrics]
    files: list[FileMetrics]
    largest_files: list[FileMetrics]
    skipped: dict[str, int]
    notes: list[str]
    schema_version: str = "1.0"

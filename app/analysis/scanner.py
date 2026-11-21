import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from app.analysis.languages import identify
from app.analysis.lines import measure
from app.analysis.models import AnalysisResult, FileMetrics, LanguageMetrics, Summary
from app.analysis.policy import exclusion_reason
from app.config import LIMITS, Limits
from app.errors import AnalysisError


def scan_repository(root: Path, repository: str, ingestion: dict,
                    limits: Limits = LIMITS) -> AnalysisResult:
    files = []
    directories = 0
    skipped = Counter(ingestion["skipped"])
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if not (current_path / d).is_symlink()
                         and not (current_path / d / "pyvenv.cfg").exists()
                         and not exclusion_reason(PurePosixPath((current_path / d).relative_to(root).as_posix()), True))
        if current_path != root:
            directories += 1
        for name in sorted(names):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            reason = exclusion_reason(PurePosixPath(relative))
            if path.is_symlink() or not path.is_file():
                skipped["special_file"] += 1
                continue
            if reason:
                skipped[reason] += 1
                continue
            with path.open("rb") as source:
                data = source.read(limits.file_bytes + 1)
            if len(data) > limits.file_bytes:
                raise AnalysisError("A scanned file exceeds the file size limit.", "archive_limit", 413)
            # UTF-8 text only; control bytes indicate binary content regardless of suffix.
            if any(byte < 32 and byte not in (9, 10, 12, 13) for byte in data):
                skipped["binary_or_non_utf8"] += 1
                continue
            try:
                text = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                skipped["binary_or_non_utf8"] += 1
                continue
            language, is_source = identify(path)
            files.append(FileMetrics(path=relative, language=language, is_source=is_source,
                                     bytes=len(data), **measure(text, language)))
    if not files:
        raise AnalysisError("No supported text files remain after exclusions. Upload a repository containing UTF-8 source or text files.",
                            "empty_repository", 422)
    files.sort(key=lambda f: f.path)
    groups = defaultdict(lambda: {"files": 0, "bytes": 0, "lines": 0})
    for file in files:
        group = groups[file.language]
        group["files"] += 1
        group["bytes"] += file.bytes
        group["lines"] += file.lines
    languages = [LanguageMetrics(language=name, **values,
                                 percentage=round(values["files"] / len(files) * 100, 2))
                 for name, values in sorted(groups.items(), key=lambda item: (-item[1]["files"], item[0]))]
    counted = sum(f.comment_lines is not None for f in files)
    return AnalysisResult(
        repository=repository, analyzed_at=datetime.now(timezone.utc).isoformat(),
        archive_entries=ingestion["archive_entries"],
        summary=Summary(
            files=len(files), source_files=sum(f.is_source for f in files), directories=directories,
            languages=len(languages), bytes=sum(f.bytes for f in files),
            total_lines=sum(f.lines for f in files), source_lines=sum(f.lines for f in files if f.is_source),
            blank_lines=sum(f.blank_lines for f in files),
            known_comment_lines=sum(f.comment_lines or 0 for f in files),
            comment_counted_files=counted, comment_uncounted_files=len(files) - counted,
            skipped_files=sum(skipped.values()),
        ), languages=languages, files=files,
        largest_files=sorted(files, key=lambda f: (-f.bytes, f.path))[:5], skipped=dict(skipped),
        notes=[
            "Source lines are physical lines in recognized source files, including blanks and comments; configuration and documentation are excluded from this metric.",
            "Comment-only lines are counted for tokenizable Python and standard JSON only. Inline comments remain code lines; Python docstrings remain code. Null means unavailable, not zero.",
            "Language percentages use included file counts. Directories exclude the extraction root and excluded paths; archive wrapper directories are retained.",
            "Binary, nested archive, non-UTF-8, dependency, environment, cache and build files are omitted. No repository code was executed.",
            "These are descriptive metrics, not vulnerability findings. No trained model or risk prediction is available.",
        ],
    )

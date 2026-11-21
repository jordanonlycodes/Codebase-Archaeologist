"""Validate ZIP metadata before creating files; never use extractall or run code."""

import stat
import struct
import zipfile
import zlib
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from app.analysis.policy import exclusion_reason
from app.config import LIMITS, Limits
from app.errors import AnalysisError


def _preflight(stream: BinaryIO, limits: Limits) -> None:
    """Bound central-directory entries before ZipFile allocates ZipInfo objects.

    Only conventional, single-volume ZIPs are accepted. ZIP64 and self-extracting
    archives are unnecessary at these size limits and deliberately unsupported.
    """
    stream.seek(0, 2)
    size = stream.tell()
    if size > limits.upload_bytes:
        raise AnalysisError("ZIP exceeds the 25 MiB upload limit.", "archive_limit", 413)
    stream.seek(max(0, size - 65557))
    tail = stream.read()
    end = tail.rfind(b"PK\x05\x06")
    if end < 0 or len(tail) - end < 22:
        raise AnalysisError("This file is not a complete ZIP archive.")
    _, disk, cd_disk, on_disk, total, cd_size, offset, comment = struct.unpack(
        "<4s4H2IH", tail[end:end + 22]
    )
    if disk or cd_disk or on_disk != total or total == 65535:
        raise AnalysisError("Split and ZIP64 archives are unsupported.")
    if end + 22 + comment != len(tail) or offset + cd_size != size - len(tail) + end:
        raise AnalysisError("ZIP directory metadata is invalid or unsupported.")
    if total > limits.entries:
        raise AnalysisError("Archive contains too many entries (maximum 5,000).", "archive_limit", 413)
    stream.seek(offset)
    consumed = count = 0
    while consumed < cd_size:
        header = stream.read(46)
        if len(header) != 46 or header[:4] != b"PK\x01\x02":
            raise AnalysisError("ZIP central directory is malformed.")
        name_len, extra_len, comment_len = struct.unpack_from("<3H", header, 28)
        count += 1
        if count > limits.entries or name_len > limits.path_bytes:
            raise AnalysisError("Archive has too many entries or an oversized path.", "archive_limit", 413)
        step = 46 + name_len + extra_len + comment_len
        consumed += step
        if consumed > cd_size:
            raise AnalysisError("ZIP central directory is malformed.")
        stream.seek(step - 46, 1)
    if count != total:
        raise AnalysisError("ZIP entry count does not match its directory.")
    stream.seek(0)


def _safe_path(info: zipfile.ZipInfo, limits: Limits) -> PurePosixPath:
    name = info.orig_filename
    parts = name.rstrip("/").split("/")
    if (not name or name.startswith("/") or "\\" in name or ":" in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or any(p in {"", ".", ".."} for p in parts)):
        raise AnalysisError("Archive contains an unsafe path.", "unsafe_archive")
    if len(parts) > limits.depth or len(name.encode("utf-8")) > limits.path_bytes:
        raise AnalysisError("Archive paths exceed the depth or length limit.", "archive_limit", 413)
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise AnalysisError("Links and special files are not allowed.", "unsafe_archive")
    if kind == stat.S_IFDIR and not info.is_dir():
        raise AnalysisError("Archive has inconsistent directory metadata.")
    if info.flag_bits & 1:
        raise AnalysisError("Encrypted ZIP files are unsupported.")
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise AnalysisError("Use a ZIP archive with stored or deflate compression.")
    if info.file_size > limits.file_bytes:
        raise AnalysisError("An archive entry exceeds the 2 MiB file limit.", "archive_limit", 413)
    if info.file_size > max(1, info.compress_size) * limits.compression_ratio:
        raise AnalysisError("Archive exceeds the safe compression ratio.", "archive_limit", 413)
    if info.is_dir() and info.file_size:
        raise AnalysisError("Directory entries cannot contain file data.")
    return PurePosixPath(*parts)


def extract_repository(stream: BinaryIO, destination: Path, limits: Limits = LIMITS) -> dict:
    """Extract into a new private directory and report deliberately skipped files."""
    skipped: Counter[str] = Counter()
    try:
        _preflight(stream, limits)
        with zipfile.ZipFile(stream) as archive:
            entries = archive.infolist()
            if not entries:
                raise AnalysisError("The ZIP archive is empty.", "empty_repository", 422)
            paths: dict[str, bool] = {}
            validated = []
            expanded = 0
            for info in entries:
                path = _safe_path(info, limits)
                key = str(path).casefold()
                if key in paths:
                    raise AnalysisError("Duplicate or case-colliding archive paths are not allowed.", "unsafe_archive")
                paths[key] = info.is_dir()
                expanded += info.file_size
                if expanded > limits.expanded_bytes:
                    raise AnalysisError("Archive expands beyond 100 MiB.", "archive_limit", 413)
                validated.append((info, path))
            for _, path in validated:
                if any(paths.get(str(parent).casefold()) is False for parent in path.parents
                       if str(parent) != "."):
                    raise AnalysisError("Archive contains conflicting file and directory paths.", "unsafe_archive")
            # Recognize virtual environments even when their folder has a custom name.
            venv_roots = {path.parent for _, path in validated if path.name.lower() == "pyvenv.cfg"}
            total_written = 0
            for info, path in validated:
                reason = exclusion_reason(path, info.is_dir())
                if any(root == path or root in path.parents for root in venv_roots):
                    reason = "excluded_directory"
                if reason:
                    if not info.is_dir():
                        skipped[reason] += 1
                    continue
                target = destination.joinpath(*path.parts)
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise AnalysisError("Archive path escapes the extraction directory.", "unsafe_archive")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with archive.open(info) as source, target.open("xb") as output:
                    while chunk := source.read(64 * 1024):
                        written += len(chunk)
                        total_written += len(chunk)
                        if written > limits.file_bytes or total_written > limits.expanded_bytes:
                            raise AnalysisError("Expanded archive data exceeds safety limits.", "archive_limit", 413)
                        output.write(chunk)
                if written != info.file_size:
                    raise AnalysisError("ZIP entry size does not match its contents.")
            return {"archive_entries": len(entries), "skipped": dict(skipped)}
    except AnalysisError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, NotImplementedError,
            EOFError, UnicodeError, ValueError, zlib.error, struct.error) as exc:
        raise AnalysisError("The ZIP is corrupt or uses an unsupported format.") from exc

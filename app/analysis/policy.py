from pathlib import PurePosixPath


EXCLUDED_DIRECTORIES = frozenset({
    ".git", ".hg", ".svn", "node_modules", "bower_components", ".venv", "venv",
    "env", "virtualenv", "site-packages", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".cache", ".tox", ".nox", "dist", "build",
    "target", "coverage", ".next", ".nuxt", ".output", ".idea", ".vscode",
    "__macosx", "vendor", ".eggs",
})
BINARY_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tiff",
    ".pdf", ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".wav",
    ".ogg", ".mov", ".avi", ".exe", ".dll", ".so", ".dylib", ".o", ".a",
    ".class", ".jar", ".pyc", ".pyo", ".zip", ".gz", ".bz2", ".xz", ".7z",
    ".tar", ".rar", ".sqlite", ".sqlite3", ".db", ".bin", ".wasm", ".lockb",
})


def exclusion_reason(path: PurePosixPath, is_directory: bool = False) -> str | None:
    directories = path.parts if is_directory else path.parts[:-1]
    if any(part.lower() in EXCLUDED_DIRECTORIES or part.lower().endswith(".egg-info")
           for part in directories):
        return "excluded_directory"
    if path.name.lower() in {".ds_store", "pyvenv.cfg"}:
        return "metadata"
    if path.suffix.lower() in BINARY_SUFFIXES:
        return "binary_or_archive"
    return None

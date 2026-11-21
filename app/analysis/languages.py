from pathlib import Path


LANGUAGES = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".cjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".md": "Markdown", ".rst": "reStructuredText", ".txt": "Text",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".go": "Go",
    ".rs": "Rust", ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++",
    ".cc": "C++", ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".sql": "SQL",
    ".xml": "XML", ".svg": "XML", ".vue": "Vue", ".svelte": "Svelte",
    ".r": "R", ".dart": "Dart", ".lua": "Lua", ".ex": "Elixir", ".exs": "Elixir",
    ".ipynb": "Jupyter Notebook", ".ini": "INI", ".cfg": "Configuration",
}
NON_SOURCE = {"JSON", "YAML", "TOML", "Markdown", "reStructuredText", "Text", "XML",
              "INI", "Configuration", "Jupyter Notebook", "Other text"}


def identify(path: Path) -> tuple[str, bool]:
    name = path.name.lower()
    if name == "dockerfile":
        return "Dockerfile", True
    if name in {"makefile", "gnumakefile"}:
        return "Makefile", True
    language = LANGUAGES.get(path.suffix.lower(), "Other text")
    return language, language not in NON_SOURCE

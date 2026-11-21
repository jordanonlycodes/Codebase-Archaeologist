"""Physical line metrics. Never import, compile, or execute repository content."""

import io
import json
import tokenize


def measure(text: str, language: str) -> dict:
    # Universal newlines keep token positions and physical line totals aligned.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n") if text else []
    if text.endswith("\n"):
        lines.pop()
    blank = sum(not line.strip() for line in lines)
    comments: int | None = None
    if language == "Python":
        try:
            comment_rows = set()
            code_rows = set()
            ignored = {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE,
                       tokenize.NL, tokenize.INDENT, tokenize.DEDENT}
            for token in tokenize.generate_tokens(io.StringIO(text).readline):
                if token.type == tokenize.ERRORTOKEN and token.string.strip():
                    raise tokenize.TokenError("Invalid token")
                if token.type == tokenize.COMMENT:
                    comment_rows.add(token.start[0])
                elif token.type not in ignored:
                    code_rows.update(range(token.start[0], token.end[0] + 1))
            comments = len(comment_rows - code_rows)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass  # Broken syntax must not turn a partial count into a claimed total.
    elif language == "JSON":
        try:
            json.loads(text)
            comments = 0  # Only valid standard JSON can claim no comments.
        except (ValueError, RecursionError):
            pass
    return {
        "lines": len(lines), "blank_lines": blank,
        "nonblank_lines": len(lines) - blank, "comment_lines": comments,
        "code_lines": len(lines) - blank - comments if comments is not None else None,
    }

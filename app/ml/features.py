"""Shared, deterministic C-function features for training and future inference.

Only source text is accepted. Labels, IDs, projects and commit metadata never
enter this module. Tree-sitter dependencies are loaded lazily for Task 1 users.
"""

from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import version
import math

FEATURE_VERSION = "c-function-v1"
MAX_FUNCTION_BYTES = 2 * 1024 * 1024
FEATURE_DESCRIPTIONS = {
    "physical_lines": "Physical lines after universal-newline normalization and outer whitespace trimming.",
    "nonblank_lines": "Physical lines containing non-whitespace characters.",
    "function_bytes": "UTF-8 byte length of the normalized function snippet.",
    "parameter_count": "Declared parameters of the function; void and variadic ellipsis excluded.",
    "conditional_count": "if statements, switch statements and ternary expressions.",
    "loop_count": "for, while and do statements.",
    "return_count": "return statements.",
    "max_nesting_depth": "Maximum nested if/switch/loop/ternary nodes; else-if adds a level.",
    "decision_complexity": "1 + if + loops + non-default case labels + ternaries + logical &&/|| operators.",
    "pointer_syntax_count": "Pointer declarators, unary address/dereference expressions, and -> member accesses.",
    "call_count": "Call-expression syntax nodes; macros resembling calls may be included.",
}
FEATURE_NAMES = tuple(FEATURE_DESCRIPTIONS)
STRUCTURAL_NAMES = FEATURE_NAMES[3:]
CONTROLS = {"if_statement", "switch_statement", "for_statement", "while_statement", "do_statement", "conditional_expression"}
LOOPS = {"for_statement", "while_statement", "do_statement"}


def normalize_source(source: str) -> str:
    return source.replace("\r\n", "\n").replace("\r", "\n").strip()


@lru_cache(maxsize=1)
def _language():
    try:
        from tree_sitter import Language
        import tree_sitter_c
    except ImportError as exc:
        raise RuntimeError("C features require: pip install -r requirements-ml.txt") from exc
    return Language(tree_sitter_c.language())


def feature_schema() -> dict:
    return {
        "version": FEATURE_VERSION, "names": list(FEATURE_NAMES), "dtype": "float64",
        "features": [{"name": name, "description": FEATURE_DESCRIPTIONS[name]} for name in FEATURE_NAMES],
        "missing_values": "NaN; fit median imputation on training rows only, retaining all-empty columns.",
        "parser": {"tree-sitter": version("tree-sitter"), "tree-sitter-c": version("tree-sitter-c")},
        "parsing_policy": "Exactly one function definition and no Tree-sitter errors; otherwise structural values are unavailable. Lexical values remain available for nonempty text.",
        "excluded_inputs": ["target", "project", "commit_id", "id"],
    }


@dataclass(frozen=True)
class FunctionFeatures:
    values: tuple[float, ...]
    parse_status: str

    def as_dict(self) -> dict[str, float | None]:
        return {name: None if math.isnan(value) else value for name, value in zip(FEATURE_NAMES, self.values)}


def _walk(node):
    stack = [(node, 0)]
    while stack:
        current, depth = stack.pop()
        depth += current.type in CONTROLS
        yield current, depth
        stack.extend((child, depth) for child in reversed(current.named_children))


def _parameters(function) -> int:
    declarator = function.child_by_field_name("declarator")
    parameters = None
    while declarator is not None:
        if declarator.type == "function_declarator":
            parameters = declarator.child_by_field_name("parameters")
        declarator = declarator.child_by_field_name("declarator")
    if parameters is None:
        return 0
    params = [child for child in parameters.named_children
              if child.type in {"parameter_declaration", "identifier"}]
    if len(params) == 1 and params[0].text.strip() == b"void":
        return 0
    return len(params)


def extract_features(source: object) -> FunctionFeatures:
    values = {name: math.nan for name in FEATURE_NAMES}

    def result(status):
        return FunctionFeatures(tuple(float(values[name]) for name in FEATURE_NAMES), status)

    if not isinstance(source, str) or not source.strip():
        return result("missing_or_invalid_input")
    source = normalize_source(source)
    try:
        data = source.encode("utf-8")
    except UnicodeEncodeError:
        return result("invalid_unicode")
    if len(data) > MAX_FUNCTION_BYTES or "\x00" in source:
        return result("unsupported_input")
    lines = source.split("\n")
    values.update(physical_lines=len(lines), nonblank_lines=sum(bool(line.strip()) for line in lines), function_bytes=len(data))
    from tree_sitter import Parser
    tree = Parser(_language()).parse(data)
    root = tree.root_node
    if root.has_error:
        return result("parse_error")
    functions = [node for node, _ in _walk(root) if node.type == "function_definition"]
    if len(functions) != 1:
        return result("expected_one_function")
    function = functions[0]
    values.update({name: 0 for name in STRUCTURAL_NAMES})
    values["parameter_count"] = _parameters(function)
    values["decision_complexity"] = 1
    for node, depth in _walk(function):
        kind = node.type
        values["max_nesting_depth"] = max(values["max_nesting_depth"], depth)
        if kind in {"if_statement", "switch_statement", "conditional_expression"}:
            values["conditional_count"] += 1
        if kind in LOOPS:
            values["loop_count"] += 1
        if kind == "return_statement":
            values["return_count"] += 1
        if kind in LOOPS | {"if_statement", "conditional_expression"}:
            values["decision_complexity"] += 1
        if kind == "case_statement" and node.child_by_field_name("value") is not None:
            values["decision_complexity"] += 1
        operator = node.child_by_field_name("operator")
        if kind == "binary_expression" and operator is not None and operator.text in {b"&&", b"||"}:
            values["decision_complexity"] += 1
        if kind in {"pointer_declarator", "abstract_pointer_declarator", "pointer_expression"}:
            values["pointer_syntax_count"] += 1
        if kind == "field_expression" and operator is not None and operator.text == b"->":
            values["pointer_syntax_count"] += 1
        if kind == "call_expression":
            values["call_count"] += 1
    return result("ok")


def feature_matrix(functions):
    """The single numerical conversion path used by training and inference."""
    import numpy as np
    extracted = [extract_features(source) for source in functions]
    matrix = np.array([item.values for item in extracted], dtype=np.float64).reshape(-1, len(FEATURE_NAMES))
    return matrix, [item.parse_status for item in extracted]

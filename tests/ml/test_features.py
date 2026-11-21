import math

import pytest

pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_c")
np = pytest.importorskip("numpy")

from app.ml.features import FEATURE_NAMES, extract_features, feature_matrix, feature_schema


def test_known_c_syntax_counts():
    source = """int f(int *p, int n) {
    if (p && n) {
        for (int i=0; i<n; i++) {
            *p += g(i);
        }
    }
    return *p;
}"""
    result = extract_features(source)
    assert result.parse_status == "ok"
    assert result.as_dict() == {
        "physical_lines": 8.0, "nonblank_lines": 8.0, "function_bytes": float(len(source.encode())),
        "parameter_count": 2.0, "conditional_count": 1.0, "loop_count": 1.0,
        "return_count": 1.0, "max_nesting_depth": 2.0, "decision_complexity": 4.0,
        "pointer_syntax_count": 3.0, "call_count": 1.0,
    }


def test_comments_strings_and_multiplication_do_not_count_as_syntax():
    source = 'int f(void) { /* if(x) while(y) *p */ const char *s="if && return call()"; return 2 * 3; }'
    metrics = extract_features(source).as_dict()
    assert metrics["conditional_count"] == metrics["loop_count"] == metrics["call_count"] == 0
    assert metrics["parameter_count"] == 0
    assert metrics["pointer_syntax_count"] == 1
    assert metrics["decision_complexity"] == 1


@pytest.mark.parametrize("value", [None, "", "  \n", 42, {}, b"int f(void){}"])
def test_invalid_input_has_no_fabricated_zero_counts(value):
    result = extract_features(value)
    assert result.parse_status == "missing_or_invalid_input"
    assert all(math.isnan(value) for value in result.values)


@pytest.mark.parametrize("source,status", [
    ("int f( {", "parse_error"),
    ("int x;", "expected_one_function"),
    ("int f(void) {} int g(void) {}", "expected_one_function"),
    ("int f(void) { return 1;", "parse_error"),
])
def test_parse_failure_retains_only_lexical_features(source, status):
    result = extract_features(source)
    assert result.parse_status == status
    assert all(math.isfinite(value) for value in result.values[:3])
    assert all(math.isnan(value) for value in result.values[3:])


def test_newline_normalization_and_determinism():
    source = "int f(void) {\n\n return 1;\n}\n"
    assert extract_features(source) == extract_features(source.replace("\n", "\r\n"))
    assert extract_features(source) == extract_features(source)
    assert extract_features(source).as_dict()["nonblank_lines"] == 3


def test_feature_order_is_shared_and_excludes_metadata():
    source = "int f(int x) { return x; }"
    matrix, statuses = feature_matrix([source])
    assert statuses == ["ok"]
    np.testing.assert_array_equal(matrix[0], extract_features(source).values)
    assert list(extract_features(source).as_dict()) == list(FEATURE_NAMES) == feature_schema()["names"]
    assert not set(FEATURE_NAMES) & {"target", "project", "commit_id", "id"}


def test_switch_ternary_and_pointer_member():
    metrics = extract_features("int f(struct S *p, int n) { switch(n) { case 1: return p->x ? 2 : 3; default: return 0; } }").as_dict()
    assert metrics["conditional_count"] == 2
    assert metrics["decision_complexity"] == 3
    assert metrics["pointer_syntax_count"] == 2


def test_function_pointer_parameter_and_void():
    assert extract_features("int f(int (*callback)(int), int x) { return callback(x); }").as_dict()["parameter_count"] == 2
    assert extract_features("int f(void) { return 0; }").as_dict()["parameter_count"] == 0


def test_empty_matrix_and_input_size_limit():
    matrix, statuses = feature_matrix([])
    assert matrix.shape == (0, len(FEATURE_NAMES)) and statuses == []
    assert extract_features("a" * (2 * 1024 * 1024 + 1)).parse_status == "unsupported_input"
    assert extract_features("\x00").parse_status == "unsupported_input"

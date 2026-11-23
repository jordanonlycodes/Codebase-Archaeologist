"""Experimental AST additions, isolated from the immutable production v1 schema."""
import math
from collections import Counter
from app.ml.features import (FEATURE_NAMES, extract_features, normalize_source, _language, _walk)

VERSION = 'c-function-v2-experimental'
EXTRA = ('ast_leaf_tokens','identifier_occurrences','unique_identifiers','array_subscripts',
         'assignments','comparisons','arithmetic_operators','local_declarations',
         'comment_fraction','tokens_per_nonblank_line','decisions_per_nonblank_line')
NAMES = FEATURE_NAMES + EXTRA


def extract(source):
    """Single source-only callable for cached fitting and candidate-inference parity."""
    base = extract_features(source)
    if base.parse_status != 'ok':
        return base.values + (math.nan,) * len(EXTRA)
    from tree_sitter import Parser
    data = normalize_source(source).encode('utf-8')
    root = Parser(_language()).parse(data).root_node
    function = next(n for n,_ in _walk(root) if n.type == 'function_definition')
    counts = Counter(); identifiers = set(); comment_bytes = 0
    stack = [function]
    while stack:
        n = stack.pop()
        if n.type == 'comment':
            comment_bytes += n.end_byte-n.start_byte
            continue
        stack.extend(reversed(n.children))
        if not n.children: counts['ast_leaf_tokens'] += 1
        if n.type in {'identifier','field_identifier','type_identifier'}:
            counts['identifier_occurrences'] += 1;identifiers.add(n.text)
        if n.type == 'subscript_expression': counts['array_subscripts'] += 1
        if n.type == 'assignment_expression': counts['assignments'] += 1
        if n.type == 'declaration': counts['local_declarations'] += 1
        operator = n.child_by_field_name('operator')
        op = operator.text if operator else None
        if n.type == 'binary_expression' and op in {b'==',b'!=',b'<',b'>',b'<=',b'>='}:
            counts['comparisons'] += 1
        if ((n.type == 'binary_expression' and op in {b'+',b'-',b'*',b'/',b'%'}) or
            (n.type in {'unary_expression','update_expression'} and op in {b'+',b'-',b'++',b'--'})):
            counts['arithmetic_operators'] += 1
    counts['unique_identifiers'] = len(identifiers)
    counts['comment_fraction'] = comment_bytes / len(data)
    counts['tokens_per_nonblank_line'] = counts['ast_leaf_tokens'] / base.values[1]
    counts['decisions_per_nonblank_line'] = base.values[8] / base.values[1]
    return base.values + tuple(float(counts[k]) for k in EXTRA)


def schema():
    return {'version':VERSION,'names':list(NAMES),'base_version':'c-function-v1',
            'missing':'Unavailable AST additions are NaN; training-fold-only median imputation.',
            'scope':'C functions only. Source-only AST counts/densities, not semantic defect indicators.'}

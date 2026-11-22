"""Bounded AST metrics. No imports or execution of analyzed source."""
import ast
from dataclasses import dataclass
from app.ml.features import _language, _parameters


class WorkLimit(Exception):
    pass


@dataclass
class Budget:
    maximum: int
    used: int = 0

    def visit(self):
        self.used += 1
        if self.used > self.maximum:
            raise WorkLimit


def parse_c(data):
    from tree_sitter import Parser
    return Parser(_language()).parse(data).root_node


def c_name(node):
    declarator = node.child_by_field_name('declarator')
    while declarator is not None:
        if declarator.type == 'identifier':
            return declarator.text.decode('utf-8')
        declarator = declarator.child_by_field_name('declarator')
    return None


def c_definitions(root, budget):
    stack = [root]
    while stack:
        node = stack.pop()
        budget.visit()
        if node.type == 'function_definition':
            yield node, c_name(node), None
        else:
            stack.extend(reversed(node.named_children))


def python_definitions(root, budget):
    """Discover nested functions/methods, retaining lexical class/function scope."""
    stack = [(root, ())]
    while stack:
        node, scope = stack.pop()
        budget.visit()
        nested_scope = scope
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nested_scope = (*scope, node.name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield node, node.name, '.'.join(nested_scope)
        stack.extend((child, nested_scope) for child in reversed(list(ast.iter_child_nodes(node))))


def c_metrics(function, budget):
    controls = {'if_statement', 'switch_statement', 'for_statement', 'while_statement', 'do_statement', 'conditional_expression'}
    loops = {'for_statement', 'while_statement', 'do_statement'}
    decisions = count_loops = conditionals = nesting = 0
    # Declarations/attributes/parameters are outside the executable function body.
    body = function.child_by_field_name('body')
    stack = [(body, 0)] if body is not None else []
    while stack:
        node, depth = stack.pop()
        budget.visit()
        if node.type == 'function_definition':
            continue
        kind = node.type
        depth += kind in controls
        nesting = max(nesting, depth)
        count_loops += kind in loops
        conditionals += kind in {'if_statement', 'switch_statement', 'conditional_expression'}
        decisions += kind in loops | {'if_statement', 'conditional_expression'}
        if kind == 'case_statement' and node.child_by_field_name('value') is not None:
            decisions += 1
        operator = node.child_by_field_name('operator')
        if kind == 'binary_expression' and operator is not None and operator.text in {b'&&', b'||'}:
            decisions += 1
        stack.extend((child, depth) for child in reversed(node.named_children))
    return dict(parameter_count=_parameters(function), cyclomatic_complexity=decisions+1,
                decision_points=decisions, loop_count=count_loops, conditional_count=conditionals,
                max_nesting_depth=nesting)


def python_metrics(function, budget):
    decisions = loops = conditionals = nesting = 0
    controls = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.With, ast.AsyncWith,
                ast.Try, ast.ExceptHandler, ast.Match)
    if hasattr(ast, 'TryStar'):
        controls += (ast.TryStar,)
    stack = [(node, 0) for node in reversed(function.body)]
    while stack:
        node, depth = stack.pop()
        budget.visit()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue  # Nested code objects have their own scope, including defaults/decorators.
        depth += isinstance(node, controls)
        nesting = max(nesting, depth)
        if isinstance(node, (ast.If, ast.IfExp)):
            decisions += 1
            conditionals += 1
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            decisions += 1
            loops += 1
        if isinstance(node, ast.BoolOp):
            decisions += len(node.values)-1
        if isinstance(node, ast.ExceptHandler):
            decisions += 1
        if isinstance(node, ast.match_case):
            # Plain capture/wildcard is irrefutable; guarded cases can fail.
            irrefutable = isinstance(node.pattern, ast.MatchAs) and node.pattern.pattern is None
            decisions += int(not irrefutable or node.guard is not None)
            conditionals += 1
        # Comprehensions add one loop per generator and one branch per filter.
        # Their nesting is not statement/control nesting; document this boundary.
        if isinstance(node, ast.comprehension):
            decisions += 1 + len(node.ifs)
            loops += 1
            conditionals += len(node.ifs)
        stack.extend((child, depth) for child in reversed(list(ast.iter_child_nodes(node))))
    args = function.args
    parameters = len(args.posonlyargs)+len(args.args)+len(args.kwonlyargs)+int(args.vararg is not None)+int(args.kwarg is not None)
    return dict(parameter_count=parameters, cyclomatic_complexity=decisions+1, decision_points=decisions,
                loop_count=loops, conditional_count=conditionals, max_nesting_depth=nesting)

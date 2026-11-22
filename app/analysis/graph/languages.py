"""Bounded AST evidence extraction. Function identities come from structural records."""
import ast
from dataclasses import dataclass, field

from app.analysis.structural_parsers import c_name
from .models import Evidence


@dataclass
class RawReference:
    source: str
    kind: str
    name: str
    evidence: Evidence
    scope: int = 0
    mode: str = ''
    module: str = ''
    symbol: str = ''
    level: int = 0


@dataclass
class Scope:
    parent: int | None
    kind: str
    bindings: dict = field(default_factory=dict)
    wildcard: bool = False

    def bind(self, name, value):
        self.bindings.setdefault(name, []).append(value)


@dataclass
class Facts:
    path: str
    language: str
    references: list = field(default_factory=list)
    scopes: list = field(default_factory=lambda:[Scope(None, 'module')])
    definitions: dict = field(default_factory=dict)
    static: set = field(default_factory=set)
    declarations: set = field(default_factory=set)
    static_declarations: set = field(default_factory=set)
    shadowed: dict = field(default_factory=dict)
    macros: set = field(default_factory=set)


def expression(node):
    """Only name/attribute chains; never unparse arbitrary, potentially huge ASTs."""
    parts = []
    while isinstance(node, ast.Attribute) and len(parts) < 16:
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        return '.'.join([node.id, *reversed(parts)])
    return '<dynamic expression>'


def python_facts(path, tree, functions, file_id, visit, emit):
    facts = Facts(path, 'Python')
    records = {(f.start_line,f.start_column):f for f in functions if f.status == 'analyzed'}
    stack = [(tree, 0, file_id, False)]
    while stack:
        node, scope_id, owner, conditional = stack.pop()
        visit()
        scope = facts.scopes[scope_id]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            function = records.get((node.lineno,node.col_offset)) if not isinstance(node,ast.ClassDef) else None
            usable = function is not None and not node.decorator_list and not conditional
            scope.bind(node.name, ('function',function.id) if usable else ('dynamic',))
            # Methods do not inherit class namespace as a lexical function scope.
            parent = scope.parent if scope.kind == 'class' else scope_id
            new = Scope(parent, 'class' if isinstance(node,ast.ClassDef) else 'function')
            facts.scopes.append(new)
            child_id = len(facts.scopes)-1
            if hasattr(node,'args'):
                args = node.args
                for arg in [*args.posonlyargs,*args.args,*args.kwonlyargs,args.vararg,args.kwarg]:
                    if arg is not None:
                        new.bind(arg.arg, ('dynamic',))
            # Defaults, annotations, decorators and class bases are definition-time
            # expressions, not function-body calls. They are explicitly outside coverage.
            if not isinstance(node, ast.ClassDef) and function is None:
                continue
            child_owner = function.id if function else owner
            stack.extend((child,child_id,child_owner,False) for child in reversed(node.body))
            continue
        if isinstance(node, ast.Lambda):
            continue
        if isinstance(node, (ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp)):
            # Comprehension variables have an implicit scope. Conservatively block
            # call resolution there instead of leaking their bindings into the parent.
            child = Scope(scope_id, 'comprehension', wildcard=True)
            facts.scopes.append(child)
            scope_id = len(facts.scopes)-1
            scope = child
        if isinstance(node,ast.NamedExpr) and isinstance(node.target,ast.Name):
            binding_scope = scope_id
            while facts.scopes[binding_scope].kind == 'comprehension':
                binding_scope = facts.scopes[binding_scope].parent
            if binding_scope != scope_id:
                facts.scopes[binding_scope].bind(node.target.id,('dynamic',))
        if isinstance(node,(ast.Global,ast.Nonlocal)):
            for name in node.names:
                scope.bind(name,('dynamic',))
        if isinstance(node, ast.Name) and isinstance(node.ctx,(ast.Store,ast.Del)):
            scope.bind(node.id, ('dynamic',))
        if isinstance(node,ast.Attribute) and isinstance(node.ctx,(ast.Store,ast.Del)):
            scope.bind(expression(node).split('.')[0],('dynamic',))
        if isinstance(node,ast.ExceptHandler) and node.name:
            scope.bind(node.name,('dynamic',))
        if isinstance(node,(ast.MatchAs,ast.MatchStar)) and node.name:
            scope.bind(node.name,('dynamic',))
        if isinstance(node,ast.MatchMapping) and node.rest:
            scope.bind(node.rest,('dynamic',))
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            for alias in node.names:
                module = alias.name if isinstance(node,ast.Import) else node.module or ''
                symbol = '' if isinstance(node,ast.Import) else alias.name
                level = getattr(node,'level',0)
                ref = RawReference(file_id,'IMPORTS',('.'*level)+module+(':'+symbol if symbol else ''),
                                   Evidence(path,node.lineno,node.col_offset),scope_id,'import',module,symbol,level)
                emit(facts,ref)
                if alias.name == '*':
                    scope.wildcard = True
                else:
                    bound = alias.asname or alias.name.split('.')[0]
                    # import pkg.sub binds pkg, not pkg.sub, unless aliased.
                    binding_module = module if alias.asname or symbol else module.split('.')[0]
                    scope.bind(bound,('dynamic',) if conditional else ('import',binding_module,symbol,level))
        if isinstance(node,ast.Call):
            name = expression(node.func)
            if name in {'exec', 'eval', 'globals', 'locals', 'setattr', 'delattr'}:
                scope.wildcard = True
            emit(facts, RawReference(owner,'CALLS',name,Evidence(path,node.lineno,node.col_offset),scope_id))
            if name in {'__import__','importlib.import_module'} or name.endswith('.import_module'):
                emit(facts,RawReference(file_id,'IMPORTS',name,Evidence(path,node.lineno,node.col_offset),scope_id,'dynamic'))
        is_conditional = conditional or isinstance(node,(ast.If,ast.For,ast.AsyncFor,ast.While,ast.Try,ast.Match,ast.With,ast.AsyncWith))
        is_conditional |= hasattr(ast,'TryStar') and isinstance(node,ast.TryStar)
        stack.extend((child,scope_id,owner,is_conditional) for child in reversed(list(ast.iter_child_nodes(node))))
    return facts


def c_facts(path, tree, functions, file_id, visit, emit):
    facts = Facts(path, 'C')
    records = {(f.start_line,f.start_column):f for f in functions if f.status=='analyzed'}
    stack = [(tree,None)]
    while stack:
        node, owner = stack.pop()
        visit()
        if node.type == 'function_definition':
            f = records.get((node.start_point.row+1,node.start_point.column))
            if f is None:
                continue
            owner = f.id
            facts.definitions.setdefault(f.name,[]).append(f.id)
            if any(n.type=='storage_class_specifier' and n.text==b'static' for n in node.named_children):
                facts.static.add(f.id)
            facts.shadowed[owner] = set()
        if node.type in {'preproc_def','preproc_function_def'}:
            name = node.child_by_field_name('name')
            if name is not None:
                facts.macros.add(name.text.decode('utf-8'))
        if node.type in {'declaration','parameter_declaration'}:
            # Declarator identifiers are bindings; don't confuse initializer calls
            # or type identifiers with the name being declared.
            for child in node.named_children:
                if child.type in {'primitive_type','type_identifier','storage_class_specifier','type_qualifier'}:
                    continue
                decl = child.child_by_field_name('declarator') if child.type=='init_declarator' else child
                is_function = (decl is not None and decl.type == 'function_declarator'
                               and decl.child_by_field_name('declarator') is not None
                               and decl.child_by_field_name('declarator').type == 'identifier')
                while decl is not None and decl.type != 'identifier':
                    decl = (decl.named_children[0] if decl.type == 'parenthesized_declarator' and decl.named_children
                            else decl.child_by_field_name('declarator'))
                if decl is not None:
                    name = decl.text.decode('utf-8')
                    if owner:
                        facts.shadowed[owner].add(name)
                    elif is_function:
                        facts.declarations.add(name)
                        if any(n.type=='storage_class_specifier' and n.text==b'static' for n in node.named_children):
                            facts.static_declarations.add(name)
                    else:
                        facts.macros.add(name)  # file-scope object may be a callback
        if node.type == 'preproc_include':
            value = node.child_by_field_name('path')
            name = value.text.decode('utf-8') if value is not None else '<macro include>'
            mode = 'quoted' if value is not None and value.type=='string_literal' else 'angle' if value is not None and value.type=='system_lib_string' else 'dynamic'
            emit(facts,RawReference(file_id,'INCLUDES',name.strip('"<>'),Evidence(path,node.start_point.row+1,node.start_point.column),mode=mode))
        if node.type == 'call_expression' and owner:
            target = node.child_by_field_name('function')
            direct = target is not None and target.type == 'identifier'
            name = ((target.text if direct else target.text[:256]).decode('utf-8',errors='replace')
                    if target is not None else '<dynamic expression>')
            emit(facts,RawReference(owner,'CALLS',name,Evidence(path,node.start_point.row+1,node.start_point.column),mode='direct' if direct else 'dynamic'))
        stack.extend((child,owner) for child in reversed(node.named_children))
    return facts

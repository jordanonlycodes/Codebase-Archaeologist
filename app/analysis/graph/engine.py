"""One graph for hierarchy, calls and dependencies, shared by both ingestion paths."""
import ast
from dataclasses import asdict
from pathlib import PurePosixPath

from app.config import GRAPH_LIMITS
from app.analysis.structural import identity
from app.analysis.structural_parsers import Budget, WorkLimit, parse_c
from .builder import Builder, graph_id
from .models import Node
from .languages import python_facts, c_facts
from .resolution import Symbols


def extract_graph(root, result, *, parsed_files=None, limits=GRAPH_LIMITS):
    builder = Builder(limits)
    structure = result.structural
    parsed_files = parsed_files if parsed_files is not None else {}
    files = sorted(result.files,key=lambda f:f.path)
    structures = {f.path:f for f in structure.files} if structure else {}
    functions = sorted((f for f in structure.functions if f.status=='analyzed'),
                       key=lambda f:(f.path,f.start_line,f.start_column,f.id)) if structure else []
    if len(functions)>limits.symbols:
        builder.issue('symbol_limit',True)
        functions = functions[:limits.symbols]
    by_file = {}
    for function in functions:
        by_file.setdefault(function.path,[]).append(function)
    hotspot = {h.function_id:asdict(h)['reasons'] for h in structure.hotspots} if structure else {}
    # Identity does not depend on ZIP name, provenance, timestamp or temp path.
    repository_id = graph_id('repository', [f.path for f in files])
    builder.node(Node(repository_id,'repository',result.repository,metadata={
        'source':asdict(result.source) if result.source else None,
        'identity_scope':'snapshot-local inventory; not a content digest'}))
    for file in files:
        parent_id = repository_id
        parts = PurePosixPath(file.path).parts
        for depth in range(1,len(parts)):
            directory = '/'.join(parts[:depth])
            directory_id = graph_id('directory',directory)
            if directory_id not in builder.nodes:
                builder.node(Node(directory_id,'directory',parts[depth-1],directory))
                builder.edge(parent_id,directory_id,'CONTAINS')
            parent_id = directory_id
        record = structures.get(file.path)
        file_id = record.id if record else identity('file',file.path)
        metadata = asdict(file)
        if record:
            metadata['structural'] = asdict(record)
        builder.node(Node(file_id,'file',parts[-1],file.path,metadata))
        builder.edge(parent_id,file_id,'CONTAINS')
        for function in by_file.get(file.path,()):
            data = asdict(function)
            data['hotspots'] = hotspot.get(function.id,[])
            if function.language=='C' and function.ml_result_index is not None and result.defect_risk:
                prediction = result.defect_risk.functions[function.ml_result_index]
                data['ml'] = {key:getattr(prediction,key) for key in ('status','predicted_class','model_probability')}
            builder.node(Node(function.id,'function',function.qualified_name or function.name or '<unnamed>',file.path,data))
            builder.edge(file_id,function.id,'DEFINES')
    facts = {}
    for file in files:
        suffix = PurePosixPath(file.path).suffix
        if suffix not in {'.c','.h','.py','.pyi'}:
            builder.coverage.unsupported_source_files += int(file.is_source)
            continue
        builder.coverage.eligible_files += 1
        if (file.bytes>limits.file_bytes or builder.coverage.source_bytes+file.bytes>limits.total_bytes
                or builder.coverage.visited_nodes>=limits.traversal_nodes):
            builder.coverage.skipped_files += 1
            builder.issue('source_or_work_limit',True)
            continue
        budget = Budget(min(limits.nodes_per_file,limits.traversal_nodes-builder.coverage.visited_nodes))
        try:
            cached = parsed_files.get(file.path)
            if cached is not None:
                data,tree = cached
            else:
                path = root/file.path
                if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError
                with path.open('rb') as stream:
                    data = stream.read(limits.file_bytes+1)
                text = data.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
                data = text.encode('utf-8')
            if len(data)>limits.file_bytes or builder.coverage.source_bytes+len(data)>limits.total_bytes:
                raise WorkLimit
            builder.coverage.source_bytes += len(data)
            if cached is None:
                tree = ast.parse(text) if suffix in {'.py','.pyi'} else parse_c(data)
            if suffix in {'.c','.h'} and tree.has_error:
                builder.issue('parse_error')
                builder.coverage.skipped_files += 1
                continue
            def emit(fact, ref):
                if builder.coverage.observed_references >= limits.references:
                    raise WorkLimit
                builder.coverage.observed_references += 1
                if len(ref.name)>limits.reference_chars:
                    ref.name = ref.name[:limits.reference_chars]
                    ref.mode = 'dynamic'
                    builder.issue('reference_length_limit',True)
                fact.references.append(ref)
            collector = python_facts if suffix in {'.py','.pyi'} else c_facts
            collected = collector(file.path,tree,by_file.get(file.path,()),identity('file',file.path),budget.visit,emit)
            binding_count = (sum(len(entries) for scope in collected.scopes for entries in scope.bindings.values())
                             + sum(len(ids) for ids in collected.definitions.values())
                             + len(collected.declarations) + len(collected.macros)
                             + sum(len(names) for names in collected.shadowed.values()))
            if builder.coverage.retained_symbol_bindings+binding_count > limits.symbols:
                builder.issue('symbol_limit',True)
                raise WorkLimit
            builder.coverage.retained_symbol_bindings += binding_count
            facts[file.path] = collected
            builder.coverage.analyzed_files += 1
        except WorkLimit:
            builder.coverage.skipped_files += 1
            builder.issue('reference_or_work_limit',True)
        except (OSError,ValueError,SyntaxError,RecursionError,ImportError,RuntimeError):
            builder.coverage.skipped_files += 1
            builder.issue('parse_or_read_failed')
        finally:
            builder.coverage.visited_nodes += min(budget.used,budget.maximum)
    symbols = Symbols(facts,[f.path for f in files])
    # Directly included headers supply declarations; no unbounded transitive walks.
    for path,fact in sorted(facts.items()):
        declarations = set(fact.declarations)
        macros = set(fact.macros)
        static_declarations = set(fact.static_declarations)
        missing_header = False
        for ref in fact.references:
            if ref.kind == 'INCLUDES':
                target,status = symbols.include(path,ref.name,ref.mode)
                if target in facts:
                    declarations.update(facts[target].declarations)
                    macros.update(facts[target].macros)
                    static_declarations.update(facts[target].static_declarations)
                elif target is not None:
                    missing_header = True
        for ref in fact.references:
            reason = 'no_unique_supported_static_target'
            if ref.mode=='dynamic':
                target,status = None,'unsupported_dynamic'
            elif ref.kind=='INCLUDES':
                target,status = symbols.include(path,ref.name,ref.mode)
                target = identity('file',target) if target else None
            elif ref.kind=='IMPORTS':
                target,status = symbols.import_target(path,ref.module,ref.symbol,ref.level)
                target = identity('file',target) if target else None
            elif fact.language=='Python':
                target,status = symbols.python_call(fact,ref)
            else:
                target,status = ((None,'unsupported_dynamic') if missing_header else
                                 symbols.c_call(fact,ref,declarations,macros,static_declarations))
            if target is not None:
                builder.edge(ref.source,target,ref.kind,ref.name,ref.evidence)
            else:
                builder.reference(ref.source,ref.kind,ref.name,status,reason,ref.evidence)
    if structure and (structure.coverage.skipped_files or structure.coverage.partial_files or structure.coverage.truncated):
        builder.issue('structural_definitions_partial')
    return builder.finish()

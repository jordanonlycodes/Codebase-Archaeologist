"""Bounded deterministic aggregation of existing inventory, structure and graph only."""
from dataclasses import asdict
from pathlib import PurePosixPath

from app.config import ARCHITECTURE_LIMITS
from app.analysis.structural import identity
from app.analysis.graph.builder import graph_id
from .models import Metrics, HeatNode, Component, ComponentEdge, Coverage, Architecture

MEASUREMENTS = ('functions', 'max_complexity', 'total_complexity', 'hotspots', 'max_c_function_score')
DEFINITIONS = {
    'components': 'Direct-parent-directory groups of retained files; root files use the explicit (root files) group. Groups partition files, not inferred application layers.',
    'hierarchy': 'Heatmap directories aggregate all retained descendants; component metrics cover immediate member files only. Nested directory components do not overlap.',
    'edges': 'Directed, type-specific aggregates of retained resolved CALLS/IMPORTS/INCLUDES graph edges. Counts distinguish unique source edges, occurrences and aggregate edges. Same-component edges are counted separately.',
    'complexity': 'File/directory max_complexity is the maximum measured valid function complexity, never an average. total_complexity sums observed valid functions. Missing data stays null; measured_files reports coverage.',
    'functions': 'Counts valid analyzed structural function records. A completely analyzed empty file has zero; unsupported/unavailable files have null. Partial files may expose observed counts only.',
    'lines': 'physical_lines includes code, comments and blank lines from the existing inventory, for all retained text files. It is not executable LOC.',
    'hotspots': 'Count existing structural hotspot function IDs; thresholds and reasons remain in structural.hotspots.',
    'ML': 'max_c_function_score is the maximum actual estimated score among reliably linked analyzed C functions. It is a review signal, not a file/directory defect probability or a new prediction. Never average scores. Null means no scored function.',
    'cycles': 'Strongly connected groups of at least two components, using retained IMPORTS/INCLUDES aggregate edges only. Component aggregation may overapproximate file-level cycles; no runtime or build-cycle claim.',
    'coverage': 'All results cover bounded retained inventory and graph evidence only. Unsupported, unresolved, excluded and truncated content is not evidence of architectural independence.',
}


def combine(items):
    result = Metrics()
    for item in items:
        for field in ('files', 'source_files', 'physical_lines', 'bytes', 'scored_functions'):
            setattr(result, field, getattr(result, field) + getattr(item, field))
        for field in MEASUREMENTS:
            value = getattr(item, field)
            if value is not None:
                previous = getattr(result, field)
                setattr(result, field, max(previous, value) if previous is not None and field.startswith('max_')
                        else (previous or 0) + value if not field.startswith('max_') else value)
            result.measured_files[field] = result.measured_files.get(field, 0) + item.measured_files.get(field, 0)
    return result


def strongly_connected(ids, edges):
    """Iterative Kosaraju; cycles in retained component dependencies only."""
    adjacency = {id: [] for id in ids}
    reverse = {id: [] for id in ids}
    for edge in edges:
        if edge.type in {'IMPORTS', 'INCLUDES'}:
            adjacency[edge.source].append(edge.target)
            reverse[edge.target].append(edge.source)
    seen, order = set(), []
    for id in sorted(ids):
        stack = [(id, False)]
        while stack:
            node, done = stack.pop()
            if done:
                order.append(node)
            elif node not in seen:
                seen.add(node)
                stack.append((node, True))
                stack.extend((child, False) for child in reversed(adjacency[node]) if child not in seen)
    seen, cycles = set(), []
    for id in reversed(order):
        if id in seen:
            continue
        group, stack = [], [id]
        seen.add(id)
        while stack:
            node = stack.pop()
            group.append(node)
            for child in reverse[node]:
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        if len(group) > 1:
            cycles.append(sorted(group))
    return sorted(cycles)


def reconstruct(result, limits=ARCHITECTURE_LIMITS):
    coverage = Coverage(inventory_files=len(result.files))
    graph, structure = result.knowledge_graph, result.structural
    graph_nodes = {n.id: n for n in graph.nodes} if graph else {}
    graph_files = {n.path: n.id for n in graph_nodes.values() if n.type == 'file'}
    graph_directories = {n.path: n.id for n in graph_nodes.values() if n.type == 'directory'}
    root_graph = next((n.id for n in graph_nodes.values() if n.type == 'repository'), None)
    structures = {f.path: f for f in structure.files} if structure else {}
    functions, owners = {}, {}
    for f in structure.functions if structure else []:
        owners[f.id] = f.path
        if f.status == 'analyzed':
            functions.setdefault(f.path, []).append(f)
    hotspots = {h.function_id for h in structure.hotspots} if structure else set()
    root_id = graph_id('heat-root', '.')
    heat = {root_id: HeatNode(root_id, None, 'Repository', '.', 'directory', Metrics(), root_graph)}
    directory_ids = {'.': root_id}
    grouped, file_components, file_nodes = {}, {}, {}
    for file in sorted(result.files, key=lambda f: f.path):
        parts = PurePosixPath(file.path).parts
        ancestors = ['/'.join(parts[:i]) for i in range(1, len(parts))]
        if len(heat) + sum(p not in directory_ids for p in ancestors) + 1 > limits.heat_nodes:
            coverage.truncated = True
            if 'heat_node_limit' not in coverage.issues:
                coverage.issues.append('heat_node_limit')
            continue
        parent = root_id
        for directory in ancestors:
            if directory not in directory_ids:
                id = graph_id('directory', directory)
                directory_ids[directory] = id
                heat[id] = HeatNode(id, parent, PurePosixPath(directory).name, directory, 'directory', Metrics(), graph_directories.get(directory))
            parent = directory_ids[directory]
        id = identity('file', file.path)
        owners[id] = file.path
        record = structures.get(file.path)
        valid = functions.get(file.path, [])
        measured = bool(record and (record.status in {'analyzed', 'no_functions'} or valid))
        metrics = Metrics(files=1, source_files=int(file.is_source), physical_lines=file.lines, bytes=file.bytes,
                          functions=len(valid) if measured else None,
                          max_complexity=max((f.cyclomatic_complexity for f in valid), default=None),
                          total_complexity=sum(f.cyclomatic_complexity for f in valid) if measured else None,
                          hotspots=sum(f.id in hotspots for f in valid) if measured else None)
        scores = []
        for f in valid:
            if (f.language == 'C' and f.ml_result_index is not None and result.defect_risk
                    and 0 <= f.ml_result_index < len(result.defect_risk.functions)):
                prediction = result.defect_risk.functions[f.ml_result_index]
                if (prediction.status == 'analyzed' and prediction.model_probability is not None
                        and (prediction.path, prediction.start_line, prediction.end_line, prediction.name) == (f.path, f.start_line, f.end_line, f.name)
                        and 0 <= prediction.model_probability <= 1):
                    scores.append(prediction.model_probability)
        metrics.max_c_function_score = max(scores, default=None)
        metrics.scored_functions = len(scores)
        metrics.measured_files = {key: int(getattr(metrics, key) is not None) for key in MEASUREMENTS}
        path = PurePosixPath(file.path).parent.as_posix()
        node = HeatNode(id, parent, parts[-1], file.path, 'file', metrics, graph_files.get(file.path),
                        language=file.language, structural_status=record.status if record else 'unavailable',
                        ml_status='scored' if scores else 'unsupported' if PurePosixPath(file.path).suffix != '.c' else 'unscored')
        heat[id] = node
        file_nodes[file.path] = node
        grouped.setdefault(path, []).append(node)
    components = []
    for path in sorted(grouped):
        if len(components) >= limits.components:
            coverage.truncated = True
            if 'component_limit' not in coverage.issues:
                coverage.issues.append('component_limit')
            continue
        id = graph_id('component', path)
        files = grouped[path]
        for node in files:
            node.component_id = id
            file_components[node.path] = id
        components.append(Component(id, '(root files)' if path == '.' else PurePosixPath(path).name, path,
                                    combine(n.metrics for n in files), [n.id for n in files],
                                    sorted(f.id for n in files for f in functions.get(n.path, [])),
                                    root_graph if path == '.' else graph_directories.get(path)))
    by_component = {c.id: c for c in components}
    grouped_edges = {}
    retained_graph_edges = sorted(graph.edges, key=lambda e: e.id) if graph else []
    coverage.retained_graph_edges_observed = len(retained_graph_edges)
    for edge in retained_graph_edges:
        if edge.type not in {'CALLS', 'IMPORTS', 'INCLUDES'} or edge.status != 'resolved_internal':
            continue
        coverage.semantic_edges += 1
        source, target = file_components.get(owners.get(edge.source)), file_components.get(owners.get(edge.target))
        if not source or not target:
            coverage.unmapped_semantic_edges += 1
            continue
        if source == target:
            by_component[source].intra_component_edges += 1
            by_component[source].intra_component_occurrences += edge.occurrences
            continue
        key = (source, target, edge.type)
        if key not in grouped_edges:
            if len(grouped_edges) >= limits.component_edges:
                coverage.omitted_component_edges += 1
                coverage.truncated = True
                continue
            grouped_edges[key] = ComponentEdge(graph_id('component-edge', *key), *key)
        aggregate = grouped_edges[key]
        aggregate.graph_edges += 1
        aggregate.occurrences += edge.occurrences
        if len(aggregate.edge_ids) < limits.evidence_ids:
            aggregate.edge_ids.append(edge.id)
        else:
            aggregate.evidence_truncated = True
    edges = sorted(grouped_edges.values(), key=lambda e: e.id)
    incoming, outgoing = {}, {}
    for edge in edges:
        incoming.setdefault(edge.target, set()).add(edge.source)
        outgoing.setdefault(edge.source, set()).add(edge.target)
    for ref in sorted(graph.references, key=lambda r: r.id) if graph else []:
        component = by_component.get(file_components.get(owners.get(ref.source)))
        if component is None:
            coverage.unmapped_references += 1
            continue
        component.unresolved_count += 1
        if len(component.unresolved_ids) < limits.reference_ids:
            component.unresolved_ids.append(ref.id)
        else:
            component.unresolved_truncated = True
    for component in components:
        component.incoming_components = sorted(incoming.get(component.id, ()))
        component.outgoing_components = sorted(outgoing.get(component.id, ()))
    children = {}
    for node in heat.values():
        if node.parent_id:
            children.setdefault(node.parent_id, []).append(node)
    for node in sorted(heat.values(), key=lambda n: (-len(PurePosixPath(n.path).parts), n.path)):
        if node.type == 'directory':
            node.metrics = combine(n.metrics for n in children.get(node.id, []))
    coverage.retained_files = len(file_nodes)
    coverage.graph_mapped_files = sum(path in graph_files for path in file_nodes)
    coverage.structural_measured_files = sum(n.metrics.functions is not None for n in file_nodes.values())
    coverage.graph_truncated = bool(graph and graph.coverage.truncated)
    coverage.structural_truncated = bool(structure and structure.coverage.truncated)
    if coverage.graph_truncated:
        coverage.issues.append('upstream_graph_truncated')
    if coverage.structural_truncated:
        coverage.issues.append('upstream_structure_truncated')
    coverage.graph_complete = bool(graph and graph.coverage.complete)
    coverage.structural_complete = bool(structure and structure.coverage.complete)
    if not coverage.graph_complete:
        coverage.issues.append('graph_partial_or_unavailable')
    if not coverage.structural_complete:
        coverage.issues.append('structural_partial_or_unavailable')
    if coverage.omitted_component_edges:
        coverage.issues.append('component_edge_limit')
    cycles = strongly_connected(by_component, edges)
    findings = []
    for label, key, format_value in [
        ('Largest by bytes', lambda c: c.metrics.bytes, lambda c: f'{c.metrics.bytes} inventoried bytes'),
        ('Most observed functions', lambda c: c.metrics.functions or 0, lambda c: f'{c.metrics.functions} valid observed functions'),
        ('Highest function complexity', lambda c: c.metrics.max_complexity or 0, lambda c: f'maximum function complexity {c.metrics.max_complexity}'),
        ('Structural review concentration', lambda c: c.metrics.hotspots or 0, lambda c: f'{c.metrics.hotspots} measured hotspot functions'),
        ('Most connected component', lambda c: len(set(c.incoming_components+c.outgoing_components)), lambda c: f'{len(set(c.incoming_components+c.outgoing_components))} distinct connected components')]:
        ranked = sorted(components, key=lambda c: (-key(c), c.path))
        if ranked and key(ranked[0]) > 0:
            winner = ranked[0]
            findings.append({'title': label, 'component_id': winner.id,
                             'text': f'{winner.path}: {format_value(winner)}. Inspect members and retained source evidence; this is not a quality score.'})
    return Architecture(components, edges, sorted(heat.values(), key=lambda n: (n.path, n.type)), cycles, findings,
                        {'components': len(components), 'aggregate_edges': len(edges), 'cross_component_graph_edges': sum(e.graph_edges for e in edges),
                         'cross_component_occurrences': sum(e.occurrences for e in edges), 'intra_component_graph_edges': sum(c.intra_component_edges for c in components),
                         'dependency_cycle_groups': len(cycles), 'unresolved_references': sum(c.unresolved_count for c in components)},
                        coverage, DEFINITIONS.copy(), asdict(limits))

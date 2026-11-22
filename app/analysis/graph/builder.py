"""Deterministic graph construction with retained-output accounting."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json

from .models import Coverage, Edge, KnowledgeGraph, Reference


def graph_id(kind, *parts):
    value = json.dumps([kind, *parts], ensure_ascii=True, separators=(',', ':'))
    return 'graph_'+kind+'_'+hashlib.sha256(value.encode()).hexdigest()


class Builder:
    def __init__(self, limits):
        self.limits = limits
        self.coverage = Coverage()
        self.nodes = {}
        self.edges = {}
        self.references = []
        self.reference_ids = Counter()
        self.bytes = 0

    def issue(self, reason, truncated=False):
        # Reasons are controlled codes, never exception text or source contents.
        if reason not in self.coverage.issues:
            self.coverage.issues.append(reason)
        self.coverage.truncated |= truncated

    def reserve(self, item):
        size = len(json.dumps(asdict(item), ensure_ascii=True).encode())+2
        # Reserve space for summary, coverage, limits and envelope (fixed-size codes).
        if self.bytes+size > max(0, self.limits.output_bytes-16384):
            self.issue('output_bytes_limit', True)
            return False
        self.bytes += size
        return True

    def node(self, node):
        if node.id in self.nodes:
            return True
        if len(self.nodes) >= self.limits.nodes:
            self.issue('node_limit', True)
            return False
        if not self.reserve(node):
            return False
        self.nodes[node.id] = node
        return True

    def edge(self, source, target, kind, reference='', evidence=None):
        if source not in self.nodes or target not in self.nodes:
            self.issue('endpoint_not_retained', True)
            return
        key = graph_id('edge', source, target, kind, reference)
        if key in self.edges:
            edge = self.edges[key]
            # Charge counter growth conservatively even when evidence is capped.
            if self.bytes+16 > self.limits.output_bytes-16384:
                self.issue('output_bytes_limit', True)
                return
            self.bytes += 16
            edge.occurrences += 1
            if evidence is not None:
                if len(edge.evidence) < self.limits.evidence_per_edge and self.reserve(evidence):
                    edge.evidence.append(evidence)
                else:
                    edge.evidence_truncated = True
                    self.issue('evidence_limit', True)
            return
        if len(self.edges) >= self.limits.edges:
            self.issue('edge_limit', True)
            return
        edge = Edge(key, source, target, kind, reference,
                    evidence=[evidence] if evidence is not None and self.limits.evidence_per_edge else [])
        if evidence is not None and not edge.evidence:
            edge.evidence_truncated = True
            self.issue('evidence_limit', True)
        if self.reserve(edge):
            self.edges[key] = edge

    def reference(self, source, kind, name, status, reason, evidence):
        if source not in self.nodes:
            self.issue('endpoint_not_retained', True)
            return
        if len(self.references) >= self.limits.unresolved:
            self.issue('unresolved_limit', True)
            return
        base_id = graph_id('reference', source, kind, name, status, asdict(evidence))
        ordinal = self.reference_ids[base_id]
        self.reference_ids[base_id] += 1
        ref = Reference(graph_id('reference_occurrence',base_id,ordinal),
                        source, kind, name, status, reason, evidence)
        if self.reserve(ref):
            self.references.append(ref)

    def finish(self):
        nodes = sorted(self.nodes.values(), key=lambda n:n.id)
        edges = sorted(self.edges.values(), key=lambda e:e.id)
        refs = sorted(self.references, key=lambda r:(r.evidence.path,r.evidence.line,r.evidence.column,r.id))
        calls = [e for e in edges if e.type == 'CALLS']
        deps = [e for e in edges if e.type in {'IMPORTS','INCLUDES'}]
        summary = dict(nodes=len(nodes), edges=len(edges), references=len(refs),
                       node_types=dict(sorted(Counter(n.type for n in nodes).items())),
                       edge_types=dict(sorted(Counter(e.type for e in edges).items())),
                       resolved_call_edges=len(calls), resolved_call_occurrences=sum(e.occurrences for e in calls),
                       unresolved_call_references=sum(r.type=='CALLS' for r in refs),
                       ambiguous_references=sum(r.status=='ambiguous' for r in refs),
                       internal_dependency_edges=len(deps), internal_dependency_occurrences=sum(e.occurrences for e in deps),
                       unresolved_dependency_references=sum(r.type in {'IMPORTS','INCLUDES'} for r in refs))
        self.coverage.complete = not (self.coverage.issues or self.coverage.skipped_files or self.coverage.unsupported_source_files)
        return KnowledgeGraph(nodes, edges, refs, summary, self.coverage, asdict(self.limits))

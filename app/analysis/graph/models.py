"""Versioned graph contracts. Unresolved references never masquerade as edges."""
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Node:
    id: str
    type: Literal['repository', 'directory', 'file', 'function']
    name: str
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    path: str
    line: int
    column: int


@dataclass
class Edge:
    id: str
    source: str
    target: str
    type: Literal['CONTAINS', 'DEFINES', 'CALLS', 'IMPORTS', 'INCLUDES']
    reference: str = ''
    status: str = 'resolved_internal'
    occurrences: int = 1
    evidence: list[Evidence] = field(default_factory=list)
    evidence_truncated: bool = False


@dataclass
class Reference:
    id: str
    source: str
    type: str
    reference: str
    status: Literal['unresolved', 'ambiguous', 'unsupported_dynamic']
    reason: str
    evidence: Evidence


@dataclass
class Coverage:
    supported_languages: list[str] = field(default_factory=lambda: ['C (.c, .h includes)', 'Python (.py, .pyi)'])
    eligible_files: int = 0
    analyzed_files: int = 0
    skipped_files: int = 0
    unsupported_source_files: int = 0
    source_bytes: int = 0
    visited_nodes: int = 0
    observed_references: int = 0
    retained_symbol_bindings: int = 0
    truncated: bool = False
    complete: bool = False
    issues: list[str] = field(default_factory=list)


@dataclass
class KnowledgeGraph:
    nodes: list[Node]
    edges: list[Edge]
    references: list[Reference]
    summary: dict[str, Any]
    coverage: Coverage
    limits: dict[str, int]
    schema_version: str = '1.0'


class GraphIndex:
    """Reusable O(V+E) index; callers can traverse cycles using their own visited set."""
    def __init__(self, graph):
        self.nodes = {node.id: node for node in graph.nodes}
        self._incoming = {}
        self._outgoing = {}
        for edge in graph.edges:
            self._incoming.setdefault(edge.target, []).append(edge)
            self._outgoing.setdefault(edge.source, []).append(edge)

    def node(self, identity):
        return self.nodes.get(identity)

    def nodes_of_type(self, kind):
        return [n for n in self.nodes.values() if n.type == kind]

    def incoming(self, identity, kind=None):
        return [e for e in self._incoming.get(identity, ()) if kind is None or e.type == kind]

    def outgoing(self, identity, kind=None):
        return [e for e in self._outgoing.get(identity, ()) if kind is None or e.type == kind]

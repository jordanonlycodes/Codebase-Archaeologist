"""Small source fixtures with manually known static relationships."""
from dataclasses import asdict, replace
from pathlib import Path
import json

import pytest

from app.analysis.graph.engine import extract_graph
from app.analysis.graph.models import GraphIndex
from app.analysis.structural import analyze_structure, identity, link_ml_results
from app.analysis.lines import measure
from app.analysis.models import FileMetrics, RepositorySource
from app.config import GRAPH_LIMITS
from types import SimpleNamespace


def graph(tmp_path, sources, limits=GRAPH_LIMITS, reverse=False):
    files=[]
    for path,text in sources.items():
        p=tmp_path/path
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(text)
        language='Python' if p.suffix in {'.py','.pyi'} else 'C' if p.suffix in {'.c','.h'} else 'JavaScript'
        files.append(FileMetrics(path,language,True,len(text.encode()),**measure(text,language)))
    if reverse:
        files.reverse()
    cache={}
    structural=analyze_structure(tmp_path,files,parsed_files=cache)
    result=SimpleNamespace(files=files,structural=structural,repository='fixture.zip',source=RepositorySource('zip',filename='fixture.zip'),defect_risk=None)
    return extract_graph(tmp_path,result,parsed_files=cache,limits=limits),structural


def relationships(g, kind):
    nodes={n.id:n for n in g.nodes}
    return [(nodes[e.source].name,nodes[e.target].name,e) for e in g.edges if e.type==kind]


def test_hierarchy_ids_determinism(tmp_path):
    sources={'a.py':'def a(): pass','sub/a.py':'def a(): pass','sub/deep/file.js':'let x=1;'}
    g,s=graph(tmp_path,sources)
    other,_=graph(tmp_path,sources,reverse=True)
    assert asdict(g)==asdict(other)
    ids=[n.id for n in g.nodes]
    assert len(ids)==len(set(ids))
    assert {f.id for f in s.functions}<set(ids)
    assert {f.id for f in s.files}<set(ids)
    assert len(relationships(g,'CONTAINS'))==5
    assert len(relationships(g,'DEFINES'))==2
    assert all(e.source in ids and e.target in ids for e in g.edges)
    assert g.coverage.unsupported_source_files==1
    assert not g.coverage.complete


def test_c_direct_recursion_repeat_and_evidence(tmp_path):
    g,_=graph(tmp_path,{'a.c':'int f(void){return f();}\nint g(void){ f(); if(f()) return f(); return 0; }'})
    calls=relationships(g,'CALLS')
    assert {(s,t,e.occurrences) for s,t,e in calls}=={('f','f',1),('g','f',3)}
    assert all(e.evidence[0].line in {1,2} for _,_,e in calls)
    assert g.summary['resolved_call_occurrences']==4
    assert g.summary['resolved_call_edges']==2


@pytest.mark.parametrize('declaration,definition,status',[
    ('int f(void);','int f(void){return 1;}','resolved_internal'),
    ('','int f(void){return 1;}','unresolved'),
    ('int f(void);','static int f(void){return 1;}','unresolved'),
])
def test_c_cross_file_visibility(tmp_path,declaration,definition,status):
    g,_=graph(tmp_path,{'a.c':declaration+'\nint g(void){return f();}','b.c':definition})
    assert bool(relationships(g,'CALLS'))==(status=='resolved_internal')
    if status!='resolved_internal': assert g.references[0].status==status


def test_c_ambiguous_symbols(tmp_path):
    g,_=graph(tmp_path,{'a.c':'int f(void); int g(void){return f();}','b.c':'int f(void){return 1;}','c.c':'int f(void){return 2;}'})
    assert not relationships(g,'CALLS')
    assert g.references[0].status=='ambiguous'


@pytest.mark.parametrize('source',[
    'int f(void){return 0;} int g(int (*f)(void)){return f();}',
    'int f(void){return 0;} int g(void){int (*f)(void); return f();}',
    'int f(void){return 0;} int g(void){return (*f)();}',
    '#define f() 2\nint g(void){return f();}',
])
def test_c_indirect_and_macros(tmp_path,source):
    g,_=graph(tmp_path,{'a.c':source})
    assert not relationships(g,'CALLS')
    assert any(r.status=='unsupported_dynamic' for r in g.references)


def test_c_comments_strings_no_calls(tmp_path):
    g,_=graph(tmp_path,{'a.c':'int f(void){/* f(); */ char *s="f()"; return 0;}'})
    assert not relationships(g,'CALLS') and not g.references


def test_c_includes_declarations(tmp_path):
    g,_=graph(tmp_path,{'src/a.c':'#include "api.h"\n#include <stdio.h>\nint g(void){return f();}',
                      'src/api.h':'int f(void);','impl.c':'int f(void){return 1;}'})
    assert [(s,t) for s,t,_ in relationships(g,'INCLUDES')]==[('a.c','api.h')]
    assert [(s,t) for s,t,_ in relationships(g,'CALLS')]==[('g','f')]
    assert any(r.type=='INCLUDES' and r.reference=='stdio.h' and r.status=='unresolved' for r in g.references)


def test_c_ambiguous_and_macro_include(tmp_path):
    g,_=graph(tmp_path,{'a.c':'#include <api.h>\n#include HEADER\n','x/api.h':'','y/api.h':''})
    assert not relationships(g,'INCLUDES')
    assert {r.status for r in g.references}=={'ambiguous','unsupported_dynamic'}


def test_python_local_recursive_nested_scope(tmp_path):
    g,_=graph(tmp_path,{'a.py':'''def target(): pass
def outer():
    def inner():
        target()
        inner()
    inner()
    return 1
'''} )
    calls={(s,t) for s,t,_ in relationships(g,'CALLS')}
    assert calls=={('outer.inner','target'),('outer.inner','outer.inner'),('outer','outer.inner')}


@pytest.mark.parametrize('statement,call',[
    ('import other','other.f()'),('import other as o','o.f()'),
    ('from other import f','f()'),('from other import f as alias','alias()'),
])
def test_python_import_calls(tmp_path,statement,call):
    g,_=graph(tmp_path,{'a.py':statement+'\ndef run():\n '+call,'other.py':'def f(): pass'})
    assert [(s,t) for s,t,_ in relationships(g,'CALLS')]==[('run','f')]
    assert len(relationships(g,'IMPORTS'))==1


@pytest.mark.parametrize('statement,call',[
    ('from .other import f','f()'),('from . import other','other.f()'),
    ('import pkg.other','pkg.other.f()'),('import pkg.other as o','o.f()'),
    ('from pkg import other','other.f()'),
])
def test_python_packages_relative(tmp_path,statement,call):
    g,_=graph(tmp_path,{'pkg/__init__.py':'','pkg/a.py':statement+'\ndef run():\n '+call,'pkg/other.py':'def f(): pass'})
    assert [(s,t) for s,t,_ in relationships(g,'CALLS')]==[('run','f')]
    assert len(relationships(g,'IMPORTS'))==1


def test_src_package_and_ambiguous_roots(tmp_path):
    sources={'src/pkg/__init__.py':'','src/pkg/a.py':'from .b import f\ndef run(): f()', 'src/pkg/b.py':'def f(): pass'}
    g,_=graph(tmp_path,sources)
    assert len(relationships(g,'CALLS'))==1
    sources.update({'pkg/__init__.py':'','pkg/b.py':'def f(): pass'})
    g,_=graph(tmp_path,sources)
    assert not relationships(g,'CALLS')
    assert any(r.status=='ambiguous' for r in g.references)


@pytest.mark.parametrize('source',[
    'def f(): pass\ndef g(f): f()',
    'def f(): pass\ndef g():\n f()\n f = 1',
    'from other import f\nf = 1\ndef g(): f()',
    'import other\ndef g(other): other.f()',
    'def f(): pass\ndef g(obj): obj.f()',
    'def f(): pass\ndef g():\n global f\n f()',
    'from other import *\ndef g(): f()',
    'def f(): pass\ndef g(): [f() for f in []]',
    'def f(): pass\ndef g():\n match 1:\n  case f: f()',
])
def test_python_shadowed_or_dynamic(tmp_path,source):
    g,_=graph(tmp_path,{'a.py':source,'other.py':'def f(): pass'})
    assert not relationships(g,'CALLS')
    assert any(r.type=='CALLS' and r.status in {'unsupported_dynamic','ambiguous'} for r in g.references)


def test_python_module_calls_class_methods_and_dynamic_import(tmp_path):
    g,_=graph(tmp_path,{'a.py':'''def f(): pass
f()
class C:
    def f(self): pass
    def g(self):
        self.f()
        f()
__import__('other')
'''})
    assert {(s,t) for s,t,_ in relationships(g,'CALLS')}=={('a.py','f'),('C.g','f')}
    assert any(r.type=='IMPORTS' and r.status=='unsupported_dynamic' for r in g.references)
    assert any(r.reference=='self.f' and r.status=='unsupported_dynamic' for r in g.references)


def test_cyclic_query_index_and_summary(tmp_path):
    g,_=graph(tmp_path,{'a.py':'def a(): b()\ndef b(): a()'})
    index=GraphIndex(g)
    functions=index.nodes_of_type('function')
    for f in functions:
        assert index.node(f.id)==f
        assert len(index.incoming(f.id,'CALLS'))==1
        assert len(index.outgoing(f.id,'CALLS'))==1
    assert g.summary['nodes']==len(g.nodes)
    assert g.summary['edges']==len(g.edges)
    assert sum(g.summary['node_types'].values())==len(g.nodes)
    assert sum(g.summary['edge_types'].values())==len(g.edges)


@pytest.mark.parametrize('limit,value,code',[
    ('nodes',2,'node_limit'),('edges',1,'edge_limit'),('references',1,'reference_or_work_limit'),
    ('unresolved',1,'unresolved_limit'),('evidence_per_edge',1,'evidence_limit'),
    ('nodes_per_file',1,'reference_or_work_limit'),('total_bytes',1,'source_or_work_limit'),
    ('symbols',1,'symbol_limit'),('output_bytes',17000,'output_bytes_limit'),
])
def test_resource_limits(tmp_path,limit,value,code):
    sources={'a.py':'def f():\n f()\n f()\n unknown()\n missing()\ndef g(): f()'}
    if limit=='output_bytes': sources.update({f'other{i}.py':'def x(): pass' for i in range(40)})
    g,_=graph(tmp_path,sources,replace(GRAPH_LIMITS,**{limit:value}))
    assert g.coverage.truncated and not g.coverage.complete
    assert code in g.coverage.issues
    assert all(e.source in {n.id for n in g.nodes} and e.target in {n.id for n in g.nodes} for e in g.edges)
    assert len(json.dumps(asdict(g),ensure_ascii=True).encode()) <= (value if limit=='output_bytes' else GRAPH_LIMITS.output_bytes)


def test_malformed_and_empty(tmp_path):
    g,_=graph(tmp_path,{'a.c':'int f( { broken','b.py':'def invalid(', 'empty.py':''})
    assert not relationships(g,'CALLS')
    assert g.coverage.skipped_files==2 and g.coverage.analyzed_files==1
    assert not g.coverage.complete


def test_reuses_parsers_and_structural_values(tmp_path,monkeypatch):
    from app.analysis.graph import engine
    sources={'a.py':'def f(): f()','a.c':'int f(void){return f();}'}
    # Graph must use structural parse cache, not parse again.
    monkeypatch.setattr(engine,'parse_c',lambda *_:pytest.fail('C parsed twice'))
    original=engine.ast.parse
    count=[]
    def parse(*args,**kwargs):
        count.append(1)
        return original(*args,**kwargs)
    monkeypatch.setattr(engine.ast,'parse',parse)
    g,s=graph(tmp_path,sources)
    assert len(count)==1  # exactly one Python parse, performed by structure
    functions={n.id:n for n in g.nodes if n.type=='function'}
    for f in s.functions:
        assert functions[f.id].metadata['cyclomatic_complexity']==f.cyclomatic_complexity
        assert functions[f.id].metadata['ml_status']=='unavailable'
    assert len(relationships(g,'CALLS'))==2


def test_shared_pipeline_and_real_model(make_zip):
    from app.routes.analysis import analyze_archive
    archive=make_zip({'repo/a.py':'def p(): p()','repo/a.c':'int c(void){return c();}'})
    result=analyze_archive(archive,'fixture.zip',RepositorySource('zip',filename='fixture.zip'))
    graph=result.knowledge_graph
    assert len(relationships(graph,'CALLS'))==2
    assert 'knowledge_graph' in asdict(result)
    assert result.summary.files==2 and result.structural.summary.analyzed_functions==2
    c=next(n for n in graph.nodes if n.type=='function' and n.metadata['language']=='C')
    p=next(n for n in graph.nodes if n.type=='function' and n.metadata['language']=='Python')
    assert 'ml' not in p.metadata
    assert c.metadata['ml_result_index']==0
    assert c.metadata['ml']['model_probability']==result.defect_risk.functions[0].model_probability


def test_missing_model_still_graph(make_zip,tmp_path,monkeypatch):
    from app.ml.repository import ModelService
    from app.routes.analysis import analyze_archive
    monkeypatch.setattr('app.ml.repository.SERVICE',ModelService(tmp_path/'missing'))
    result=analyze_archive(make_zip({'a.c':'int f(void){return f();}'}),'a.zip',RepositorySource('zip'))
    assert result.defect_risk.status=='unavailable'
    assert len(relationships(result.knowledge_graph,'CALLS'))==1


def test_include_target_and_header_macro(tmp_path):
    g,_=graph(tmp_path,{'a.c':'#include "macros.h"\nint f(void){return 0;}\nint g(void){return f();}',
                      'macros.h':'#define f() 7\n'})
    assert not relationships(g,'CALLS')
    assert any(r.reference=='f' and r.status=='unsupported_dynamic' for r in g.references)


def test_from_package_dependency_points_to_submodule(tmp_path):
    g,_=graph(tmp_path,{'pkg/__init__.py':'','pkg/child.py':'def f(): pass',
                      'a.py':'from pkg import child\ndef g(): child.f()'})
    assert [(s,t) for s,t,_ in relationships(g,'IMPORTS')]==[('a.py','child.py')]


def test_module_and_package_attribute_collision(tmp_path):
    g,_=graph(tmp_path,{'pkg/__init__.py':'def child(): pass','pkg/child.py':'def f(): pass',
                      'a.py':'from pkg import child\ndef g(): child.f()'})
    assert not relationships(g,'CALLS')
    assert any(r.status=='ambiguous' and r.type=='IMPORTS' for r in g.references)


def test_symbol_binding_limit(tmp_path):
    source='\n'.join(f'x{i}={i}' for i in range(30))
    g,_=graph(tmp_path,{'a.py':source},replace(GRAPH_LIMITS,symbols=10))
    assert g.coverage.retained_symbol_bindings<=10
    assert g.coverage.truncated and 'symbol_limit' in g.coverage.issues


@pytest.mark.parametrize('source',[
    'def f(): pass\nexec("f = None")\ndef g(): f()',
    'def f(): pass\n@decorator\ndef g(): pass\ndef h(): g()',
    'def f(): pass\ndef g():\n if True:\n  from other import f\n f()',
    'def f(): pass\ndef g():\n f = lambda: None\n f()',
])
def test_dynamic_binding_cases(tmp_path,source):
    g,_=graph(tmp_path,{'a.py':source,'other.py':'def f(): pass'})
    assert not relationships(g,'CALLS')


def test_duplicate_reference_ids_unique(tmp_path):
    g,_=graph(tmp_path,{'a.py':'import unknown, unknown'})
    assert len(g.references)==2
    assert len({r.id for r in g.references})==2


def test_file_and_global_traversal_limits(tmp_path):
    for limits in (replace(GRAPH_LIMITS,file_bytes=1), replace(GRAPH_LIMITS,traversal_nodes=1)):
        g,_=graph(tmp_path,{'a.py':'def f(): f()'},limits)
        assert g.coverage.truncated and not g.coverage.complete
        assert g.coverage.visited_nodes<=limits.traversal_nodes


def test_unavailable_and_partial_structural_functions(tmp_path):
    g,s=graph(tmp_path,{'a.c':'int good(void){return good();}\nint bad( {'})
    assert any(f.name=='good' for f in s.functions)
    assert not relationships(g,'CALLS')  # conservative whole-file semantic failure
    assert any(n.name=='good' and n.type=='function' for n in g.nodes)
    assert not g.coverage.complete


def test_graph_does_not_mutate_structure_or_ml(make_zip,tmp_path):
    from app.ingestion.archive import extract_repository
    from app.analysis.scanner import scan_repository
    from app.ml.repository import analyze_functions
    source=make_zip({'a.c':'int f(void){return f();}'})
    result=scan_repository(tmp_path,'test.zip',extract_repository(source,tmp_path))
    cache={}
    result.structural=analyze_structure(tmp_path,result.files,parsed_files=cache)
    result.defect_risk=analyze_functions(tmp_path,result.files,parsed_files=cache)
    link_ml_results(result.structural,result.defect_risk)
    before=asdict(result)
    g=extract_graph(tmp_path,result,parsed_files=cache)
    assert asdict(result)==before
    assert len(relationships(g,'CALLS'))==1


def test_api_graph_and_json_export_contract(make_zip):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        response=client.post('/api/analyze',files={'file':('a.zip',make_zip({'a.py':'def f(): f()'}).getvalue())})
        assert response.status_code==200
        data=response.json()
        assert {'structural','source','defect_risk','summary','files','knowledge_graph'}<=data.keys()
        assert data['knowledge_graph']['summary']['resolved_call_edges']==1
        assert data['knowledge_graph']['schema_version']=='1.0'
        assert 'JSON.stringify(result, null, 2)' in client.get('/static/product/workspace.js').text
        schema=client.get('/openapi.json').json()
        assert 'knowledge_graph' in schema['components']['schemas']['AnalysisResult']['properties']


def test_static_declaration_never_links_external_definition(tmp_path):
    g,_=graph(tmp_path,{'a.c':'static int f(void); int g(void){return f();}', 'b.c':'int f(void){return 1;}'})
    assert not relationships(g,'CALLS')
    assert g.references[0].status=='unresolved'


def test_same_file_static_definition_with_prototype(tmp_path):
    g,_=graph(tmp_path,{'a.c':'static int f(void); static int f(void){return 0;} int g(void){return f();}'})
    assert [(s,t) for s,t,_ in relationships(g,'CALLS')]==[('g','f')]


def test_malformed_included_header_prevents_call_claim(tmp_path):
    g,_=graph(tmp_path,{'a.c':'#include "bad.h"\nint f(void){return f();}', 'bad.h':'#define f() 7'})
    assert not relationships(g,'CALLS')
    assert g.coverage.skipped_files==1
    assert any(r.type=='CALLS' and r.status=='unsupported_dynamic' for r in g.references)


def test_long_c_reference_cannot_resolve_truncated_prefix(tmp_path):
    prefix='f'*256
    g,_=graph(tmp_path,{'a.c':f'int {prefix}(void){{return 1;}} int g(void){{return {prefix}x();}}'})
    assert not relationships(g,'CALLS')
    assert any(r.status=='unsupported_dynamic' for r in g.references)
    assert 'reference_length_limit' in g.coverage.issues


def test_failed_parses_consume_source_budget(tmp_path):
    sources={f'a{i}.py':'def invalid(' for i in range(4)}
    g,_=graph(tmp_path,sources,replace(GRAPH_LIMITS,total_bytes=24))
    assert g.coverage.source_bytes==24
    assert g.coverage.skipped_files==4
    assert 'source_or_work_limit' in g.coverage.issues


def test_graph_limit_configuration_rejects_invalid_envelope():
    with pytest.raises(ValueError):
        replace(GRAPH_LIMITS,output_bytes=10)
    with pytest.raises(ValueError):
        replace(GRAPH_LIMITS,edges=-1)


@pytest.mark.parametrize('source',[
    'def f(): pass\ndef g():\n [(f := 1) for x in []]\n f()',
    'try:\n from other import f\nexcept* Exception:\n pass\ndef g(): f()',
])
def test_comprehension_assignment_and_try_star_bindings(tmp_path,source):
    g,_=graph(tmp_path,{'a.py':source,'other.py':'def f(): pass'})
    assert not relationships(g,'CALLS')

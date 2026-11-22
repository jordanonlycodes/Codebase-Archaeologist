"""Known small repositories verify architecture facts rather than layout guesses."""
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest
from app.analysis.models import FileMetrics, RepositorySource
from app.analysis.lines import measure
from app.analysis.structural import analyze_structure, link_ml_results
from app.analysis.graph.engine import extract_graph
from app.analysis.architecture.engine import reconstruct, combine, strongly_connected
from app.analysis.architecture.models import Metrics, ComponentEdge
from app.config import ARCHITECTURE_LIMITS


def analyze(tmp_path, sources):
    files=[]
    for path,text in sources.items():
        file=tmp_path/path
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(text)
        language='Python' if file.suffix=='.py' else 'C' if file.suffix in {'.c','.h'} else 'JavaScript' if file.suffix=='.js' else 'Text'
        files.append(FileMetrics(path,language,language!='Text',len(text.encode()),**measure(text,language)))
    cache={}
    result=SimpleNamespace(files=files,structural=analyze_structure(tmp_path,files,parsed_files=cache),defect_risk=None,
                           knowledge_graph=None,source=RepositorySource('zip'),repository='fixture')
    result.knowledge_graph=extract_graph(tmp_path,result,parsed_files=cache)
    return result


@pytest.fixture
def sources():
    return {'README.md':'Notes\n','a/__init__.py':'','b/__init__.py':'',
            'a/core.py':'from b.util import helper\ndef entry(): return helper()\n',
            'b/util.py':'from a.core import entry\ndef helper(): return entry()\n',
            'z/client.js':'function unsupported(){return 1;}\n'}


def test_partition_hierarchy_and_metrics(tmp_path,sources):
    result=analyze(tmp_path,sources);data=reconstruct(result)
    components={c.path:c for c in data.components}
    assert set(components)=={'.','a','b','z'}
    assert components['a'].metrics.files==2 and components['a'].metrics.functions==1
    assert components['z'].metrics.functions is None
    assert components['z'].metrics.max_c_function_score is None
    root=next(n for n in data.heatmap if n.parent_id is None)
    assert root.metrics.files==len(sources)
    assert root.metrics.physical_lines==sum(f.lines for f in result.files)
    assert root.metrics.functions==2
    ids=[id for c in data.components for id in c.file_ids]
    assert len(ids)==len(set(ids))==len(sources)
    assert all(n.parent_id in {n.id for n in data.heatmap} for n in data.heatmap if n.parent_id)
    assert components['a'].metrics.measured_files['functions']==2


def test_nested_directory_components_do_not_double_count(tmp_path):
    result=analyze(tmp_path,{'pkg/a.py':'def a(): pass','pkg/sub/b.py':'def b(): pass'})
    data=reconstruct(result);components={c.path:c for c in data.components}
    assert components['pkg'].metrics.files==components['pkg/sub'].metrics.files==1
    directory=next(n for n in data.heatmap if n.path=='pkg')
    assert directory.metrics.files==2 and directory.metrics.functions==2
    assert all(n.path!='empty' for n in data.heatmap)


def test_directed_aggregation_cycles_and_original_evidence(tmp_path,sources):
    result=analyze(tmp_path,sources);data=reconstruct(result)
    paths={c.id:c.path for c in data.components}
    assert {(paths[e.source],paths[e.target],e.type) for e in data.edges}=={('a','b','IMPORTS'),('b','a','IMPORTS'),('a','b','CALLS'),('b','a','CALLS')}
    assert len(data.dependency_cycles)==1
    assert {paths[id] for id in data.dependency_cycles[0]}=={'a','b'}
    original={e.id:e for e in result.knowledge_graph.edges}
    assert all(id in original for edge in data.edges for id in edge.edge_ids)
    assert data.summary['cross_component_graph_edges']==4
    assert all(c.incoming_components and c.outgoing_components for c in data.components if c.path in {'a','b'})


def test_repeated_calls_aggregate_occurrences_and_self_calls_stay_internal(tmp_path):
    result=analyze(tmp_path,{'a/__init__.py':'','b/__init__.py':'',
          'a/run.py':'from b.lib import f\ndef run():\n f()\n f()\n f()','b/lib.py':'def f(): f()'})
    data=reconstruct(result)
    call=next(e for e in data.edges if e.type=='CALLS')
    assert call.graph_edges==1 and call.occurrences==3
    b=next(c for c in data.components if c.path=='b')
    assert b.intra_component_edges==1
    assert data.dependency_cycles==[]


def test_calls_alone_are_not_dependency_cycles(tmp_path):
    result=analyze(tmp_path,{'a/a.c':'int b(void); int a(void){return b();}','b/b.c':'int a(void); int b(void){return a();}'})
    data=reconstruct(result)
    assert len(data.edges)==2 and all(e.type=='CALLS' for e in data.edges)
    assert data.dependency_cycles==[]


def test_quoted_c_include_direction(tmp_path):
    result=analyze(tmp_path,{'src/a.c':'#include "../include/a.h"\nint a(void){return 0;}','include/a.h':'int a(void);\n'})
    data=reconstruct(result);paths={c.id:c.path for c in data.components}
    assert [(paths[e.source],paths[e.target],e.type) for e in data.edges]==[('src','include','INCLUDES')]


def test_unresolved_reference_count_and_bounds(tmp_path):
    result=analyze(tmp_path,{'src/a.py':'def f():\n missing()\n other()\n missing()'})
    data=reconstruct(result,replace(ARCHITECTURE_LIMITS,reference_ids=1))
    component=data.components[0]
    assert component.unresolved_count==3 and len(component.unresolved_ids)==1
    assert component.unresolved_truncated
    assert data.edges==[]


def test_ambiguous_references_are_not_dependencies(tmp_path):
    result=analyze(tmp_path,{'a/a.c':'int f(void); int a(void){return f();}','b/b.c':'int f(void){return 1;}','c/c.c':'int f(void){return 2;}'})
    data=reconstruct(result)
    assert not data.edges
    a=next(c for c in data.components if c.path=='a')
    assert a.unresolved_count==1
    ref=next(r for r in result.knowledge_graph.references if r.id==a.unresolved_ids[0])
    assert ref.status=='ambiguous'


@pytest.mark.parametrize('sources,status,functions',[
    ({'a.py':''},'no_functions',0),({'a.py':'# comment\n'},'no_functions',0),
    ({'a.py':'def invalid('},'unavailable',None),({'a.js':'function x(){}'},'unsupported',None),
])
def test_missing_metrics_are_not_zero(tmp_path,sources,status,functions):
    data=reconstruct(analyze(tmp_path,sources));file=next(n for n in data.heatmap if n.type=='file')
    assert file.structural_status==status and file.metrics.functions==functions
    assert file.metrics.max_complexity is None and file.metrics.max_c_function_score is None


def test_exact_complexity_and_hotspot_aggregation(tmp_path):
    source='def f(x):\n'+''.join(' if x: x-=1\n' for _ in range(10))+' return x\ndef simple(): pass\n'
    result=analyze(tmp_path,{'src/a.py':source,'src/sub/b.py':'def b(): pass'})
    data=reconstruct(result);root=next(n for n in data.heatmap if n.parent_id is None)
    assert root.metrics.max_complexity==11 and root.metrics.total_complexity==13
    assert root.metrics.hotspots==1 and root.metrics.functions==3
    assert next(c for c in data.components if c.path=='src').metrics.total_complexity==12


def test_missing_model_and_real_score_linking(make_zip,tmp_path,monkeypatch):
    from app.routes.analysis import analyze_archive
    from app.ml.repository import ModelService
    from app.ml.schemas import DefectRisk, FunctionResult
    result=analyze(tmp_path,{'a.c':'int a(void){return 1;}','b.py':'def b(): pass'})
    f=next(f for f in result.structural.functions if f.language=='C')
    result.defect_risk=DefectRisk('ready','fixture',functions=[FunctionResult(f.name,f.path,f.start_line,f.end_line,'analyzed',1,.7)])
    link_ml_results(result.structural,result.defect_risk)
    data=reconstruct(result);c=next(n for n in data.heatmap if n.path=='a.c')
    assert c.metrics.max_c_function_score==.7 and c.metrics.scored_functions==1
    assert next(n for n in data.heatmap if n.path=='b.py').metrics.max_c_function_score is None
    monkeypatch.setattr('app.ml.repository.SERVICE',ModelService(tmp_path/'absent'))
    result=analyze_archive(make_zip({'a.c':'int a(void){return a();}'}),'fixture.zip',RepositorySource('zip'))
    assert result.defect_risk.status=='unavailable'
    assert result.architecture.components[0].metrics.functions==1
    assert result.architecture.components[0].metrics.max_c_function_score is None


def test_partial_measurement_coverage(tmp_path):
    data=reconstruct(analyze(tmp_path,{'a.py':'def f(): pass','b.js':'x=1'}))
    root=next(n for n in data.heatmap if n.parent_id is None)
    assert root.metrics.functions==1 and root.metrics.measured_files['functions']==1 and root.metrics.files==2
    assert not data.coverage.structural_complete


@pytest.mark.parametrize('limit,number,reason',[
    ('components',1,'component_limit'),('heat_nodes',3,'heat_node_limit'),('component_edges',1,'component_edge_limit')
])
def test_truncation_is_explicit(tmp_path,sources,limit,number,reason):
    data=reconstruct(analyze(tmp_path,sources),replace(ARCHITECTURE_LIMITS,**{limit:number}))
    assert data.coverage.truncated and reason in data.coverage.issues
    if limit=='components': assert len(data.components)<=number
    if limit=='heat_nodes': assert len(data.heatmap)<=number
    if limit=='component_edges': assert len(data.edges)<=number


def test_edge_evidence_bounds(tmp_path,sources):
    result=analyze(tmp_path,sources)
    original=next(e for e in result.knowledge_graph.edges if e.type=='CALLS')
    result.knowledge_graph.edges.append(replace(original,id='another',occurrences=4))
    data=reconstruct(result,replace(ARCHITECTURE_LIMITS,evidence_ids=1))
    edge=next(e for e in data.edges if e.occurrences==5)
    assert edge.graph_edges==2 and len(edge.edge_ids)==1 and edge.evidence_truncated


def test_deterministic_and_does_not_mutate_inputs(tmp_path,sources):
    result=analyze(tmp_path,sources)
    before=(asdict(result.structural),asdict(result.knowledge_graph))
    data=reconstruct(result)
    result.files.reverse();result.knowledge_graph.nodes.reverse();result.knowledge_graph.edges.reverse()
    assert asdict(data)==asdict(reconstruct(result))
    result.knowledge_graph.nodes.reverse();result.knowledge_graph.edges.reverse()
    assert before==(asdict(result.structural),asdict(result.knowledge_graph))


def test_unavailable_graph_and_empty_inventory(tmp_path):
    result=analyze(tmp_path,{})
    result.knowledge_graph=None
    data=reconstruct(result)
    assert data.summary['components']==0 and len(data.heatmap)==1
    assert next(n for n in data.heatmap if n.parent_id is None).metrics.functions is None
    assert 'graph_partial_or_unavailable' in data.coverage.issues


def test_iterative_cycles_and_nullable_combine():
    edges=[ComponentEdge('ab','a','b','IMPORTS'),ComponentEdge('ba','b','a','INCLUDES'),ComponentEdge('bc','b','c','CALLS')]
    assert strongly_connected(['a','b','c'],edges)==[['a','b']]
    combined=combine([Metrics(files=1,functions=0,hotspots=0,max_c_function_score=0,measured_files={'functions':1}),Metrics(files=1)])
    assert combined.functions==combined.hotspots==combined.max_c_function_score==0
    assert combined.measured_files['functions']==1


def test_api_export_and_real_inference(make_zip):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        response=client.post('/api/analyze',files={'file':('fixture.zip',make_zip({'a.c':'int a(void){return 1;}','src/b.py':'def b(): pass'}).getvalue())})
        assert response.status_code==200
        data=response.json()
        assert {'summary','structural','knowledge_graph','defect_risk','architecture'}<=data.keys()
        c=next(n for n in data['architecture']['heatmap'] if n['path']=='a.c')
        assert c['metrics']['max_c_function_score']==data['defect_risk']['functions'][0]['model_probability']
        assert 'architecture' in client.get('/openapi.json').json()['components']['schemas']['AnalysisResult']['properties']
        assert 'JSON.stringify(result, null, 2)' in client.get('/static/app.js').text


def test_invalid_limits_and_reused_file_identity(tmp_path):
    with pytest.raises(ValueError): replace(ARCHITECTURE_LIMITS,heat_nodes=0)
    with pytest.raises(ValueError): replace(ARCHITECTURE_LIMITS,components=-1)
    result=analyze(tmp_path,{'src/a.py':'def a(): pass'})
    data=reconstruct(result)
    assert next(n for n in data.heatmap if n.type=='file').id==result.structural.files[0].id
    assert data.components[0].function_ids==[result.structural.functions[0].id]


def test_upstream_truncation_and_missing_graph_nodes_are_explicit(tmp_path):
    result=analyze(tmp_path,{'src/a.py':'def a(): pass'})
    result.knowledge_graph.coverage.truncated=True
    result.knowledge_graph.coverage.complete=False
    result.knowledge_graph.nodes=[]
    data=reconstruct(result)
    assert data.coverage.graph_truncated
    assert 'upstream_graph_truncated' in data.coverage.issues
    assert data.coverage.retained_files==1 and data.coverage.graph_mapped_files==0

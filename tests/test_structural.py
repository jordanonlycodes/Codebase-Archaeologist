import ast
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from app.analysis.lines import measure
from app.analysis.models import FileMetrics
from app.analysis.structural import analyze_structure, link_ml_results, band
from app.analysis.structural_parsers import Budget, python_metrics
from app.config import STRUCTURAL_LIMITS, STRUCTURAL_THRESHOLDS


def analyze(tmp_path, sources, **kwargs):
    files=[]
    for path,text in sources.items():
        file=tmp_path/path
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(text)
        lang='Python' if file.suffix in {'.py','.pyi'} else 'C' if file.suffix=='.c' else 'JavaScript' if file.suffix=='.js' else 'Text'
        files.append(FileMetrics(path,lang,lang!='Text',len(text.encode()),**measure(text,lang)))
    return analyze_structure(tmp_path,files,**kwargs)


def py(source):
    function=ast.parse(source).body[0]
    return python_metrics(function,Budget(10000))


@pytest.mark.parametrize('source,complexity,loops,conditionals,depth',[
    ('def f():\n return 1',1,0,0,0),
    ('def f(x):\n if x:\n  return 1\n elif x==2:\n  return 2',3,0,2,2),
    ('def f(x):\n if x:\n  while x:\n   if x>2:\n    x-=1',4,1,2,3),
    ('def f(x):\n return 1 if x else 0',2,0,1,1),
    ('def f(a,b,c):\n return a and b or c',3,0,0,0),
    ('def f(xs):\n return [x for x in xs if x and x>0]',4,1,1,0),
    ('def f(x):\n try:\n  return x\n except ValueError:\n  return 0\n except TypeError:\n  return 1',3,0,0,2),
    ('def f(x):\n match x:\n  case 1: return 1\n  case 2 if x>0: return 2\n  case _: return 0',3,0,3,1),
    ('async def f(xs):\n async for x in xs:\n  if x: return x',3,1,1,2),
    ('def f():\n # if while and\n s="if while or"\n return s',1,0,0,0),
])
def test_python_decisions(source,complexity,loops,conditionals,depth):
    metrics=py(source)
    assert metrics['cyclomatic_complexity']==complexity
    assert metrics['decision_points']==complexity-1
    assert metrics['loop_count']==loops
    assert metrics['conditional_count']==conditionals
    assert metrics['max_nesting_depth']==depth


def test_nested_python_scopes_and_parameters(tmp_path):
    source='''class Example:
    def outer(self, a, /, b=1, *args, c=0, **kwargs):
        def inner(x):
            if x and a:
                return 1
        class Nested:
            def method(self):
                while True:
                    break
        return lambda x: x if x else b
'''
    result=analyze(tmp_path,{'a.py':source})
    funcs={f.qualified_name:f for f in result.functions}
    assert funcs['Example.outer'].cyclomatic_complexity==1
    assert funcs['Example.outer'].parameter_count==6
    assert funcs['Example.outer.inner'].cyclomatic_complexity==3
    assert funcs['Example.outer.Nested.method'].cyclomatic_complexity==2
    f=funcs['Example.outer']
    assert f.start_line==2 and f.end_line==10 and f.span_lines==9
    assert len(result.functions)==3 and result.status=='complete'


@pytest.mark.parametrize('body,cc,loops,conditionals,depth',[
    ('return 1;',1,0,0,0),
    ('if(x) return 1; else if(x>2) return 2; return 0;',3,0,2,2),
    ('for(int i=0;i<x;i++){while(x){if(x>2) break;}} return 0;',4,2,1,3),
    ('do {x--;} while(x); return 0;',2,1,0,1),
    ('return x && y || x;',3,0,0,0),
    ('return x ? y : 0;',2,0,1,1),
    ('switch(x){case 1:return 0; case 2:return 1; default:return 2;}',3,0,1,1),
    ('/* if && while */ const char *s="if && while"; return 0;',1,0,0,0),
])
def test_c_decisions(tmp_path,body,cc,loops,conditionals,depth):
    pytest.importorskip('tree_sitter')
    result=analyze(tmp_path,{'a.c':f'int f(int x,int y){{{body}}}'})
    f=result.functions[0]
    assert f.status=='analyzed'
    assert (f.cyclomatic_complexity,f.loop_count,f.conditional_count,f.max_nesting_depth)==(cc,loops,conditionals,depth)
    assert f.parameter_count==2 and f.decision_points==cc-1


def test_c_void_variadic_range(tmp_path):
    pytest.importorskip('tree_sitter')
    result=analyze(tmp_path,{'a.c':'// heading\nint first(void){\n return 0;\n}\nint next(int x, ...){return x;}\n'})
    a,b=result.functions
    assert (a.start_line,a.end_line,a.span_lines,a.parameter_count)==(2,4,3,0)
    assert b.parameter_count==1


def test_partial_c_keeps_independent_functions(tmp_path):
    pytest.importorskip('tree_sitter')
    result=analyze(tmp_path,{'a.c':'int good(void){return 0;}\nint bad(void){return +;}\nint broken( {'})
    assert result.status=='partial' and result.coverage.partial_files==1
    assert any(f.name=='good' and f.cyclomatic_complexity==1 for f in result.functions)
    assert any(f.name=='bad' and f.cyclomatic_complexity is None for f in result.functions)
    assert result.composition.status=='unavailable'


def test_composition_mixed_inline_multiline(tmp_path):
    pytest.importorskip('tree_sitter')
    sources={'a.c':'/* block\n * comment\n */\n\nint f(void){ // inline\n return 1; /* mixed */\n}\n',
             'b.py':'# comment\n\ndef f():\n """docstring"""\n return 1 # inline\n'}
    result=analyze(tmp_path,sources)
    a,b=[f.composition for f in result.files]
    assert (a.physical_lines,a.blank_lines,a.comment_lines,a.code_lines)==(7,1,3,3)
    assert (b.physical_lines,b.blank_lines,b.comment_lines,b.code_lines)==(5,1,1,3)
    assert a.comment_density==.5
    for c in [a,b,result.composition]:
        assert c.physical_lines==c.blank_lines+c.comment_lines+c.code_lines


@pytest.mark.parametrize('sources,status',[
    ({'a.py':''},'no_functions'),({'a.py':'x=1'},'no_functions'),
    ({'a.js':'function f(){}'},'no_supported_files'),({'a.py':'def f(:'},'partial'),
])
def test_empty_unsupported_malformed(tmp_path,sources,status):
    result=analyze(tmp_path,sources)
    assert result.status==status and not result.functions
    assert result.summary.average_complexity is None
    assert result.summary.maximum_complexity is None
    assert result.summary.total_complexity is None


def test_aggregation_hotspots_coverage_ids(tmp_path):
    result=analyze(tmp_path,{'b.py':'def z(a,b,c,d,e,f):\n return 1','a.py':'def f(x):\n if x:\n  if x>1:\n   return 1\n return 0','a.js':'const x=1;'})
    assert result.summary.analyzed_functions==2
    assert result.summary.average_complexity==2 and result.summary.total_complexity==4
    assert result.summary.maximum_complexity==3 and result.summary.maximum_nesting==2
    assert result.summary.complexity_bands['low']==2
    assert result.coverage.unsupported_files==1 and not result.coverage.complete
    assert result.status=='partial'
    assert len(result.hotspots)==1
    assert result.hotspots[0].name=='z' and result.hotspots[0].reasons[0].threshold==6
    second=analyze(tmp_path,{'b.py':'def z(a,b,c,d,e,f):\n return 1','a.js':'const x=1;','a.py':'def f(x):\n if x:\n  if x>1:\n   return 1\n return 0'})
    assert asdict(result)==asdict(second)
    assert len({f.id for f in result.functions})==2
    assert result.files[0].id!=result.files[1].id
    assert result.files[0].composition.comment_lines is None  # JavaScript unavailable
    assert result.coverage.composition_files==2


@pytest.mark.parametrize('limits',[
    replace(STRUCTURAL_LIMITS,file_bytes=5),replace(STRUCTURAL_LIMITS,total_bytes=5),
    replace(STRUCTURAL_LIMITS,functions=1),replace(STRUCTURAL_LIMITS,nodes_per_file=2),
    replace(STRUCTURAL_LIMITS,total_nodes=2),replace(STRUCTURAL_LIMITS,function_bytes=5),
])
def test_resource_limits(tmp_path,limits):
    result=analyze(tmp_path,{'a.py':'def a():\n return 1\ndef b():\n return 2'},limits=limits)
    assert result.status=='partial' and result.coverage.truncated
    assert len(result.functions)<=limits.functions
    assert result.coverage.visited_nodes<=limits.total_nodes


def test_hotspot_order_thresholds(tmp_path):
    thresholds=replace(STRUCTURAL_THRESHOLDS,high_complexity=2,large_span=2,deep_nesting=1)
    result=analyze(tmp_path,{'b.py':'def b(x):\n if x:return 1','a.py':'def a(x):\n if x:\n  if x>2:return 1'},thresholds=thresholds)
    assert [h.path for h in result.hotspots]==['a.py','b.py']
    assert len(result.hotspots[0].reasons)==3
    assert result.summary.high_complexity_functions==2
    assert result.summary.large_functions==2
    assert result.summary.deeply_nested_functions==2


@pytest.mark.parametrize('cc,label',[(1,'low'),(5,'low'),(6,'moderate'),(10,'moderate'),(11,'high'),(20,'high'),(21,'very_high')])
def test_bands(cc,label): assert band(cc)==label


def test_model_unavailable_still_structural(tmp_path,monkeypatch):
    from app.ml.repository import ModelService,analyze_functions
    pytest.importorskip('tree_sitter')
    sources={'a.c':'int f(void){return 0;}', 'b.py':'def f():\n return 0'}
    result=analyze(tmp_path,sources)
    files=[FileMetrics(p,'C' if p.endswith('.c') else 'Python',True,len(s.encode()),**measure(s,'C' if p.endswith('.c') else 'Python')) for p,s in sources.items()]
    risk=analyze_functions(tmp_path,files,ModelService(tmp_path/'missing'))
    link_ml_results(result,risk)
    assert result.summary.analyzed_functions==2
    assert all(f.ml_status=='unavailable' for f in result.functions)


def test_c_tree_reuse_preserves_ml_output(tmp_path):
    pytest.importorskip('tree_sitter')
    from app.ml.repository import ModelService,analyze_functions
    source='int a(int x){if(x) return 1; return 0;}'
    cache={}
    structure=analyze(tmp_path,{'a.c':source},parsed_files=cache)
    file=FileMetrics('a.c','C',True,len(source),**measure(source,'C'))
    model=ModelService()
    if model.load() is None: pytest.skip('Compatible local model unavailable')
    original=analyze_functions(tmp_path,[file],model)
    reused=analyze_functions(tmp_path,[file],model,parsed_files=cache)
    assert asdict(original)==asdict(reused)
    link_ml_results(structure,reused)
    assert structure.functions[0].ml_result_index==0
    assert structure.functions[0].ml_status=='analyzed'


def test_zip_api_structure_and_export(make_zip,monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.ml.repository import ModelService
    monkeypatch.setattr('app.ml.repository.SERVICE',ModelService(tmp_path/'missing'))
    with TestClient(app) as client:
        response=client.post('/api/analyze',files={'file':('mixed.zip',make_zip({'a.py':'def f(x):\n if x:return 1','a.c':'int c(void){return 0;}','a.js':'let a=1;'}))})
        assert response.status_code==200,response.text
        data=response.json()
        assert data['summary']['files']==3 and data['source']['type']=='zip'
        assert data['structural']['summary']['analyzed_functions']==2
        assert data['structural']['coverage']['unsupported_files']==1
        assert data['defect_risk']['status']=='unavailable'
        assert '/tmp/' not in response.text
        assert 'structural' in client.get('/openapi.json').json()['components']['schemas']['AnalysisResult']['properties']
        assert 'Structural Intelligence' in client.get('/').text
        assert 'JSON.stringify(result, null, 2)' in client.get('/static/app.js').text


def test_composition_unicode_blank_inside_comment(tmp_path):
    pytest.importorskip('tree_sitter')
    result=analyze(tmp_path,{'a.c':'/*\n\u00a0\n*/\nint x;\n'})
    c=result.composition
    assert c.physical_lines==4 and c.blank_lines==1 and c.comment_lines==2 and c.code_lines==1


def test_c_missing_parser_does_not_break_python(tmp_path,monkeypatch):
    def unavailable(*args): raise ImportError('no parser')
    monkeypatch.setattr('app.analysis.structural.parse_c',unavailable)
    result=analyze(tmp_path,{'a.c':'int x;','b.py':'def a():\n return 1'})
    assert result.summary.analyzed_functions==1 and result.coverage.skipped_files==1
    assert result.files[0].reasons==['parser_unavailable']


def test_nested_depth_and_large_span_actual_thresholds(tmp_path):
    source='def large(x):\n if x:\n  if x>1:\n   if x>2:\n    if x>3:\n     return 1\n'+' # padding\n'*75+' return 0\n'
    result=analyze(tmp_path,{'a.py':source})
    assert result.summary.large_functions==1 and result.summary.deeply_nested_functions==1
    assert result.functions[0].max_nesting_depth==4
    assert {r.metric for r in result.hotspots[0].reasons}=={'span_lines','max_nesting_depth'}


def test_ml_link_is_not_name_only(tmp_path):
    from app.ml.schemas import DefectRisk,FunctionResult
    result=analyze(tmp_path,{'a.py':'def f():\n return 0'})
    risk=DefectRisk('ready','test',functions=[FunctionResult('f','a.py',1,2,'analyzed')])
    link_ml_results(result,risk)
    assert result.functions[0].ml_result_index is None
    result.functions[0].language='C'
    risk.functions[0].path='other.c'
    link_ml_results(result,risk)
    assert result.functions[0].ml_result_index is None
    risk.functions[0].path='a.py'
    risk.functions.append(risk.functions[0])
    link_ml_results(result,risk)
    assert result.functions[0].ml_result_index is None


def test_repeated_symbols_have_unique_ids(tmp_path):
    result=analyze(tmp_path,{'a.py':'def f():\n return 1\ndef f():\n return 2','b.py':'def f():\n return 1'})
    assert len({f.id for f in result.functions})==3


def test_cached_c_tree_skips_full_file_reparse(tmp_path,monkeypatch):
    pytest.importorskip('tree_sitter')
    from app.ml.repository import function_nodes
    cache={}
    analyze(tmp_path,{'a.c':'int f(void){return 0;}'},parsed_files=cache)
    data,root=cache['a.c']
    import tree_sitter
    def no_parser(*args): pytest.fail('Full file parsed twice')
    monkeypatch.setattr(tree_sitter,'Parser',no_parser)
    error,definitions=function_nodes(data,root)
    assert not error and len(list(definitions))==1


def test_partial_composition_totals_use_covered_files_only(tmp_path):
    result=analyze(tmp_path,{'a.py':'# comment\n\ndef a():\n return 1','a.js':'// unknown\nconst a=1;'})
    composition=result.composition
    assert composition.status=='partial'
    assert composition.physical_lines==4
    assert composition.physical_lines==composition.blank_lines+composition.comment_lines+composition.code_lines
    assert result.coverage.composition_physical_lines==4

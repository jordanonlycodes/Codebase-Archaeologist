#!/usr/bin/env python3
"""Build a verified source snapshot and explicitly gated final or candidate package."""
from pathlib import Path,PurePosixPath
from io import BytesIO
import argparse,hashlib,json,shutil,subprocess,tarfile,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
APPROVED_MODEL='models/devign-v1/pipeline.joblib'
APPROVED_SHA='9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6'
MODEL_FILES=('pipeline.joblib','metadata.json','feature_schema.json','manifest.json','C-UDA-1.0.md','README.md')
BLOCKERS=['Final acceptance has not been explicitly requested and validated.']
GRAPH_FILES=('app/static/vendor/3d-force-graph-1.73.3.min.js','app/static/vendor/3d-force-graph-1.73.3.LICENSE','app/static/vendor/graph-assets.json')
def reviewed_graph_allowed(name):
    if name not in GRAPH_FILES:return False
    import importlib.util
    spec=importlib.util.spec_from_file_location('verified_graph',ROOT/'tools/verify_vendor_assets.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.inspect()['redistribution_approved']

def sha(data):return hashlib.sha256(data).hexdigest()
def safe_name(name):
    p=PurePosixPath(name)
    return bool(p.parts) and name==p.as_posix() and not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name and not any(ord(c)<32 for c in name)
def source_allowed(name):
    if not safe_name(name):return False
    p=PurePosixPath(name)
    if any(part in {'.git','.venv','__pycache__','.pytest_cache','secrets','.secrets','data','datasets','artifacts','checkpoints'} for part in p.parts):return False
    if name.startswith(('submission/final/','app/static/vendor/')):return False
    if any(part.startswith('.env') for part in p.parts):return False
    if p.suffix in {'.zip','.pyc','.parquet','.npy','.npz','.pem','.key','.p12','.pfx','.pickle','.pkl','.pt','.pth','.onnx','.safetensors'}:return False
    if p.suffix=='.joblib':return name==APPROVED_MODEL
    return True

def write_zip(path,entries):
    seen=set();total=0
    for name,data in entries:
        if not safe_name(name) or name in seen:raise ValueError('Unsafe/duplicate archive entry')
        seen.add(name);total+=len(data)
        if len(data)>20*1024*1024 or total>80*1024*1024:raise ValueError('Release archive budget exceeded')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(entries):
            info=zipfile.ZipInfo(name,(2026,11,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:raise ValueError('Archive CRC failure')

def inventory(directory):
    return {p.relative_to(directory).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(directory.rglob('*')) if p.is_file()}
def verify_inventory(directory,records):
    for name,record in records.items():
        if not safe_name(name):raise ValueError('Unsafe manifest path')
        p=directory/name
        if not p.is_file() or p.is_symlink() or p.stat().st_size!=record['bytes'] or sha(p.read_bytes())!=record['sha256']:
            raise ValueError('Release payload changed: '+name)

def require_final_acceptance(commit):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location('verified_graph',ROOT/'tools/verify_vendor_assets.py')
    m=module_from_spec(spec);spec.loader.exec_module(m)
    if not m.inspect()['redistribution_approved']:raise ValueError('Offline3D evidence not accepted')
    shots=json.loads((ROOT/'submission/screenshots.json').read_text())
    if len(shots)!=3 or not all(e.get('verified') and sha((ROOT/e['path']).read_bytes())==e.get('sha256') for e in shots):raise ValueError('Screenshot acceptance incomplete')
    layout=json.loads((ROOT/'reports/release/task7e/layout.json').read_text())
    if not layout.get('visual_reviewed') or layout.get('libreoffice_exit')!=0:raise ValueError('Office layout acceptance incomplete')
    for name,expected in layout['canonical_outputs'].items():
        if sha((ROOT/'submission'/name).read_bytes())!=expected:raise ValueError('Office/report acceptance is stale')
    checks=json.loads((ROOT/'submission/release_checks.json').read_text())
    acceptance=checks.get('task7e_acceptance',{})
    if not (acceptance.get('clean_source_commit')==commit and acceptance.get('clean_source_smoke') and acceptance.get('offline_3d_browser') and acceptance.get('published_source_commit')==commit):raise ValueError('Clean source/browser/publication acceptance incomplete')
    if checks.get('full_regression',{}).get('failed')!=0 or checks.get('full_regression',{}).get('passed',0)<540:raise ValueError('Regression acceptance incomplete')
    if not json.loads((ROOT/'submission/academic_details.json').read_text()).get('evaluation_protocol_confirmation'):raise ValueError('Academic protocol confirmation missing')

def build(destination=None, final=False):
    destination=Path(destination or ROOT/'submission/final');destination.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if final:require_final_acceptance(commit)
    status='FINAL — verified submission' if final else 'PARTIAL — submission candidate'
    blockers=[] if final else BLOCKERS
    archive_name='Codebase_Archaeologist_Submission.zip' if final else 'Codebase_Archaeologist_Submission_Candidate.zip'
    tarbytes=subprocess.check_output(['git','archive',commit],cwd=ROOT)
    if len(tarbytes)>80*1024*1024:raise ValueError('Source archive budget exceeded')
    entries=[]
    with tarfile.open(fileobj=BytesIO(tarbytes),mode='r:') as archive:
        for member in archive:
            if member.isdir() or not (source_allowed(member.name) or reviewed_graph_allowed(member.name)):continue
            if not member.isfile() or member.size>20*1024*1024:raise ValueError('Unsafe source member')
            entries.append((member.name,archive.extractfile(member).read()))
    if APPROVED_MODEL not in {n for n,_ in entries}:raise ValueError('Approved model must be committed before packaging')
    if sha(dict(entries)[APPROVED_MODEL])!=APPROVED_SHA:raise ValueError('Committed model is not approved')
    packaged=json.loads((ROOT/'models/devign-v1/manifest.json').read_text())
    for name,record in packaged['files'].items():
        if name not in MODEL_FILES:raise ValueError('Unexpected model member')
        data=(ROOT/'models/devign-v1'/name).read_bytes()
        if sha(data)!=record['sha256'] or len(data)!=record['bytes']:raise ValueError('Packaged model changed')
    if sha((ROOT/APPROVED_MODEL).read_bytes())!=APPROVED_SHA:raise ValueError('Working model is not approved')
    for name in GRAPH_FILES:
        if dict(entries).get(name)!=(ROOT/name).read_bytes():raise ValueError('Reviewed graph assets must be committed and match evidence')
    write_zip(destination/'source.zip',entries)
    payload=destination/'payload'
    # Only overwrite our explicitly generated payload names; never recursively delete user data.
    payload.mkdir(exist_ok=True)
    copies={'Codebase_Archaeologist_Report.docx':'submission/Codebase_Archaeologist_Report.docx','Codebase_Archaeologist_Report.pdf':'submission/Codebase_Archaeologist_Report.pdf','SETUP.md':'README.md','DEMO.md':'docs/task7d_demo_guide.md','THIRD_PARTY_NOTICES.md':'THIRD_PARTY_NOTICES.md','academic_details.json':'submission/academic_details.json','verification.json':'submission/release_checks.json'}
    for output,source in copies.items():shutil.copyfile(ROOT/source,payload/output)
    for name in MODEL_FILES:
        source=ROOT/'models/devign-v1'/name
        if source.is_file():
            target=payload/'models/devign-v1'/source.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    release_assets=list(GRAPH_FILES)+['third_party/graph/LICENSES.txt','third_party/graph/provenance.json','third_party/graph/upstream-yarn.lock']+[e['path'] for e in json.loads((ROOT/'submission/screenshots.json').read_text()) if e.get('verified')]
    for name in ['app/static/product/fonts/OFL.txt','third_party/DejaVu-LICENSE.txt']+release_assets:
        target=payload/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    (payload/'SOURCE.txt').write_text(f'https://github.com/jordanonlycodes/Codebase-Archaeologist\nCommitted source:{commit}\nUse accompanying source.zip for offline source delivery; upstream publication is separately checked against remote HEAD.\n')
    (payload/'STATUS.md').write_text('# '+status+'\n\n'+'\n'.join('- '+b for b in blockers)+'\n\nAcademic details are explicitly confirmed. Verified browser captures and isolated LibreOffice layout evidence are documented in Task7E.\n')
    # Reject unexpected existing payload files instead of silently shipping private leftovers.
    expected=set(copies)|{'SOURCE.txt','STATUS.md'}
    expected|={f'models/devign-v1/{name}' for name in MODEL_FILES}
    expected|={'app/static/product/fonts/OFL.txt','third_party/DejaVu-LICENSE.txt'}|set(release_assets)
    records=inventory(payload)
    records.pop('MANIFEST.json',None)  # This generated receipt is replaced on explicit rebuild.
    if set(records)!=expected:raise ValueError('Unexpected payload files; inspect without deleting user data')
    verify_inventory(payload,records)
    pm={'status':status,'source_commit':commit,'authors':json.loads((ROOT/'submission/academic_details.json').read_text())['authors'],'files':records,'remaining_actions':blockers}
    (payload/'MANIFEST.json').write_text(json.dumps(pm,indent=2)+'\n')
    write_zip(destination/archive_name,[(p.relative_to(payload).as_posix(),p.read_bytes()) for p in payload.rglob('*') if p.is_file()])
    with tempfile.TemporaryDirectory(prefix='submission-verify-') as temporary:
        with zipfile.ZipFile(destination/archive_name) as archive:
            for name in archive.namelist():
                if not safe_name(name):raise ValueError('Unsafe packaged path')
                target=Path(temporary)/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(name))
        verify_inventory(Path(temporary),records)
    outer={'status':status,'source_commit':commit,'files':{name:{'bytes':(destination/name).stat().st_size,'sha256':sha((destination/name).read_bytes())} for name in ['source.zip',archive_name]},'payload':records,'remaining_actions':blockers,'generation_date':'23 November 2026','archive_crc_and_extracted_payload_verified':True}
    (destination/'manifest.json').write_text(json.dumps(outer,indent=2)+'\n')
    (destination/'README.md').write_text('# '+status+'\n\nBoth authors/confirmed academic fields are in the payload. Deliver both ZIPs and manifest.json.\nsource.zip is the exact committed-source delivery; publication is checked separately.\nSubmission ZIP includes reports, exact model, offline3D, real screenshots, setup/demo, notices and checksums.\n\n'+'\n'.join('- '+b for b in blockers)+'\n')
    return outer
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path);parser.add_argument('--final',action='store_true');args=parser.parse_args()
    result=build(args.destination,final=args.final);print(json.dumps({k:v for k,v in result.items() if k!='payload'},indent=2))

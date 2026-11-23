#!/usr/bin/env python3
"""Build a clearly PARTIAL submission candidate plus a clean committed-source archive."""
from pathlib import Path,PurePosixPath
from io import BytesIO
import argparse,hashlib,json,shutil,subprocess,tarfile,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
APPROVED_MODEL='models/devign-v1/pipeline.joblib'
APPROVED_SHA='9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6'
MODEL_FILES=('pipeline.joblib','metadata.json','feature_schema.json','manifest.json','C-UDA-1.0.md','README.md')
BLOCKERS=['Genuine application screenshots not captured/integrated','Local Office layout and physical browser/demo acceptance pending','Portable offline3D redistribution provenance unresolved','GitHub publication pending verification','Instructor interpretation of final-test-for-every-candidate wording needs clarification']
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

def build(destination=None):
    destination=Path(destination or ROOT/'submission/final');destination.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    tarbytes=subprocess.check_output(['git','archive',commit],cwd=ROOT)
    if len(tarbytes)>80*1024*1024:raise ValueError('Source archive budget exceeded')
    entries=[]
    with tarfile.open(fileobj=BytesIO(tarbytes),mode='r:') as archive:
        for member in archive:
            if member.isdir() or not source_allowed(member.name):continue
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
    for name in ['app/static/product/fonts/OFL.txt','third_party/DejaVu-LICENSE.txt']:
        target=payload/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    (payload/'SOURCE.txt').write_text(f'https://github.com/jordanonlycodes/Codebase-Archaeologist\nCommitted source:{commit}\nUse accompanying source.zip for offline source delivery; upstream publication remains separately verified.\n')
    (payload/'STATUS.md').write_text('# SUBMISSION CANDIDATE — PARTIALLY COMPLETED\n\n'+'\n'.join('- '+b for b in BLOCKERS)+'\n\nAcademic details are explicitly confirmed. No screenshot or Office acceptance is fabricated.\n')
    # Reject unexpected existing payload files instead of silently shipping private leftovers.
    expected=set(copies)|{'SOURCE.txt','STATUS.md'}
    expected|={f'models/devign-v1/{name}' for name in MODEL_FILES}
    expected|={'app/static/product/fonts/OFL.txt','third_party/DejaVu-LICENSE.txt'}
    records=inventory(payload)
    records.pop('MANIFEST.json',None)  # This generated receipt is replaced on explicit rebuild.
    if set(records)!=expected:raise ValueError('Unexpected payload files; inspect without deleting user data')
    verify_inventory(payload,records)
    pm={'status':'PARTIAL — submission candidate','source_commit':commit,'authors':json.loads((ROOT/'submission/academic_details.json').read_text())['authors'],'files':records,'remaining_actions':BLOCKERS}
    (payload/'MANIFEST.json').write_text(json.dumps(pm,indent=2)+'\n')
    write_zip(destination/'Codebase_Archaeologist_Submission_Candidate.zip',[(p.relative_to(payload).as_posix(),p.read_bytes()) for p in payload.rglob('*') if p.is_file()])
    with tempfile.TemporaryDirectory(prefix='submission-verify-') as temporary:
        with zipfile.ZipFile(destination/'Codebase_Archaeologist_Submission_Candidate.zip') as archive:
            for name in archive.namelist():
                if not safe_name(name):raise ValueError('Unsafe packaged path')
                target=Path(temporary)/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(name))
        verify_inventory(Path(temporary),records)
    outer={'status':'PARTIAL — submission candidate','source_commit':commit,'files':{name:{'bytes':(destination/name).stat().st_size,'sha256':sha((destination/name).read_bytes())} for name in ['source.zip','Codebase_Archaeologist_Submission_Candidate.zip']},'payload':records,'remaining_actions':BLOCKERS,'generation_date':'23 November 2026','archive_crc_and_extracted_payload_verified':True}
    (destination/'manifest.json').write_text(json.dumps(outer,indent=2)+'\n')
    (destination/'README.md').write_text('# Submission candidate — NOT unconditional final acceptance\n\nBoth authors/confirmed academic fields are in the payload. Deliver both ZIPs and manifest.json.\nsource.zip is a clean committed-source fallback while GitHub publication is pending.\nCandidate ZIP includes reports, exact model, setup/demo, notices and checksums.\n\n'+'\n'.join('- '+b for b in BLOCKERS)+'\n')
    return outer
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path);args=parser.parse_args()
    result=build(args.destination);print(json.dumps({k:v for k,v in result.items() if k!='payload'},indent=2))

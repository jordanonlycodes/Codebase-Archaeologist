#!/usr/bin/env python3
"""Recover reviewed upstream notices from fixed release evidence; no npm execution.
Explicit networked maintainer command, not application startup. Downloads only fixed
npm/GitHub destinations, verifies source-lock and package-integrity hashes.
"""
import re,shlex,json,urllib.request,tarfile,io,hashlib,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import os
os.chdir(ROOT)
def download(url):
 with urllib.request.urlopen(url,timeout=30) as response:data=response.read(20*1024*1024+1)
 if len(data)>20*1024*1024:raise ValueError('Evidence download exceeds limit')
 return data
lock=download('https://raw.githubusercontent.com/vasturiano/3d-force-graph/9806444ee2af34a0a45ecc8ea035ec9efa929d54/yarn.lock').decode()
assert hashlib.sha256(lock.encode()).hexdigest()=='27cacfcd6475eea96350f5423e14b49626192db2ca497876511d41f015017773'
entries={};current=None
for line in lock.splitlines():
 if line and not line.startswith((' ','#')) and line.endswith(':'):
  current={'dependencies':{}}
  for key in re.findall(r'"([^"]+)"|([^, ]+)',line[:-1]):
   k=key[0] or key[1];entries[k]=current
 elif current is not None:
  m=re.match(r'^  (version|integrity) "?([^"\n]+)"?$',line)
  if m:current[m[1]]=m[2]
  if line.startswith('    ') and not line.startswith('      '):
   parts=shlex.split(line.strip())
   if len(parts)==2:current['dependencies'][parts[0]]=parts[1]
package=json.loads(download('https://registry.npmjs.org/3d-force-graph/1.73.3'));assert package['gitHead']=='9806444ee2af34a0a45ecc8ea035ec9efa929d54';todo=list(package['dependencies'].items());seen={}
while todo:
 name,version=todo.pop();record=entries[name+'@'+version];key=name+'@'+record['version']
 if key in seen:continue
 seen[key]={'name':name,**record};todo.extend(record['dependencies'].items())
print('runtime packages',len(seen))
# Babel helper code can be emitted by the source build: retain its MIT notice too.
for key in ['@babel/helpers@^7.24.1','@babel/core@^7.24.3']:
 if key in entries:
  e=entries[key];name=key[:key.rfind('@')];seen[name+'@'+e['version']]={'name':name,**e}
out=Path('third_party/graph');out.mkdir(parents=True,exist_ok=True);(out/'upstream-yarn.lock').write_text(lock)
receipts=[];texts=[]
for key,r in sorted(seen.items()):
 name,version=r['name'],r['version'];url=f'https://registry.npmjs.org/{name}/-/{name.split("/")[-1]}-{version}.tgz'
 with urllib.request.urlopen(url,timeout=25) as response:data=response.read(20*1024*1024+1)
 assert len(data)<=20*1024*1024
 integrity=r.get('integrity');alg,expected=integrity.split('-',1)
 assert base64.b64encode(hashlib.new(alg,data).digest()).decode()==expected,key
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
  meta=json.load(tar.extractfile('package/package.json'));assert meta['name']==name and meta['version']==version
  licenses=[]
  for member in tar.getmembers():
   if member.isfile() and len(member.name.split('/'))==2 and re.match(r'(?i)^(license|licence|copying|notice)(\.|$)',member.name.split('/')[-1]):
    assert member.size<100000;licenses.append((member.name,tar.extractfile(member).read().decode('utf8','replace')))
  assert licenses,(key,'Missing license')
  assert meta.get('license') in ['MIT','ISC','BSD-3-Clause','BSD-2-Clause'],(key,meta.get('license'))
  texts.append('\n\n'+'='*72+'\n'+key+' — '+str(meta.get('license'))+'\n'+url+'\n'+'\n'.join(t for _,t in licenses))
 receipts.append({'package':name,'version':version,'license':meta.get('license'),'url':url,'sha256':hashlib.sha256(data).hexdigest(),'integrity':integrity,'license_members':[n for n,_ in licenses]})
 print(key,meta.get('license'))
(out/'LICENSES.txt').write_text('Conservative runtime dependency and emitted Babel helper notices. Upstream source lock; not a claim every module survives tree-shaking.\n'+''.join(texts))
(out/'provenance.json').write_text(json.dumps({'upstream_commit':package['gitHead'],'source_lock_sha256':hashlib.sha256(lock.encode()).hexdigest(),'packages':receipts},indent=2)+'\n')

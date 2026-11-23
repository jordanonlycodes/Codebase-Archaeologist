#!/usr/bin/env python3
"""Check local Markdown report links and configured figure/screenshot paths offline."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]
def main():
    files=list((ROOT/'docs').glob('task7c*.md'))+list((ROOT/'docs').glob('task7d*.md'))+list((ROOT/'docs').glob('task7e*.md'))+[ROOT/'README.md',ROOT/'submission/README.md']
    checked=0;failures=[]
    for file in files:
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text()):
            target=target.strip('<>').split('#',1)[0]
            if not target or '://' in target or target.startswith('mailto:'):continue
            checked+=1
            path=(file.parent/target).resolve()
            if not path.is_relative_to(ROOT) or not path.exists():failures.append([str(file.relative_to(ROOT)),target])
    manifest=json.loads((ROOT/'submission/report_manifest.json').read_text())
    for entry in manifest['figure_index']:
        checked+=1
        if not (ROOT/entry['path']).is_file():failures.append(entry['path'])
    for entry in json.loads((ROOT/'submission/screenshots.json').read_text()):
        path=(ROOT/entry['path']).resolve()
        assert path.is_relative_to(ROOT/'docs/screenshots')
        if entry.get('verified'):
            checked+=1
            if not path.is_file():failures.append(entry['path'])
    assert not failures,failures
    print(json.dumps({'local_links_and_figures_checked':checked,'missing':failures,'external_references':'Primary-source metadata inspected separately; no network request in this checker.'},indent=2))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Original tiny multi-directory fixture for real browser dependency checks, not ML evaluation."""
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
def create(path):
    members={'src/review.c':(ROOT/'tests/fixtures/university_demo/review.c').read_bytes(),'core/helpers.py':(ROOT/'tests/fixtures/university_demo/helpers.py').read_bytes(),'ui/main.py':b'from core.helpers import describe_count\n\ndef render_count(value):\n    return describe_count(value)\n'}
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,data in sorted(members.items()):
            info=ZipInfo(name,(2026,11,23,0,0,0));info.compress_type=ZIP_DEFLATED;z.writestr(info,data)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);args=p.parse_args();create(args.output)

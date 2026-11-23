#!/usr/bin/env python3
"""Original browser fixture: real mixed source, nested directory and functionless file."""
from pathlib import Path
from zipfile import ZipFile
from create_acceptance_fixture import create


def build(path):
    create(path)
    with ZipFile(path,'a') as archive:
        archive.writestr('README.md','Original Codebase Archaeologist X-Ray browser fixture.\n')
        archive.writestr('src/nested/architecture_investigation_with_a_deliberately_long_directory_name_for_responsive_acceptance/empty.py','# Original functionless source for empty-state acceptance.\n')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    build(parser.parse_args().output)

#!/usr/bin/env python3
"""Check report structure, exact metrics, shared text and PDF text bounds.

Requires Poppler's pdftotext/pdfinfo, plus only Python's standard library.
Visual inspection is a separate manual step; this script does not claim it.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def compact(text):
    return re.sub(r'\s+', '', text)


def main():
    docx = OUT / 'Codebase_Archaeologist_Report.docx'
    pdf = OUT / 'Codebase_Archaeologist_Report.pdf'
    manifest = json.loads((OUT / 'report_manifest.json').read_text())
    for name, expected in manifest['outputs_sha256'].items():
        assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == expected, name
    for name, expected in manifest['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    with zipfile.ZipFile(docx) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith(('.xml', '.rels')):
                ET.fromstring(z.read(name))
        document = ET.fromstring(z.read('word/document.xml'))
        core = ET.fromstring(z.read('docProps/core.xml'))
        assert core.find('{http://purl.org/dc/elements/1.1/}creator').text == 'Bilal Malik'
        assert core.find('{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}lastModifiedBy').text == 'Bilal Malik'
        paragraphs = [''.join(n.text or '' for n in p.findall('.//w:t', NS))
                      for p in document.findall('.//w:p', NS)]
        word_text = ' '.join(paragraphs)
        images = [n for n in z.namelist() if n.startswith('word/media/')]
        assert len(images) == manifest['figures'] == 9
        rels = ET.fromstring(z.read('word/_rels/document.xml.rels'))
        for rel in rels:
            assert 'word/' + rel.attrib['Target'] in z.namelist()
        assert len(word_text.split()) > 5000
        footer_text = z.read('word/footer1.xml').decode()
        assert 'BILAL MALIK' in footer_text and '24P-3061' in footer_text
    with TemporaryDirectory(prefix='archaeologist-report-qa-') as temporary:
        textfile = Path(temporary) / 'report.txt'
        bbox = Path(temporary) / 'bbox.html'
        subprocess.run(['pdftotext', '-layout', str(pdf), str(textfile)], check=True)
        subprocess.run(['pdftotext', '-bbox', str(pdf), str(bbox)], check=True)
        pdf_text = textfile.read_text()
        pdf_info = subprocess.run(['pdfinfo', str(pdf)], check=True, capture_output=True, text=True).stdout
        assert 'Author:          Bilal Malik' in pdf_info
        pages = [p for p in pdf_text.split('\f') if p.strip()]
        assert len(pages) == manifest['pdf_pages'] == 28
        assert all(len(p.split()) >= 40 for p in pages)
        tree = ET.parse(bbox)
        clipped = []
        for pi, p in enumerate(tree.findall('.//{*}page'), start=1):
            width, height = float(p.attrib['width']), float(p.attrib['height'])
            for word in p.findall('.//{*}word'):
                a = word.attrib
                if float(a['xMin']) < 0 or float(a['yMin']) < 0 or float(a['xMax']) > width or float(a['yMax']) > height:
                    clipped.append((pi, word.text))
        assert not clipped, clipped
    for text in (word_text, pdf_text):
        for expected in ('Bilal Malik', '24P-3061', 'Software Engineering (SE)', 'Class 5A', 'FAST-NUCES, Peshawar'):
            assert expected in text, expected
        for old in ('Muhammad Ali Jamshed', '24P-0002', 'BAI-5A', 'Department of Artificial Intelligence'):
            assert old not in text, old
    for file in ('model_comparison.json', 'test_evaluation.json'):
        evidence = json.loads((ROOT / 'reports/ml' / file).read_text())
        groups = [v['validation'] for v in evidence.values()] if file.startswith('model_comparison') else [evidence['metrics']]
        for group in groups:
            for metric in ('accuracy', 'precision', 'recall', 'f1', 'roc_auc'):
                assert str(group[metric]) in compact(pdf_text)
                assert str(group[metric]) in word_text
    # Every substantive DOCX paragraph must appear in the PDF. Cover typography
    # and its combined institution/year line intentionally differ in layout.
    missing = [p for p in paragraphs if len(p) > 100 and compact(p) not in compact(pdf_text)]
    assert not missing, missing
    sections = ['Abstract', 'Introduction', 'Problem Statement', 'Project Objectives',
                'Dataset Description', 'Data Preprocessing', 'Exploratory Data Analysis',
                'Feature Engineering', 'Models and Training', 'Model Evaluation and Comparison',
                'Selected Model', 'System Architecture', 'Web Application Implementation',
                'Testing and Validation', 'Limitations', 'Future Enhancements', 'Conclusion', 'References']
    assert all(s in word_text and s in pdf_text for s in sections)
    results = {'pdf_pages': len(pages), 'required_sections_including_cover': 19,
               'figures': len(images), 'docx_words': len(word_text.split()),
               'exact_saved_metrics_in_both_documents': True,
               'shared_substantive_paragraphs_match': True,
               'docx_xml_and_relationships_valid': True,
               'student_identity_and_metadata_valid': True,
               'pdf_text_outside_page': clipped,
               'empty_pdf_pages': 0,
               'evidence_and_output_checksums_valid': True,
               'visual_checks': 'Separate manual rendering review; not asserted by this script.',
               'docx_pagination': 'Not visually verified: LibreOffice conversion unavailable in sandbox.'}
    (OUT / 'validation.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()

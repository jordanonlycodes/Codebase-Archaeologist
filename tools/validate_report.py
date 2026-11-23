#!/usr/bin/env python3
"""Validate actual shared report evidence, editable OOXML and fixed-layout PDF.
No fitting/inference. Poppler is required; visual inspection is separate.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,json,re,subprocess,zipfile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'submission'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def compact(text):return re.sub(r'\s+','',text).replace('−','-').replace('–','-').replace('—','-')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked_sources(manifest):
    """Never substitute a digest for a missing/superseded file."""
    for name,expected in manifest['source_sha256'].items():
        path=(ROOT/name).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(),name
        assert sha(path)==expected, f'Source changed; review content and regenerate: {name}'
    assert 'app/static/app.js' not in manifest['source_sha256']
    assert 'app/templates/dashboard.html' not in manifest['source_sha256']
    for current in ['app/static/product/workspace.js','app/templates/workspace.html','app/routes/analysis.py','tools/report_content.py']:
        assert current in manifest['source_sha256'],current

def document_text(docx):
    with zipfile.ZipFile(docx) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith(('.xml','.rels')):ET.fromstring(z.read(name))
        document=ET.fromstring(z.read('word/document.xml'))
        core=ET.fromstring(z.read('docProps/core.xml'))
        authors='Bilal Malik; Aun Anis'
        assert core.find('{http://purl.org/dc/elements/1.1/}creator').text==authors
        assert core.find('{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}lastModifiedBy').text==authors
        paras=[''.join(t.text or '' for t in p.findall('.//w:t',NS)) for p in document.findall('.//w:p',NS)]
        media=[n for n in z.namelist() if n.startswith('word/media/')]
        for rel in ET.fromstring(z.read('word/_rels/document.xml.rels')):
            assert 'word/'+rel.attrib['Target'] in z.namelist()
        footer=z.read('word/footer1.xml').decode()
        assert 'AUN ANIS' in footer and '24P-3017' in footer and 'PAGE' in footer
        assert 'BILAL MALIK' in footer and '24P-3061' in footer
        headings=document.findall('.//w:pStyle',NS)
        assert sum(h.attrib.get('{'+NS['w']+'}val')=='Heading1' for h in headings)>=17
        assert len(document.findall('.//w:tbl',NS))>10
        assert len(paras)>100
    return paras,media

def metric_checks(word_text,pdf_text):
    groups=[]
    baseline=json.loads((ROOT/'reports/ml/model_comparison.json').read_text())
    groups.extend(v['validation'] for v in baseline.values())
    groups.append(json.loads((ROOT/'reports/ml/test_evaluation.json').read_text())['metrics'])
    opt=json.loads((ROOT/'reports/ml/optimization/task7c0-v1/results.json').read_text())
    groups.extend([opt['finalists']['v2_rf_baseline_shape']['validation_at_half'],opt['finalists']['v2_rf_baseline_shape']['validation'],opt['finalists']['v2_extra_trees']['validation'],opt['always_positive_validation']])
    for group in groups:
        for metric in ('accuracy','precision','recall','f1','roc_auc'):
            value=f'{group[metric]:.6f}'
            assert value in word_text and value in pdf_text,(metric,value)
    assert not opt['numerical_gate_passers'] and opt['test_predictions']==0
    for text in [word_text,pdf_text]:
        assert 'not deployed' in text or 'not deployment' in text
        assert 'zero specificity' in text and 'exposed' in text
        assert 'devign-v1-4a23cc304ca8' in text

def main():
    manifest=json.loads((OUT/'report_manifest.json').read_text());checked_sources(manifest)
    for name,digest in manifest['outputs_sha256'].items():assert sha(OUT/name)==digest,name
    paras,media=document_text(OUT/'Codebase_Archaeologist_Report.docx');word_text=' '.join(paras)
    assert len(media)==manifest['figures']
    with zipfile.ZipFile(OUT/'Codebase_Archaeologist_Report.docx') as z:
        body=ET.fromstring(z.read('word/document.xml')).find('w:body',NS)
        children=list(body)
        for title,key,prefix in [('List of Tables','tables','Table'),('List of Figures','figures','Figure')]:
            index=next(i for i,node in enumerate(children) if node.tag.endswith('}p') and ''.join(t.text or '' for t in node.findall('.//w:t',NS))==title)
            listing=next(node for node in children[index+1:] if node.tag.endswith('}tbl'))
            entries=listing.findall('w:tr',NS)[1:]
            assert len(entries)==manifest[key],title
            for number,row in enumerate(entries,1):
                label=''.join(t.text or '' for t in row.find('w:tc',NS).findall('.//w:t',NS))
                assert label.startswith(f'{prefix} {number}.'),label
    assert len(word_text.split())>6000
    with TemporaryDirectory(prefix='task7c-pdf-qa-') as directory:
        text=Path(directory)/'report.txt';bbox=Path(directory)/'bbox.html'
        pdf=OUT/'Codebase_Archaeologist_Report.pdf'
        subprocess.run(['pdftotext','-layout',str(pdf),str(text)],check=True)
        subprocess.run(['pdftotext','-bbox',str(pdf),str(bbox)],check=True)
        info=subprocess.run(['pdfinfo',str(pdf)],check=True,capture_output=True,text=True).stdout
        assert 'Bilal Malik; Aun Anis' in info
        raw=Path(directory)/'raw.txt'
        subprocess.run(['pdftotext','-raw',str(pdf),str(raw)],check=True)
        raw_text=raw.read_text()
        pdf_text=text.read_text();pages=[p for p in pdf_text.split('\f') if p.strip()]
        assert len(pages)==manifest['pdf_pages']
        assert all(len(p.split())>=20 for p in pages)
        outside=[]
        for pi,page in enumerate(ET.parse(bbox).findall('.//{*}page'),1):
            width,height=float(page.attrib['width']),float(page.attrib['height'])
            for word in page.findall('.//{*}word'):
                a=word.attrib
                if float(a['xMin'])<0 or float(a['yMin'])<0 or float(a['xMax'])>width or float(a['yMax'])>height:outside.append((pi,word.text))
        assert not outside,outside
    for text in [word_text,pdf_text]:
        for value in ['Bilal Malik','24P-3061','Aun Anis','24P-3017'] + [json.loads((OUT/'academic_details.json').read_text())[k] for k in ['institution','department','course','instructor','semester','submission_date']]:
            assert compact(value) in compact(text),value
        assert '[CONFIRM ' not in text
        for forbidden in ['Individual AI project','instructor-approved solo participation','Tasks 1, 2 and 3A at implementation']:
            assert forbidden.lower() not in text.lower(),forbidden
    metric_checks(word_text,pdf_text)
    missing=[p for p in paras if len(p)>100 and compact(p) not in compact(pdf_text) and compact(p) not in compact(raw_text)]
    assert not missing,missing[:3]
    for entry in manifest['figure_index']:assert (ROOT/entry['path']).is_file()
    refs=json.loads((OUT/'references.json').read_text());assert [r['id'] for r in refs]==list(range(1,len(refs)+1))
    for ref in refs:
        assert ref['url'].startswith('https://') and ref['verification']
        assert compact(ref['url']) in compact(pdf_text),ref['url']
    chapters={p['chapter'] for p in manifest['page_index']}
    assert all(f'{n:02}' in chapters for n in range(1,18))
    assert all(n in chapters for n in 'ABCDE')
    result={'pdf_pages':len(pages),'chapters':17,'appendices':5,'figures':len(media),'tables':manifest['tables'],
      'docx_words':len(word_text.split()),'source_manifest_current_and_valid':True,'source_output_checksums_valid':True,
      'rounded_saved_metrics_consistent':True,'shared_substantive_paragraphs_match':True,'two_author_metadata_and_identity_valid':True,
      'docx_xml_relationships_and_editable_tables_valid':True,'automatic_word_page_fields':True,
      'pdf_text_outside_page':outside,'empty_pdf_pages':0,'references_traceable':True,
      'verified_application_screenshots':manifest['screenshots_verified'],
      'remaining_academic_placeholders':[],
      'visual_review':'Separate Poppler rendering review; not asserted by this structural validator.',
      'docx_pagination':'Not visually verified; LibreOffice exited1, matching substantive content not guaranteed identical pagination.'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

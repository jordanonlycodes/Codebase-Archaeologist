#!/usr/bin/env python3
"""Build editable DOCX and submission PDF from one evidence-driven page model.

Run: .venv/bin/python tools/generate_report.py
Dependencies: existing matplotlib and Pillow (requirements-ml.txt).
No model import, dataset loading, training or prediction occurs here.
DOCX uses standard Office Open XML; PDF uses Matplotlib's text/vector backend.
"""
from pathlib import Path
import json
import hashlib
import re
import zipfile
from xml.sax.saxutils import escape
import tempfile
from functools import lru_cache

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.font_manager import FontProperties
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
ML = ROOT / 'reports/ml'
BLACK, BURGUNDY, CRIMSON, PALE = '#0B0C0E', '#50202B', '#7A1E2B', '#F3EEEA'
INK, MUTED = '#28252A', '#655D63'
WIDTH, HEIGHT, MARGIN = 595.28, 841.89, 60
BODY_WIDTH = WIDTH - 2 * MARGIN
DATE = '23 November 2026'
AUTHORS = 'Bilal Malik; Aun Anis'
ACADEMIC = json.loads((OUT/'academic_details.json').read_text())
FIGURES, TABLES = [], []
plt.rcParams.update({'font.family': 'DejaVu Sans', 'pdf.fonttype': 42, 'font.size': 10})

def read(name):
    return json.loads((ML / name).read_text())

COMPARISON = read('model_comparison.json')
TEST = read('test_evaluation.json')
AUDIT = read('cleaning_audit.json')
EDA = read('eda_summary.json')
META = read('model_metadata.json')
SCHEMA = read('feature_schema.json')
SOURCE = read('source_manifest.json')
METRICS = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
# Fail rather than silently publish an unsupported model or a different experiment.
assert META['model'] == TEST['model'] == 'random_forest'
assert TEST['evaluations'] == 1 and TEST['selected_before_test']
assert TEST['test_rows_modified'] == 0
assert SCHEMA['names'] == META['feature_names'] == EDA['feature_order']
assert max(COMPARISON, key=lambda n: COMPARISON[n]['validation']['f1']) == 'random_forest'
if (ROOT / 'artifacts/devign-v1/metadata.json').exists():
    assert json.loads((ROOT / 'artifacts/devign-v1/metadata.json').read_text()) == META
    assert json.loads((ROOT / 'artifacts/devign-v1/test_evaluation.json').read_text()) == TEST

PAGES = []
def page(chapter, title, subtitle=''):
    p = {'chapter': chapter, 'title': title, 'subtitle': subtitle, 'blocks': []}
    PAGES.append(p)
    return p['blocks']
def para(blocks, text): blocks.append(('p', text))
def sub(blocks, text): blocks.append(('h', text))
def table(blocks, headings, rows, widths=None): blocks.append(('table', headings, rows, widths))
def figure(blocks, path, caption, height): blocks.append(('figure', str(path), caption, height))
def callout(blocks, text): blocks.append(('callout', text))

def diagram(path, kind):
    fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
    fig.patch.set_facecolor('#fffafa'); ax.set(xlim=(-.2, 10.25), ylim=(0, 6)); ax.axis('off')
    def box(x,y,label,w=2.7,h=.72,dark=False):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08,rounding_size=.08',facecolor=BURGUNDY if dark else PALE,edgecolor=CRIMSON,lw=1))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10,color=PALE if dark else INK,linespacing=1.35)
    def arrow(x1,y1,x2,y2):
        ax.annotate('',(x2,y2),(x1,y1),arrowprops={'arrowstyle':'-|>','color':CRIMSON,'lw':1.6})
    if kind == 'architecture':
        for x,y,t in [(0,4.8,'ZIP / public GitHub'),(3.5,4.8,'Bounded temporary intake'),(7,4.8,'Inventory / C + Python'),(7,3.1,'C-only trusted RF'),(3.5,3.1,'Graph / architecture'),(0,3.1,'FastAPI source-free result'),(0,1.4,'Per-tab bounded snapshot'),(3.5,1.4,'Nine scoped workspaces'),(7,1.4,'Pinned history API')]: box(x,y,t)
        for a in [(2.8,5.16,3.4,5.16),(6.3,5.16,6.9,5.16),(8.35,4.7,8.35,3.9),(6.9,3.46,6.3,3.46),(3.4,3.46,2.8,3.46),(1.35,3,1.35,2.2),(2.8,1.76,3.4,1.76),(6.3,1.76,6.9,1.76)]: arrow(*a)
        ax.text(5,.35,'Schematic evidence flow, not runtime service layers. History retrieval is separate.\nJordan Local / impact reuse the retained graph; repository code never executes.',ha='center',va='center',fontsize=9,color=MUTED)
    elif kind == 'training':
        for x,y,t in [(0,4.8,'Pinned official splits'),(3.5,4.8,'Clean development'),(7,4.8,'Shared11features'),(7,3.1,'Three original candidates'),(3.5,3.1,'Validation F1 selects RF'),(0,3.1,'Historical exposed test'),(0,1.4,'Grouped training CV'),(3.5,1.4,'OOF thresholds / 7finalists'),(7,1.4,'No gate pass: retain RF')]: box(x,y,t)
        for a in [(2.8,5.16,3.4,5.16),(6.3,5.16,6.9,5.16),(8.35,4.7,8.35,3.9),(6.9,3.46,6.3,3.46),(3.4,3.46,2.8,3.46),(2.8,1.76,3.4,1.76),(6.3,1.76,6.9,1.76)]: arrow(*a)
        ax.text(5,.35,'Lower row: later optimization development only; no new test predictions.\nExperimental22features remain isolated; official partitions unchanged.',ha='center',va='center',fontsize=9,color=MUTED)
    else:
        for x,y,t in [(0,4.8,'Included .c files'),(3.5,4.8,'Bounds + Tree-sitter parse'),(7,4.8,'Genuine definitions\nwith paths + lines'),(7,3,'Unchanged feature extractor'),(3.5,3,'Saved imputer + classifier'),(0,3,'Validate output\nclass + probability'),(0,1.2,'Structured function results'),(3.5,1.2,'UI counts, filters + details'),(7,1.2,'No new inference\non navigation')]: box(x,y,t)
        for a in [(2.8,5.16,3.4,5.16),(6.3,5.16,6.9,5.16),(8.35,4.7,8.35,3.8),(6.9,3.36,6.3,3.36),(3.4,3.36,2.8,3.36),(1.35,2.9,1.35,2),(2.8,1.56,3.4,1.56),(6.3,1.56,6.9,1.56)]: arrow(*a)
        ax.text(5,.25,'Invalid functions abstain. File issues expose unknown coverage. No source text is returned.',ha='center',fontsize=10,color=MUTED)
    fig.subplots_adjust(.025,.025,.975,.975)
    fig.savefig(path); plt.close(fig)

def selected_panels(path, original, title):
    """Reuse original EDA pixels: four documented panel crops, not new data."""
    image = Image.open(original)
    w,h=image.size
    # Original 3x4 grid: physical lines, bytes, complexity and calls.
    cells=[(0,0),(0,2),(2,0),(2,2)]
    fig,axes=plt.subplots(2,2,figsize=(8,5.7),dpi=180)
    for ax,(row,col) in zip(axes.flat,cells):
        crop=image.crop((int(col*w/4),int(row*h/3),int((col+1)*w/4),int((row+1)*h/3)))
        ax.imshow(crop);ax.axis('off')
    fig.subplots_adjust(.005,.005,.995,.995,wspace=.01,hspace=.01)
    fig.savefig(path);plt.close(fig)

_MEASURE_FIG = plt.figure(figsize=(1,1),dpi=72)
_MEASURE_FIG.canvas.draw()
RENDERER = _MEASURE_FIG.canvas.get_renderer()

@lru_cache(maxsize=8192)
def wrap(text, width, size=10):
    font=FontProperties(family='DejaVu Sans',size=size)
    def measure(s): return RENDERER.get_text_width_height_descent(s,font,False)[0]
    lines=[]
    for original in str(text).split('\n'):
        line=''
        for word in original.split():
            if measure(word)>width:
                pieces=[];part=''
                for char in word:
                    if part and measure(part+char)>width: pieces.append(part);part=''
                    part+=char
                pieces.append(part)
            else: pieces=[word]
            for piece in pieces:
                candidate=(line+' '+piece).strip()
                if line and measure(candidate)>width: lines.append(line);line=piece
                else: line=candidate
        lines.append(line)
    return lines

def layout(blocks):
    planned=[];height=0
    for block in blocks:
        kind=block[0]
        if kind in ('p','h','callout'):
            size={'p':10,'h':11,'callout':11}[kind]
            pad=12 if kind=='callout' else 0
            lines=wrap(block[1],BODY_WIDTH-pad*2,size)
            h=len(lines)*(15 if kind!='h' else 16)+(18 if kind=='callout' else 10)
            planned.append((block,h,lines));height+=h
        elif kind=='table':
            _,heads,rows,widths=block
            widths=widths or [1/len(heads)]*len(heads)
            wrapped=[]
            for row in [heads]+rows:
                cells=[wrap(str(cell),BODY_WIDTH*w-14,8.5) for cell,w in zip(row,widths)]
                h=max(len(c) for c in cells)*12+14
                wrapped.append((cells,h))
            h=sum(row[1] for row in wrapped)+13
            planned.append((block,h,wrapped));height+=h
        else:
            lines=wrap(block[2],BODY_WIDTH,8.4)
            h=block[3]+len(lines)*12+18
            planned.append((block,h,lines));height+=h
    return planned,height

def draw_text(ax,text,x,y,size=10,color=INK,weight='normal'):
    ax.text(x,y,text,va='top',ha='left',fontsize=size,color=color,fontweight=weight,linespacing=1.42)

COVER = [
    ('UNIVERSITY AI PROJECT REPORT',11,'7A1E2B',True),
    ('Codebase Archaeologist',27,'0B0C0E',True),
    ('AI-Powered Repository Intelligence',16,'28252A',False),
    ('& Defect Risk Analyzer',16,'28252A',False),
    ('Bilal Malik — 24P-3061',17,'28252A',True),
    ('Aun Anis — 24P-3017',17,'28252A',True),
    (ACADEMIC['institution'],12,'28252A',False),
    ('Department: '+ACADEMIC['department'],12,'28252A',False),
    ('Academic details explicitly confirmed by the project team.',9,'655D63',False),
    ('Course: '+ACADEMIC['course'],11,'28252A',False),
    ('Instructor: '+ACADEMIC['instructor'],11,'28252A',False),
    ('Semester: '+ACADEMIC['semester'],11,'28252A',False),
    ('Submission: '+ACADEMIC['submission_date'],11,'28252A',False),
    ('Two-member group permitted, as confirmed by the team.',10,'655D63',False),
    ('Evidence-driven final revision · built 23 November 2026',10,'655D63',False),
]

def pdf_cover(pdf):
    fig=plt.figure(figsize=(WIDTH/72,HEIGHT/72),dpi=72)
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,WIDTH),ylim=(HEIGHT,0));ax.axis('off')
    ax.plot([MARGIN,WIDTH-MARGIN],[80,80],color=CRIMSON,lw=2)
    y=105
    for i,(text,size,color,bold) in enumerate(COVER):
        lines=wrap(text,BODY_WIDTH,size)
        draw_text(ax,'\n'.join(lines),MARGIN,y,size,'#'+color,'bold' if bold else 'normal')
        y+=len(lines)*size*1.42+(22 if i in [0,3,5,8] else 10)
    pdf.savefig(fig,dpi=220);plt.close(fig)

def build_pdf(path):
    with PdfPages(path,metadata={'Title':'Codebase Archaeologist — AI-Powered Repository Intelligence & Defect Risk Analyzer','Author':AUTHORS,'Subject':'AI-Powered Repository Intelligence & Defect Risk Analyzer'}) as pdf:
        pdf_cover(pdf)
        for index,p in enumerate(PAGES,start=2):
            plan,height=layout(p['blocks'])
            if height>638:
                raise ValueError(f'Page overflows ({height:.0f}pt): {p["title"]}')
            fig=plt.figure(figsize=(WIDTH/72,HEIGHT/72),dpi=72)
            ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,WIDTH),ylim=(HEIGHT,0));ax.axis('off')
            draw_text(ax,'CODEBASE ARCHAEOLOGIST',MARGIN,25,8,MUTED,'bold')
            draw_text(ax,'RESEARCH / 2026',440,25,8,MUTED)
            ax.plot([MARGIN,WIDTH-MARGIN],[46,46],color=PALE,lw=1)
            draw_text(ax,p['chapter']+'  /  '+('CONTENTS' if p['chapter']=='00' else 'RESEARCH & IMPLEMENTATION'),MARGIN,61,8.5,CRIMSON,'bold')
            title_size=17
            while len(wrap(p['title'],BODY_WIDTH,title_size))>1: title_size-=.5
            draw_text(ax,p['title'],MARGIN,82,title_size,BLACK,'bold')
            draw_text(ax,p['subtitle'],MARGIN,115,9,MUTED)
            y=145
            for block,h,aux in plan:
                kind=block[0]
                if kind in ('p','h','callout'):
                    if kind=='callout':
                        ax.add_patch(Rectangle((MARGIN,y-3),BODY_WIDTH,h-4,color=PALE))
                        ax.add_patch(Rectangle((MARGIN,y-3),3,h-4,color=CRIMSON))
                    draw_text(ax,'\n'.join(aux),MARGIN+(12 if kind=='callout' else 0),y+(5 if kind=='callout' else 0),10 if kind=='p' else 11,BURGUNDY if kind!='p' else INK,'bold' if kind!='p' else 'normal')
                elif kind=='table':
                    widths=block[3] or [1/len(block[1])]*len(block[1]);yy=y
                    for rowidx,(cells,rh) in enumerate(aux):
                        ax.add_patch(Rectangle((MARGIN,yy),BODY_WIDTH,rh,facecolor=BURGUNDY if rowidx==0 else '#FCF4F5' if rowidx%2 else '#FFFFFF',edgecolor='none'))
                        x=MARGIN
                        for lines,w in zip(cells,widths):
                            draw_text(ax,'\n'.join(lines),x+7,yy+7,8.5,PALE if rowidx==0 else INK,'bold' if rowidx==0 else 'normal')
                            x+=BODY_WIDTH*w
                        yy+=rh
                        ax.plot([MARGIN,MARGIN+BODY_WIDTH],[yy,yy],color='#E8DADF',lw=.4)
                else:
                    image=Image.open(block[1]);iw,ih=image.size
                    boxh=block[3];boxw=min(BODY_WIDTH,boxh*iw/ih);actualh=boxw*ih/iw
                    x=MARGIN+(BODY_WIDTH-boxw)/2
                    ax.imshow(image,extent=(x,x+boxw,y+actualh,y),aspect='auto')
                    draw_text(ax,'\n'.join(aux),MARGIN,y+boxh+7,8.4,MUTED)
                y+=h
            ax.plot([MARGIN,WIDTH-MARGIN],[796,796],color=PALE,lw=1)
            draw_text(ax,'BILAL MALIK ·24P-3061  /  AUN ANIS ·24P-3017',MARGIN,809,7.0,MUTED)
            draw_text(ax,f'{index:02d} / {len(PAGES)+1:02d}',490,809,8,CRIMSON,'bold')
            pdf.savefig(fig, dpi=220);plt.close(fig)

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
XML='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
def run(text,size=20,color='28252A',bold=False):
    return f'<w:r><w:rPr><w:rFonts w:ascii="DejaVu Sans" w:hAnsi="DejaVu Sans"/><w:sz w:val="{size}"/><w:color w:val="{color}"/>'+('<w:b/>' if bold else '')+'</w:rPr><w:t xml:space="preserve">'+escape(str(text))+'</w:t></w:r>'
def paragraph(text='',size=20,color='28252A',bold=False,style=None,before=0,after=130,keep=False,shade=None):
    props=f'<w:spacing w:before="{before}" w:after="{after}" w:line="{max(290,size*13)}" w:lineRule="exact"/>'
    if style: props+=f'<w:pStyle w:val="{style}"/>'
    if keep: props+='<w:keepNext/>'
    if shade: props+=f'<w:shd w:fill="{shade}"/>'
    return '<w:p><w:pPr>'+props+'</w:pPr>'+run(text,size,color,bold)+'</w:p>'

def build_docx(path):
    media=[]
    parts=[]
    for i,(text,size,color,bold) in enumerate(COVER):
        parts.append(paragraph(text,size*2,color,bold,before=500 if i==0 else 0,after=400 if i in [0,3,5,8] else 150))
    for index,p in enumerate(PAGES,start=2):
        parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        parts.append(paragraph(p['chapter']+' / RESEARCH & IMPLEMENTATION',17,'E54859',True,before=100,after=220))
        parts.append(paragraph(p['title'],34,'0A0A0D',True,style='Heading1',after=320,keep=True))
        parts.append(paragraph(p['subtitle'],18,'655D63',after=280,keep=True))
        for block in p['blocks']:
            kind=block[0]
            if kind in ('p','h','callout'):
                parts.append(paragraph(block[1],20 if kind=='p' else 22,'28252A' if kind=='p' else '30151D',kind!='p',style='Heading2' if kind=='h' else None,before=60 if kind=='h' else 0,after=140,keep=kind=='h',shade='F8E8EA' if kind=='callout' else None))
            elif kind=='table':
                heads,rows,widths=block[1:];widths=widths or [1/len(heads)]*len(heads)
                t=['<w:tbl><w:tblPr><w:tblW w:w="9506" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:left w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>']
                for width in widths:t.append(f'<w:gridCol w:w="{int(width*9506)}"/>')
                t.append('</w:tblGrid>')
                for ri,row in enumerate([heads]+rows):
                    t.append('<w:tr><w:trPr><w:cantSplit/>'+('<w:tblHeader/>' if ri==0 else '')+'</w:trPr>')
                    for text,width in zip(row,widths):
                        fill='30151D' if ri==0 else 'FCF4F5' if ri%2 else 'FFFFFF'
                        t.append(f'<w:tc><w:tcPr><w:tcW w:w="{int(width*9506)}" w:type="dxa"/><w:shd w:fill="{fill}"/></w:tcPr>'+paragraph(text,17,'F8E8EA' if ri==0 else '28252A',ri==0,after=0).replace('w:line="290"','w:line="240"')+'</w:tc>')
                    t.append('</w:tr>')
                t.append('</w:tbl>');parts.append(''.join(t));parts.append(paragraph('',after=60,size=2))
            else:
                image=Path(block[1]);im=Image.open(image);iw,ih=im.size
                h=block[3];w=min(BODY_WIDTH,h*iw/ih);h=w*ih/iw
                media.append(image);n=len(media);cx,cy=int(w*12700),int(h*12700)
                parts.append(f'''<w:p><w:pPr><w:jc w:val="center"/><w:keepNext/><w:spacing w:after="80"/></w:pPr><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Figure {n}" descr="{escape(block[2])}"/><a:graphic xmlns:a="{A}"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{n}" name="figure{n}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="img{n}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>''')
                parts.append(paragraph(block[2],17,'655D63',after=160))
    sect='<w:sectPr><w:headerReference w:type="default" r:id="header"/><w:footerReference w:type="default" r:id="footer"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1200" w:right="1200" w:bottom="1200" w:left="1200" w:header="400" w:footer="400"/><w:titlePg/></w:sectPr>'
    document=XML+f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'+''.join(parts)+sect+'</w:body></w:document>'
    rels=[('styles','styles','styles.xml'),('header','header','header1.xml'),('footer','footer','footer1.xml')]+[(f'img{i}','image',f'media/image{i}.png') for i in range(1,len(media)+1)]
    relationships=XML+'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="{i}" Type="{R}/{t}" Target="{target}"/>' for i,t,target in rels)+'</Relationships>'
    types=XML+'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'+''.join(f'<Override PartName="/word/{name}.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.{typ}+xml"/>' for name,typ in [('document','document.main'),('styles','styles'),('header1','header'),('footer1','footer')])+'</Types>'
    styles=XML+f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="DejaVu Sans" w:hAnsi="DejaVu Sans"/><w:sz w:val="20"/></w:rPr></w:rPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'+''.join(f'<w:style w:type="paragraph" w:styleId="Heading{i}"><w:name w:val="heading {i}"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="{i-1}"/></w:pPr></w:style>' for i in (1,2))+'</w:styles>'
    header=XML+f'<w:hdr xmlns:w="{W}">'+paragraph('CODEBASE ARCHAEOLOGIST                                      RESEARCH / 2026',16,'655D63',after=0)+'</w:hdr>'
    footer=XML+f'<w:ftr xmlns:w="{W}"><w:p>'+run('BILAL MALIK ·24P-3061 / AUN ANIS ·24P-3017          ',13,'655D63')+'<w:fldSimple w:instr="PAGE">'+run('1',16,'E54859')+'</w:fldSimple></w:p></w:ftr>'
    core=XML+'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Codebase Archaeologist — AI-Powered Repository Intelligence &amp; Defect Risk Analyzer</dc:title><dc:creator>Bilal Malik; Aun Anis</dc:creator><cp:lastModifiedBy>Bilal Malik; Aun Anis</cp:lastModifiedBy><dc:subject>AI-Powered Repository Intelligence &amp; Defect Risk Analyzer</dc:subject></cp:coreProperties>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in {'[Content_Types].xml':types,'_rels/.rels':XML+f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="doc" Type="{R}/officeDocument" Target="word/document.xml"/><Relationship Id="core" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>','docProps/core.xml':core,'word/document.xml':document,'word/_rels/document.xml.rels':relationships,'word/styles.xml':styles,'word/header1.xml':header,'word/footer1.xml':footer}.items():z.writestr(name,value)
        for i,image in enumerate(media,start=1):z.write(image,f'word/media/image{i}.png')

def paginate(pages, limit=575):
    """Bounded page model; split whole paragraphs and table rows, repeat table headers."""
    result=[]
    for original in pages:
        current={**original,'blocks':[]};continued=0
        def flush():
            nonlocal current,continued
            if current['blocks']: result.append(current)
            continued+=1
            current={**original,'title':original['title']+' (continued)','blocks':[]}
        queue=list(original['blocks'])
        while queue:
            block=queue.pop(0)
            if block[0]=='table':
                head,rows,widths=block[1:];part=[]
                for row in rows:
                    trial=('table',head,part+[row],widths)
                    if layout(current['blocks']+[trial])[1]>limit:
                        if part:current['blocks'].append(('table',head,part,widths));part=[]
                        flush()
                        if layout([('table',head,[row],widths)])[1]>limit:raise ValueError('Oversized table row')
                    part.append(row)
                if part:current['blocks'].append(('table',head,part,widths))
            else:
                lookahead=[]
                if queue and (block[0]=='h' or (block[0]=='p' and re.match(r'^Table \d+\.',block[1]))):
                    next_block=queue[0]
                    lookahead=[('table',next_block[1],next_block[2][:3],next_block[3])] if next_block[0]=='table' else [next_block]
                if layout(current['blocks']+[block]+lookahead)[1]>limit:flush()
                if layout([block])[1]>limit:raise ValueError('Oversized atomic report block')
                current['blocks'].append(block)
        if current['blocks']:result.append(current)
        # Balance a very short final continuation without splitting any paragraph.
        if len(result)>1 and result[-1]['chapter']==result[-2]['chapter'] and layout(result[-1]['blocks'])[1]<180:
            previous,last=result[-2],result[-1]
            while len(previous['blocks'])>1 and layout(last['blocks'])[1]<240:
                block=previous['blocks'][-1]
                if block[0] not in ('p','callout') or re.match(r'^Table \d+\.',block[1]):break
                if layout([block]+last['blocks'])[1]>limit:break
                previous['blocks'].pop();last['blocks'].insert(0,block)
    return result


def contents_pages(body):
    # Iterate page-offset calculation because lists can themselves span pages.
    offset=0
    for _ in range(5):
        pages=[];chapters=[];seen=set();figs=[];tables=[]
        for index,p in enumerate(body,start=2):
            pg=index+(offset if p['chapter']!='FM' else 0)
            if p['chapter']!='FM' and p['chapter'] not in seen:
                chapters.append([p['chapter']+' '+p['title'],str(pg)]);seen.add(p['chapter'])
            for block in p['blocks']:
                if block[0]=='figure':figs.append([block[2],str(pg)])
                if block[0]=='p' and re.match(r'^Table \d+\.',block[1]):tables.append([block[1],str(pg)])
        for title,rows in [('Contents',chapters),('List of Figures',figs),('List of Tables',tables)]:
            item={'chapter':'FM','title':title,'subtitle':'Page references follow the fixed PDF; editable Word may repaginate.','blocks':[]}
            table(item['blocks'],['Entry','Page'],rows,[.88,.12]);pages.extend(paginate([item],limit=638))
        if len(pages)==offset:return pages
        offset=len(pages)
    raise ValueError('Contents offset did not stabilize')


def evidence_files():
    roots=['app/routes','app/ml','app/analysis','app/ingestion','app/history','app/jordan','app/templates','app/static/product','app/static/graph','app/static/architecture','app/static/impact','app/static/jordan','app/static/time_machine','tests']
    files=[ROOT/'app/config.py',ROOT/'app/static/product/motion.js',ROOT/'app/static/risk.js',ROOT/'app/static/structural.js']
    for root in roots:files.extend(p for p in (ROOT/root).rglob('*') if p.suffix in ('.py','.js','.css','.html','.cjs') and '__pycache__' not in p.parts)
    files.extend(p for p in ML.rglob('*') if p.suffix in ('.json','.png','.txt'))
    files.extend(ROOT/name for name in ['tools/generate_report.py','tools/report_content.py','tools/report_charts.py','tools/validate_report.py','tools/check_report_links.py','submission/references.json','submission/screenshots.json','submission/test_evidence.json','submission/academic_details.json','models/devign-v1/manifest.json','tools/install_model.py','tools/release_smoke.py','tools/build_submission.py','requirements-runtime.lock'])
    files.extend(p for p in (ROOT/'docs').glob('task7*.md'))
    return sorted(set(files))


def main():
    import sys,subprocess
    from report_content import build
    from report_charts import charts
    OUT.mkdir(exist_ok=True); assets=OUT/'figures';assets.mkdir(exist_ok=True)
    PAGES.clear();FIGURES.clear();TABLES.clear()
    for kind in ('architecture','training','inference'):diagram(assets/(kind+'.png'),kind)
    selected_panels(assets/'distributions_selected.png',ML/'feature_distributions.png','Distributions')
    charts(assets)
    build(sys.modules[__name__],assets)
    body=paginate(PAGES);front=contents_pages(body)
    boundary=next(i for i,p in enumerate(body) if p['chapter']!='FM')
    PAGES[:]=body[:boundary]+front+body[boundary:]
    for p in PAGES:
        _,height=layout(p['blocks']);assert height<=638
    build_pdf(OUT/'Codebase_Archaeologist_Report.pdf');build_docx(OUT/'Codebase_Archaeologist_Report.docx')
    manifest={'implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'build_tree':'Source checksums cover the reviewed build tree; implementation_commit is its base HEAD before output commit.',
      'report_date':DATE,'pdf_pages':len(PAGES)+1,'chapters':17,'appendices':5,'figures':len(FIGURES),'tables':len(TABLES),
      'figure_index':FIGURES,'table_index':TABLES,
      'page_index':[{'page':i,'chapter':p['chapter'],'title':p['title']} for i,p in enumerate(PAGES,2)],
      'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence_files()},
      'outputs_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('Codebase_Archaeologist_Report.*')},
      'training_or_evaluation_rerun':False,'authors':AUTHORS,
      'screenshots_verified':sum(bool(i.get('verified')) for i in json.loads((OUT/'screenshots.json').read_text())),
      'docx_rendering':'Editable OOXML with shared substantive content; office-suite pagination not visually verified. LibreOffice attempt exit1.'}
    (OUT/'report_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Generated {len(PAGES)+1}-page PDF, editable DOCX; {len(FIGURES)}figures, {len(TABLES)}tables.')

if __name__=='__main__':main()

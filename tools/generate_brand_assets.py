"""Rebuild local, GitHub-compatible vector brand art. Not an application screenshot.

Uses the tracked OFL font subsets, converted to paths for deterministic rendering.
Optional development dependency: fonttools. No model/data/application analysis runs.
"""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]


def generate(destination):
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen
    except ImportError as exc:
        raise SystemExit('Install the optional asset tool: pip install fonttools') from exc
    fonts={name:TTFont(ROOT/'app/static/product/fonts'/filename) for name,filename in {
        'serif':'editorial-regular.woff','italic':'editorial-italic.woff','sans':'interface-regular.woff',
    }.items()}
    def text(value,face,size,x,y,color,tracking=0):
        font=fonts[face];glyphs=font.getGlyphSet();mapping=font.getBestCmap();scale=size/font['head'].unitsPerEm;parts=[]
        for char in value:
            glyph=glyphs[mapping.get(ord(char),'.notdef')];pen=SVGPathPen(glyphs);glyph.draw(pen)
            if pen.getCommands():parts.append(f'<path d="{pen.getCommands()}" transform="translate({x:.3f} {y:.3f}) scale({scale:.6f} {-scale:.6f})"/>')
            x+=glyph.width*scale+tracking
        return f'<g fill="{color}">'+''.join(parts)+'</g>'
    paths=[]
    for i in range(17):
        paths.append(f'<path d="M {600+i*14} 660 C {1090+i*4} {540-i*4}, {950+i*7} {50+i*6}, 1238 {285+i*.7}" fill="none" stroke="url(#trail)" stroke-width="{.5+(i%3)*.3}"/>')
    identity=''.join([
        text('REPOSITORY INTELLIGENCE / A LOCAL RESEARCH INSTRUMENT','sans',10,78,63,'#9b938b',1.4),
        text('Codebase','serif',100,75,221,'#ebe7df',-1.6),
        text('Archaeologist','italic',130,75,366,'#ebe7df',-2),
        text('.','italic',130,895,366,'#bd7c81',-1),
        text('UNCOVER THE UNSEEN','sans',10,85,425,'#c9b6a7',4.2),
        text('Beyond files. Toward understanding.','sans',14,84,477,'#aaa49b',.15),
        text('SOURCE / STRUCTURE / CONSEQUENCE','sans',9,78,586,'#9f938b',1.5),
        text('BUILT ON EVIDENCE.','sans',9,1150,586,'#c3b0a5',1.2),
    ])
    content=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="640" viewBox="0 0 1440 640" role="img" aria-labelledby="title desc">
<title id="title">Codebase Archaeologist. Uncover the unseen.</title><desc id="desc">Original graphite and ivory editorial brand artwork with restrained organic light trails. Repository intelligence built on evidence. This is brand art, not an application screenshot.</desc>
<metadata>Typography: Noto Project Authors, SIL OFL 1.1. Glyphs subset and converted to paths; license in app/static/product/fonts/OFL.txt. Reproduce with tools/generate_brand_assets.py.</metadata>
<defs><radialGradient id="atmosphere"><stop stop-color="#5e4e3d" stop-opacity=".28"/><stop offset="1" stop-color="#0b0c0e" stop-opacity="0"/></radialGradient><linearGradient id="trail" x1="0" y1="1" x2="1" y2="0"><stop stop-color="#6f4c50" stop-opacity="0"/><stop offset=".5" stop-color="#bc9482" stop-opacity=".5"/><stop offset="1" stop-color="#dfcfac" stop-opacity=".8"/></linearGradient><radialGradient id="light"><stop stop-color="#fff2d2"/><stop offset=".18" stop-color="#efdcba"/><stop offset=".5" stop-color="#c2a475" stop-opacity=".4"/><stop offset="1" stop-color="#c2a475" stop-opacity="0"/></radialGradient></defs>
<rect width="1440" height="640" fill="#0b0c0e"/><ellipse cx="1238" cy="292" rx="460" ry="330" fill="url(#atmosphere)"/>{''.join(paths)}<circle cx="1238" cy="292" r="28" fill="url(#light)"/><path d="M78 540 H1362" stroke="#48403a" stroke-width=".7"/>{identity}</svg>'''
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(content)
    for font in fonts.values():font.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/assets/hero.svg')
    generate(parser.parse_args().output)

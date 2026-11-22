"""Author editable Minimalist Relic SVGs; optional fonttools outlines local OFL type.

This is original vector construction guided by the user's supplied Task7B reference,
not image tracing, stock art, or an assertion of trademark clearance.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'app/static/brand'


def symbol(ink='#E6DDD1', small=False):
    lines = ('M25 44h17M22 55h18M27 66h10' if small else
             'M31 36h12M26 45h16M21 54h20M23 63h15M28 72h7')
    branches = ('M57 49h9l15-17M66 49l15 18' if small else
                'M57 42l13-23M57 51h11l15-15M68 51l14 17M54 70l11 9 17-11')
    branch_ink = ink if small else '#7A1E2B'
    nodes = [(81,32),(81,67)] if small else [(70,19),(83,36),(82,68)]
    return (f'<g fill="none" stroke="{ink}" stroke-width="2.7" stroke-linejoin="miter">'
            '<path d="M55 9 20 34 9 48 12 64 26 81 43 93 50 64 51 36Z"/>'
            f'<path d="{lines}" stroke-width="2" stroke-linecap="square"/>'
            '<path d="m55 9-4 27 1 12-2 16" stroke-width="1.3"/></g>'
            f'<g fill="none" stroke="{branch_ink}" stroke-width="2.8"><path d="{branches}"/>'
            + ''.join(f'<circle cx="{x}" cy="{y}" r="5.5"/>' for x,y in nodes)
            + '<circle cx="68" cy="51" r="2.6" fill="#7A1E2B"/></g>')


def svg(body, width=96, height=104, title='Codebase Archaeologist — Minimalist Relic'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">'
            f'<title id="title">{title}</title>{body}</svg>\n')


def wordmark(ink):
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    result=[]
    for value,face,y,size in [('Codebase','editorial-regular.woff',51,43),
                              ('Archaeologist.','editorial-italic.woff',100,45)]:
        font=TTFont(ROOT/'app/static/product/fonts'/face)
        glyphs=font.getGlyphSet();mapping=font.getBestCmap();scale=size/font['head'].unitsPerEm;x=128
        for char in value:
            glyph=glyphs[mapping[ord(char)]];pen=SVGPathPen(glyphs);glyph.draw(pen)
            if pen.getCommands():
                result.append(f'<path d="{pen.getCommands()}" transform="translate({x:.3f} {y}) scale({scale:.6f} {-scale:.6f})"/>')
            x+=glyph.width*scale
        font.close()
    return f'<g fill="{ink}">'+''.join(result)+'</g>'


def generate():
    DEST.mkdir(exist_ok=True)
    for name,ink in [('dark','#E6DDD1'),('light','#0B0C0E')]:
        (DEST/f'relic-{name}.svg').write_text(svg(symbol(ink)))
        (DEST/f'logo-{name}.svg').write_text(svg('<g transform="translate(4 6)">'+symbol(ink)+'</g>'+wordmark(ink),440,120))
    # Opaque, simplified favicon stays legible in both dark and light browser tabs.
    tiny='<rect width="104" height="104" rx="18" fill="#0B0C0E"/>'+symbol(small=True)
    (DEST/'favicon.svg').write_text(svg(tiny,104,104))
    (DEST/'relic-small.svg').write_text(svg(symbol(small=True)))
    (DEST/'touch-icon.svg').write_text(svg(tiny,104,104))
    # Keep the previous public URL available to existing bookmarks/clients.
    (ROOT/'app/static/mark.svg').write_text(svg(symbol()))


if __name__ == '__main__':
    generate()

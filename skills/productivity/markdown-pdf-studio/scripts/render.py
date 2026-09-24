#!/usr/bin/env python3
"""Constrained Markdown to PDF via pinned Chromium; no backend fallback."""
import argparse
import base64
import hashlib
import html
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright
from pypdf import PdfReader
from pypdf.generic import ByteStringObject, TextStringObject
import pypdfium2 as pdfium

HOME = Path.home() / '.hermes/tools/markdown-pdf'
ASSETS = Path(__file__).resolve().parent.parent / 'assets'
THEMES = ('default', 'cjk-auto', 'warm-terra', 'warm-terra-menu', 'mobile')
FONT_SHA256 = '990c807e79c25662a5a9ecf7f971baeb2bf2eab9a559e5ecf15cdfdb8561d21f'


def pagebreak_rule(state, start, end, silent):
    line = state.src[state.bMarks[start] + state.tShift[start]:state.eMarks[start]]
    if line.strip() != '<!-- pagebreak -->' or state.is_code_block(start):
        return False
    if not silent:
        state.push('pagebreak', 'div', 0)
        state.line = start + 1
    return True


def markdown(source):
    if not source.strip():
        raise ValueError('Empty Markdown')
    if len(source.encode('utf-8')) > 500000:
        raise ValueError('Markdown exceeds 500000 bytes')
    parser = MarkdownIt('commonmark', {'html': False}).enable('table')
    # Parse destinations first, then enforce our stricter allowlist before rendering.
    parser.validateLink = lambda url: True
    parser.block.ruler.before('paragraph', 'pagebreak', pagebreak_rule)
    parser.add_render_rule('pagebreak', lambda self, tokens, idx, options, env: '<div class="pagebreak"></div>\n')
    tokens = parser.parse(source)
    pending = list(tokens)
    count = 0
    while pending:
        token = pending.pop()
        count += 1
        if count > 50000:
            raise ValueError('Markdown exceeds 50000 tokens')
        pending.extend(token.children or [])
        if token.type == 'image':
            raise ValueError('Images are disabled: no network, data or local images')
        if token.type == 'link_open':
            target = token.attrGet('href') or ''
            url = urlsplit(target)
            if not target.startswith('#') and not (url.scheme in ('http', 'https', 'mailto') and (url.netloc or url.scheme == 'mailto')):
                raise ValueError('Link scheme is not allowed: use HTTP(S), mailto or #fragment')
    return parser.renderer.render(tokens, parser.options, {})


def font_css(source):
    path = HOME / 'fonts/NotoSansCJKsc-VF.ttf'
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != FONT_SHA256:
        raise ValueError('Font asset checksum mismatch')
    font = TTFont(io.BytesIO(data))
    try:
        cmap = font.getBestCmap()
        missing = sorted({f'U+{ord(ch):04X}' for ch in source if not ch.isspace() and ord(ch) not in cmap})
        if missing:
            raise ValueError('Unsupported glyphs: ' + ', '.join(missing[:20]))
        options = subset.Options()
        options.layout_features = ['*']
        cutter = subset.Subsetter(options=options)
        cutter.populate(text=source + '0123456789•')
        cutter.subset(font)
        # Static in-memory subset avoids Chromium outlining variable glyphs as Type3.
        instantiateVariableFont(font, {'wght': 400}, inplace=True)
        buffer = io.BytesIO()
        font.save(buffer)
    finally:
        font.close()
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return "@font-face{font-family:'StudioCJK';font-style:normal;font-weight:normal;src:url(data:font/ttf;base64," + encoded + ") format('truetype');}\n"


def pdf_stats(data):
    reader = PdfReader(io.BytesIO(data))
    fonts, zero = set(), 0
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or '')
        resources = page['/Resources'].get_object().get('/Font', {})
        resources = resources.get_object() if hasattr(resources, 'get_object') else resources
        cid_fonts = set()
        for name, ref in resources.items():
            font = ref.get_object()
            fonts.add(str(font.get('/BaseFont', 'unknown')))
            if font.get('/Encoding') == '/Identity-H':
                cid_fonts.add(name)
        active = None
        for operands, operator in page.get_contents().operations:
            if operator == b'Tf':
                active = operands[0]
            elif operator in (b'Tj', b'TJ') and active in cid_fonts:
                strings = operands[0] if operator == b'TJ' else operands[:1]
                for value in strings:
                    if isinstance(value, ByteStringObject):
                        raw = bytes(value)
                    elif isinstance(value, TextStringObject):
                        raw = value.get_original_bytes()
                    else:
                        continue
                    zero += sum(raw[i:i + 2] == b'\x00\x00' for i in range(0, len(raw), 2))
    if zero or any('\ufffd' in text or '\x00' in text for text in pages):
        raise ValueError('PDF contains missing/zero glyph codes or replacement characters')
    return reader, pages, sorted(fonts), zero


def render(source, output, theme='default', lang='en'):
    if theme not in THEMES:
        raise ValueError('Unknown theme')
    body = markdown(source)
    css = font_css(source) + (ASSETS / 'base.css').read_text() + (ASSETS / 'themes' / (theme + '.css')).read_text()
    csp = "default-src 'none'; style-src 'unsafe-inline'; font-src data:; img-src 'none'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
    document = '<!doctype html><html lang="' + html.escape(lang, quote=True) + '"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="' + html.escape(csp, quote=True) + '"><title>' + html.escape(output.stem) + '</title><style>' + css + '</style></head><body><main>' + body + '</main></body></html>'
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(HOME / 'browsers')
    blocked = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, chromium_sandbox=True)
        try:
            context = browser.new_context(java_script_enabled=False, offline=True, service_workers='block')
            def deny(route):
                blocked.append(route.request.url)
                route.abort()
            context.route('**/*', deny)
            page = context.new_page()
            page.set_content(document, wait_until='load', timeout=30000)
            page.emulate_media(media='print')
            page.evaluate('document.fonts.ready')
            geometry = page.evaluate('''() => {
                const main = document.querySelector('main').getBoundingClientRect();
                const rect = e => { const r=e.getBoundingClientRect(); return {tag:e.tagName,x:r.x,y:r.y,width:r.width,height:r.height}; };
                const overflow = [...document.querySelectorAll('main *')].filter(e => {
                    const r=e.getBoundingClientRect(); return r.right > main.right+1 || r.left < main.left-1 || e.scrollWidth > e.clientWidth+2 && ['TD','TH','PRE'].includes(e.tagName);
                }).map(rect);
                return {overflow,tables:[...document.querySelectorAll('table')].map(rect),content_width:main.width};
            }''')
            if geometry['overflow']:
                raise ValueError('Horizontal layout overflow: ' + json.dumps(geometry['overflow'][:8]))
            if blocked:
                raise ValueError('Unexpected resource requests were blocked')
            data = page.pdf(print_background=True, prefer_css_page_size=True, display_header_footer=False, tagged=True)
            version = browser.version
        finally:
            browser.close()
    reader, texts, fonts, zero = pdf_stats(data)
    if len(reader.pages) > 100:
        raise ValueError('PDF exceeds 100 pages')
    preview_dir = output.with_suffix('.previews')
    text_path = output.with_suffix('.text.txt')
    previews = [str(preview_dir / f'page-{i + 1}.png') for i in range(len(reader.pages))]
    report = {
        'backend': 'chromium-playwright', 'browser_version': version,
        'theme': theme, 'language': lang, 'output': str(output),
        'page_count': len(reader.pages), 'pdf_bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'missing_glyphs': [], 'zero_glyph_codes': zero, 'pdf_fonts': fonts,
        'font_sha256': FONT_SHA256, 'blocked_requests': blocked,
        **geometry, 'previews': previews, 'text_path': str(text_path),
    }
    # Stage every artifact before publishing; commit the PDF last by rename.
    with tempfile.TemporaryDirectory(prefix='.pdf-studio-', dir=output.parent) as temp:
        stage = Path(temp)
        with pdfium.PdfDocument(data) as pdf:
            for index in range(len(pdf)):
                page = pdf[index]
                try:
                    bitmap = page.render(scale=150 / 72)
                    try:
                        image = bitmap.to_pil()
                        image.save(stage / f'page-{index + 1}.png')
                        image.close()
                    finally:
                        bitmap.close()
                finally:
                    page.close()
        (stage / 'document.pdf').write_bytes(data)
        (stage / 'text.txt').write_text('\n\f\n'.join(texts), encoding='utf-8')
        (stage / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        preview_dir.mkdir(exist_ok=True)
        for old in preview_dir.glob('page-*.png'):
            old.unlink()
        for index in range(len(reader.pages)):
            os.replace(stage / f'page-{index + 1}.png', preview_dir / f'page-{index + 1}.png')
        os.replace(stage / 'text.txt', text_path)
        os.replace(stage / 'report.json', output.with_suffix('.report.json'))
        os.replace(stage / 'document.pdf', output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path)
    parser.add_argument('-o', '--output', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--theme', choices=THEMES, default='default')
    parser.add_argument('--lang', choices=['en', 'zh-CN', 'zh-TW', 'ja', 'ko'], default='en')
    parser.add_argument('--list-themes', action='store_true')
    args = parser.parse_args()
    if args.list_themes:
        print(json.dumps(list(THEMES)))
        return
    if not args.input or not args.output:
        parser.error('input and -o/--output are required')
    try:
        if args.input.suffix.lower() not in ('.md', '.markdown') or args.output.suffix.lower() != '.pdf':
            raise ValueError('Use .md/.markdown input and .pdf output')
        if args.input.resolve() == args.output.resolve():
            raise ValueError('Input and output must be different files')
        sidecars = [args.output, args.output.with_suffix('.text.txt'), args.output.with_suffix('.report.json'), args.output.with_suffix('.previews')]
        for target in sidecars:
            if target.is_symlink():
                raise ValueError('Refusing symlink output or sidecar')
            if target.exists() and not args.force:
                raise ValueError('Output or sidecar exists; use --force to replace it')
        preview = args.output.with_suffix('.previews')
        if preview.exists():
            for target in preview.iterdir():
                if target.is_symlink() or not target.is_file() or not target.name.startswith('page-') or target.suffix != '.png':
                    raise ValueError('Preview directory contains unexpected files; choose another output')
        with args.input.open('rb') as handle:
            raw = handle.read(500001)
        if len(raw) > 500000:
            raise ValueError('Markdown exceeds 500000 bytes')
        source = raw.decode('utf-8')
        info = render(source, args.output.absolute(), args.theme, args.lang)
        print(json.dumps(info, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

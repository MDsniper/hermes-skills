#!/usr/bin/env python3
"""Executable integration tests; outputs retained in PDF_STUDIO_TEST_OUTPUT."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from pypdf import PdfReader
from PIL import Image
import http.server
import threading
import pypdfium2 as pdfium

SCRIPT = Path(__file__).with_name('render.py')
ROOT = Path(os.environ.get('PDF_STUDIO_TEST_OUTPUT', str(Path.home() / '.hermes/workspace/markdown-pdf-tests')))
ROOT.mkdir(parents=True, exist_ok=True)


class StudioTests(unittest.TestCase):
    def render(self, name, source, *args):
        md = ROOT / (name + '.md')
        md.write_text(source, encoding='utf-8')
        out = ROOT / (name + '.pdf')
        out.unlink(missing_ok=True)
        proc = subprocess.run([sys.executable, str(SCRIPT), str(md), '-o', str(out), '--force', *args], capture_output=True, text=True, timeout=120)
        (ROOT / (name + '.stdout.txt')).write_text(proc.stdout)
        (ROOT / (name + '.stderr.txt')).write_text(proc.stderr)
        return proc, out

    def test_01_english_pdf_is_real(self):
        proc, out = self.render('english', '# Studio smoke test\n\nHello from Hermes.\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(out.read_bytes().startswith(b'%PDF-'))
        self.assertEqual(len(PdfReader(out).pages), 1)
        self.assertIn('Hello from Hermes.', PdfReader(out).pages[0].extract_text())
        self.assertEqual(json.loads(proc.stdout)['backend'], 'chromium-playwright')


    def test_02_all_five_themes_cjk_tables_code_and_pagebreak(self):
        themes = ['default', 'cjk-auto', 'warm-terra', 'warm-terra-menu', 'mobile']
        source = '''# Multilingual studio

- 中文：你好世界，字体测试。
- 日本語：こんにちは世界。
- 한국어: 안녕하세요 세계.

| Language | Inline code |
| --- | --- |
| Chinese | `终端/文件` |
| Japanese | `日本語/コード` |
| Korean | `한국어/코드` |

```text
代码测试
日本語テスト
한글테스트
```

<!-- pagebreak -->

# Second page marker

Explicit pagination works.
'''
        expected = ['你好世界', 'こんにちは世界', '안녕하세요세계', '终端/文件', '日本語/コード', '한국어/코드', '代码测试', '日本語テスト', '한글테스트']
        for theme in themes:
            with self.subTest(theme=theme):
                proc, out = self.render('cjk-' + theme, source, '--theme', theme, '--lang', 'zh-CN')
                self.assertEqual(proc.returncode, 0, proc.stderr)
                info = json.loads(proc.stdout)
                reader = PdfReader(out)
                self.assertEqual(len(reader.pages), 2)
                text = ''.join(''.join(page.extract_text().split()) for page in reader.pages)
                for phrase in expected:
                    self.assertIn(phrase, text)
                self.assertNotIn('Second page marker', reader.pages[0].extract_text())
                self.assertIn('Second page marker', reader.pages[1].extract_text())
                self.assertEqual(info['missing_glyphs'], [])
                self.assertEqual(info['zero_glyph_codes'], 0)
                self.assertEqual(info['overflow'], [])
                self.assertEqual(info['blocked_requests'], [])
                self.assertTrue(any('NotoSans' in font for font in info['pdf_fonts']))
                self.assertEqual(len(info['previews']), 2)
                for preview in info['previews']:
                    self.assertTrue(Path(preview).is_file())
                self.assertAlmostEqual(float(reader.pages[0].mediabox.width), (148 if theme == 'mobile' else 210) * 72 / 25.4, delta=1)
                self.assertEqual(info['theme'], theme)


    def test_03_external_images_file_links_and_empty_fail_closed(self):
        cases = {
            'remote-image': ('![leak](https://example.invalid/leak.png)', 'Images are disabled'),
            'local-image': ('![secret](file:///fixture-secret.txt)', 'Images are disabled'),
            'data-image': ('![x](data:image/svg+xml;base64,PHN2Zy8+)', 'Images are disabled'),
            'file-link': ('[read](file:///fixture-secret.txt)', 'Link scheme'),
            'javascript-link': ('[run](javascript:alert(1))', 'Link scheme'),
            'relative-link': ('[read](other-page.md)', 'Link scheme'),
            'empty': ('   \n', 'Empty Markdown'),
        }
        for name, (source, message) in cases.items():
            with self.subTest(name=name):
                proc, out = self.render('reject-' + name, source)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(message, proc.stderr)
                self.assertFalse(out.exists(), 'Rejection must leave no PDF')

    def test_04_unsupported_glyph_and_bad_theme_fail_closed(self):
        proc, out = self.render('unsupported-glyph', '# Unsupported\n\n\U00031350')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('Unsupported glyphs', proc.stderr)
        self.assertFalse(out.exists())
        proc, out = self.render('bad-theme', '# Title', '--theme', 'no-such-theme')
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(out.exists())

    def test_05_raw_html_and_links_cannot_fetch_resources(self):
        hits = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'CANARY_HTTP_CONTENT')
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        sentinel = ROOT / 'local-sentinel.txt'
        sentinel.write_text('CANARY_LOCAL_CONTENT')
        url = f'http://127.0.0.1:{server.server_port}/canary'
        try:
            source = f'''# Inert HTML

<script>fetch('{url}')</script>

<img src="{url}">

<iframe src="{sentinel.as_uri()}"></iframe>

<style>@import url({url});</style>

[Allowed but never fetched]({url})
'''
            proc, out = self.render('inert-html', source)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = ''.join(page.extract_text() for page in PdfReader(out).pages)
            self.assertNotIn('CANARY_LOCAL_CONTENT', text)
            self.assertNotIn('CANARY_HTTP_CONTENT', text)
            self.assertIn('<script>', text)
            self.assertEqual(hits, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_06_paths_limits_and_failed_overwrite_preserve_input(self):
        md = ROOT / 'preserved.md'
        md.write_text('# Keep source\n')
        original = md.read_bytes()
        proc = subprocess.run([sys.executable, str(SCRIPT), str(md), '-o', str(md), '--force'], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(md.read_bytes(), original)
        pdf = ROOT / 'not-overwritten.pdf'
        pdf.write_bytes(b'KEEP_EXISTING')
        proc = subprocess.run([sys.executable, str(SCRIPT), str(md), '-o', str(pdf)], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(pdf.read_bytes(), b'KEEP_EXISTING')
        target = ROOT / 'symlink-target.txt'
        target.write_text('KEEP_SYMLINK_TARGET')
        link = ROOT / 'symlink-output.pdf'
        if not link.is_symlink():
            link.symlink_to(target)
        proc = subprocess.run([sys.executable, str(SCRIPT), str(md), '-o', str(link), '--force'], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(target.read_text(), 'KEEP_SYMLINK_TARGET')
        proc, out = self.render('oversize', 'x' * 500001)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('500000', proc.stderr)
        self.assertFalse(out.exists())
        proc = subprocess.run([sys.executable, str(SCRIPT), str(ROOT / 'no-such-file.md'), '-o', str(ROOT / 'missing.pdf')], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)

    @staticmethod
    def border_ratio(image, table, margin_mm):
        # CSS px -> PDF points -> 150dpi raster; margins are part of printed paper.
        scale = 150 / 96
        x = round(margin_mm * 150 / 25.4 + (table['x'] + table['width']) * scale)
        top = round(margin_mm * 150 / 25.4 + table['y'] * scale) + 4
        bottom = round(margin_mm * 150 / 25.4 + (table['y'] + table['height']) * scale) - 4
        gray = image.convert('L')
        painted = sum(min(gray.getpixel((col, row)) for col in range(x - 4, x + 4)) < 220 for row in range(top, bottom))
        return painted / (bottom - top), (x - 4, top, x + 4, bottom)

    def test_07_uneven_tables_have_painted_right_borders_all_themes(self):
        source = '''# Uneven table

| ID | Long module question | Details |
| --- | --- | --- |
| A | 为什么要检查表格右边框？日本語でも確認します。 | Verify every painted border, not only extracted text. |
| B | 한국어 표의 긴 내용을 확인합니다. | VeryLongUnbrokenIdentifierABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 |
| C | Mixed CJK `终端/한국어/日本語` | Finish with all columns visible. |
'''
        checks = []
        for theme in ['default', 'cjk-auto', 'warm-terra', 'warm-terra-menu', 'mobile']:
            proc, out = self.render('uneven-' + theme, source, '--theme', theme)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            info = json.loads(proc.stdout)
            self.assertEqual(info['page_count'], 1)
            self.assertEqual(info['overflow'], [])
            self.assertEqual(len(info['tables']), 1)
            with Image.open(info['previews'][0]) as image:
                ratio, box = self.border_ratio(image, info['tables'][0], 10 if theme == 'mobile' else 18 if theme in ['default', 'cjk-auto'] else 15)
                self.assertGreater(ratio, .98, (theme, ratio))
                broken = image.copy()
                broken.paste('white', box)
                negative_ratio, _ = self.border_ratio(broken, info['tables'][0], 10 if theme == 'mobile' else 18 if theme in ['default', 'cjk-auto'] else 15)
                self.assertEqual(negative_ratio, 0)
                if theme == 'default':
                    broken.save(ROOT / 'negative-control-missing-border.png')
                broken.close()
            checks.append({'theme': theme, 'painted_right_border_ratio': ratio, 'negative_control_ratio': negative_ratio, 'pdf': str(out)})
        (ROOT / 'border-validation.json').write_text(json.dumps(checks, indent=2))

    def test_08_multi_page_table_preserves_rows_headers_and_borders(self):
        source = '# Paginated table\n\n| Record | 内容 / 내용 |\n| --- | --- |\n' + ''.join(f'| Row-{i:03d} | 中文测试 日本語テスト 한국어테스트 |\n' for i in range(75))
        results = []
        for theme in ['default', 'mobile']:
            proc, out = self.render('long-table-' + theme, source, '--theme', theme)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            info = json.loads(proc.stdout)
            reader = PdfReader(out)
            self.assertGreater(len(reader.pages), 1)
            text = '\n'.join(page.extract_text() for page in reader.pages)
            for i in range(75):
                self.assertIn(f'Row-{i:03d}', text)
            for page in reader.pages:
                self.assertIn('Record', page.extract_text())
            # Each actual raster must contain a long vertical stroke at the known outer boundary.
            counts = []
            for path in info['previews']:
                with Image.open(path) as image:
                    gray = image.convert('L')
                    margin = (10 if theme == 'mobile' else 18) * 150 / 25.4
                    x = round(margin + info['content_width'] * 150 / 96)
                    count = sum(min(gray.getpixel((col, row)) for col in range(x - 4, x + 4)) < 220 for row in range(round(margin), image.height - round(margin)))
                    self.assertGreater(count, 100)
                    counts.append(count)
            results.append({'theme': theme, 'pages': len(reader.pages), 'rows': 75, 'right_border_ink_rows_by_page': counts})
        (ROOT / 'pagination-validation.json').write_text(json.dumps(results, indent=2))


    def test_09_cjk_has_embedded_truetype_and_pdfium_text(self):
        for theme in ['default', 'cjk-auto', 'warm-terra', 'warm-terra-menu', 'mobile']:
            path = ROOT / ('cjk-' + theme + '.pdf')
            with pdfium.PdfDocument(path) as pdf:
                text = ''
                for index in range(len(pdf)):
                    page = pdf[index]
                    textpage = page.get_textpage()
                    text += textpage.get_text_range()
                    textpage.close()
                    page.close()
                compact = ''.join(text.split())
                for phrase in ['你好世界', 'こんにちは世界', '안녕하세요세계', '代码测试', '日本語テスト', '한글테스트']:
                    self.assertIn(phrase, compact)
            for page in PdfReader(path).pages:
                for ref in page['/Resources']['/Font'].values():
                    font = ref.get_object()
                    self.assertEqual(font['/Subtype'], '/Type0')
                    child = font['/DescendantFonts'][0].get_object()
                    self.assertEqual(child['/Subtype'], '/CIDFontType2')
                    self.assertIn('/FontFile2', child['/FontDescriptor'].get_object())

    def test_10_pagebreak_in_fenced_code_is_literal(self):
        proc, out = self.render('literal-pagebreak', '# Literal directive\n\n```html\n<!-- pagebreak -->\n```\n\nNo page break here.\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        reader = PdfReader(out)
        self.assertEqual(len(reader.pages), 1)
        self.assertIn('<!-- pagebreak -->', reader.pages[0].extract_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)

import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('build', Path(__file__).with_name('build.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BuildTests(unittest.TestCase):
    def test_js_quotes_and_identifiers(self):
        src = '''<p>Eye</p><script>// The eye's label must remain valid.\nvar Eye=1;var label='The eye';</script>'''
        translated, missing = b.apply_translations(src, [('The eye', "L'œil \\ test\nnext", '.jsStrings.eye')])
        self.assertFalse(missing)
        self.assertIn('var Eye=1', translated)
        self.assertIn("// The eye's label", translated)
        script = translated.split('<script>')[1].split('</script>')[0]
        subprocess.run(['node', '--check'], input=script, text=True, check=True, capture_output=True)

    def test_canonical_and_hreflang_idempotent(self):
        src = '<html lang="en"><link rel="canonical" href="https://cspace-beryl.vercel.app/"></html>'
        html = b.apply_hreflang(b.apply_lang_meta(src, b.LANG_CONFIG['ko']), b.LANG_CONFIG['ko'])
        self.assertEqual(html, b.apply_hreflang(html, b.LANG_CONFIG['ko']))
        self.assertIn(b.BASE_URL + '/ko', html)

    def test_github_project_routes(self):
        self.assertEqual(b.public_url('/ko/light'), '/cspace/ko/light/')
        self.assertEqual(b.public_url('/cspace/ko/light/'), '/cspace/ko/light/')
        self.assertEqual(b.public_url('/tube.png'), '/cspace/tube.png')
        self.assertEqual(b.public_url('https://example.com/'), 'https://example.com/')

    def test_special_js_strings(self):
        src = b.SRC_HTML.read_text()
        for lang in ('fr', 'it', 'id'):
            data = json.loads((b.ROOT / 'i18n' / (lang + '.json')).read_text())
            translated, _ = b.apply_special(src, b.special_replacements(data, lang))
            import re
            for attrs, script in re.findall(r'<script([^>]*)>(.*?)</script>', translated, re.S):
                if 'ld+json' not in attrs:
                    subprocess.run(['node', '--check'], input=script, text=True, check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()

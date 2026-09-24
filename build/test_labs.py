import json
import re
import tempfile
import unittest
from pathlib import Path
import labs


class LabBuildTests(unittest.TestCase):
    def test_standard_observer_subset(self):
        data = labs.observer_data()
        for rows in data.values():
            self.assertEqual(len(rows), 81)
            self.assertEqual([row[0] for row in rows], list(range(380, 781, 5)))
        self.assertTrue(all(row[3] == 0 for row in data['ten'] if row[0] >= 560))

    def test_bilingual_self_contained_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            urls = labs.generate(root, 'https://example.org/project')
            self.assertEqual(len(urls), 18)
            self.assertEqual(len(list(root.rglob('*.html'))), 18)
            for lang in ('', 'ko/'):
                hub = (root / lang / 'labs/index.html').read_text()
                self.assertEqual(hub.count('class="card"'), 8)
                for lab in labs.LABS:
                    page = (root / lang / 'labs' / lab['slug'] / 'index.html').read_text()
                    self.assertIn('CC BY-SA 4.0', page)
                    self.assertNotIn('<script src=', page)
                    self.assertIn(lab['title'][int(bool(lang))], page)
                    self.assertIn('id="controls"', page)
                    self.assertIn('id="results"', page)
                    cfg = re.search(r'<script id="lab-config" type="application/json">(.*?)</script>', page)[1]
                    self.assertEqual(json.loads(cfg)['slug'], lab['slug'])

    def test_book_links_idempotent(self):
        source = '<html><head></head><body><header></header><section class="chapter" id="spaces"><div>Text</div></section></body></html>'
        linked = labs.book_links(source, 'ko')
        self.assertIn('/ko/labs/gamma/', linked)
        self.assertEqual(linked.count('class="lab-related"'), 1)
        self.assertEqual(labs.book_links(linked, 'ko'), linked)
        self.assertNotIn('class="lab-related"', labs.book_links('<html></html>', 'ko'))


if __name__ == '__main__':
    unittest.main()

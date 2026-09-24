import json
import re
import unittest
from pathlib import Path
import reading
import build as builder


class ReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).resolve().parent.parent / 'index32.html').read_text()
        cls.en = json.loads(builder.EN_JSON.read_text())

    def test_inventory_has_every_chapter_and_figure(self):
        sections, owners = reading.inventory(self.source)
        self.assertEqual(len(sections), 16)
        self.assertEqual(len(sections['mixing']['figures']), 3)
        self.assertEqual(owners['fig-prism'], 'light')
        self.assertEqual(owners['coda'], 'coda')

    def test_cover_contains_choices_and_legacy_route_map(self):
        page = reading.decorate(self.source, self.source, 'ko', builder.BASE_URL, 'cover')
        self.assertNotRegex(page, r'<section class="chapter')
        self.assertIn('/cspace/ko/light/', page)
        self.assertIn('/cspace/ko/book/', page)
        self.assertIn('장별로 읽기', page)
        config = json.loads(re.search(r'<script id="reading-config" type="application/json">(.*?)</script>',page)[1])
        self.assertEqual(config['anchors']['fig-prism'], builder.BASE_URL+'/ko/light/')
        self.assertEqual(config['anchors']['coda'], builder.BASE_URL+'/ko/book/')

    def test_chapter_is_single_and_all_toc_targets_exist(self):
        for n, slug in enumerate(reading.CHAPTERS,1):
            chapter = builder.build_chapter_html(self.source,builder.LANG_CONFIG['en'],'en',slug,'ch'+str(n),n,self.en)
            chapter = reading.decorate(chapter,self.source,'en',builder.BASE_URL,'chapter',slug)
            self.assertEqual(re.findall(r'<section class="chapter" id="([^"]+)"',chapter),[slug])
            self.assertIn('<h1 id="'+slug+'-h"',chapter)
            ids=set(re.findall(r'\bid="([^"]+)"',chapter))
            targets=re.findall(r'data-reading-anchor="([^"]+)"',chapter)
            self.assertGreaterEqual(len(targets),2)
            self.assertTrue(set(targets)<=ids)
            self.assertIn('class="reading-prev"',chapter)
            self.assertIn('class="reading-next"',chapter)
            self.assertNotIn('chapter-scroll-shim',chapter)
            self.assertNotIn('class="chapnav"',chapter)

    def test_complete_book_keeps_all_sections(self):
        page=reading.decorate(self.source,self.source,'en',builder.BASE_URL,'book')
        sections,_=reading.inventory(page)
        self.assertEqual(len(sections),16)
        self.assertIn('href="'+builder.BASE_URL+'/book/"',page)
        self.assertIn('id="reading-chapter-switch"',page)

    def test_changed_source_fails_instead_of_publishing_full_chapter(self):
        with self.assertRaises(ValueError):
            builder.reduce_to_chapter('<html><section></section></html>',1)


if __name__=='__main__':
    unittest.main()

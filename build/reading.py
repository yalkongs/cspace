"""Static chapter-first reading, with an optional complete-book edition.

Build from the translated book so section labels and legacy anchors remain
consistent with the actual content, including partially translated editions.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ['light', 'eye', 'mixing', 'wheel', 'space', 'harmony', 'spaces',
            'interaction', 'practice', 'glossary', 'names', 'pigments', 'nature', 'practice2']
SECTIONS = re.compile(r'<section\b[^>]*\bid="([^"]+)"[^>]*>.*?</section>', re.S)
LABEL_KEYS = ['start', 'full', 'chapters', 'contents', 'previous', 'next', 'cover',
              'intro', 'labs', 'chapter_mode', 'full_mode', 'choice', 'end']
LABELS = {
 'en': ['Read chapter by chapter', 'Read the complete book', 'Chapters', 'In this chapter', 'Previous chapter', 'Next chapter', 'Cover', 'Introduction', 'Laboratory', 'Chapter reading', 'Continuous reading', 'Choose how to read', 'Continue with the chronology & palette'],
 'ko': ['장별로 읽기', '전체 이어 읽기', '장 이동', '이 장의 소목차', '이전 장', '다음 장', '표지', '도입', '실험실', '장별 읽기', '전체 연속 읽기', '읽는 방식 선택', '연대기와 팔레트로 이어가기'],
 'ja': ['章ごとに読む', '全編を続けて読む', '章を選ぶ', 'この章の目次', '前の章', '次の章', '表紙', '導入', '実験室', '章ごとの閲覧', '連続閲覧', '読み方を選ぶ', '年表とパレットへ'],
 'es': ['Leer por capítulos', 'Leer el libro completo', 'Capítulos', 'En este capítulo', 'Capítulo anterior', 'Capítulo siguiente', 'Portada', 'Introducción', 'Laboratorio', 'Lectura por capítulos', 'Lectura continua', 'Elige cómo leer', 'Continuar con la cronología y la paleta'],
 'zh': ['按章阅读', '连续阅读全书', '选择章节', '本章目录', '上一章', '下一章', '封面', '导读', '实验室', '章节阅读', '连续阅读', '选择阅读方式', '继续阅读年表与调色板'],
 'fr': ['Lire par chapitre', 'Lire le livre entier', 'Chapitres', 'Dans ce chapitre', 'Chapitre précédent', 'Chapitre suivant', 'Couverture', 'Introduction', 'Laboratoire', 'Lecture par chapitre', 'Lecture continue', 'Choisir un mode de lecture', 'Continuer avec la chronologie et la palette'],
 'de': ['Kapitelweise lesen', 'Das ganze Buch lesen', 'Kapitel', 'In diesem Kapitel', 'Vorheriges Kapitel', 'Nächstes Kapitel', 'Titelseite', 'Einführung', 'Labor', 'Kapitelweise lesen', 'Fortlaufend lesen', 'Lesemodus wählen', 'Weiter zur Chronologie und Palette'],
 'pt': ['Ler por capítulos', 'Ler o livro completo', 'Capítulos', 'Neste capítulo', 'Capítulo anterior', 'Próximo capítulo', 'Capa', 'Introdução', 'Laboratório', 'Leitura por capítulos', 'Leitura contínua', 'Escolha como ler', 'Continuar com a cronologia e a paleta'],
 'it': ['Leggi per capitoli', 'Leggi il libro completo', 'Capitoli', 'In questo capitolo', 'Capitolo precedente', 'Capitolo successivo', 'Copertina', 'Introduzione', 'Laboratorio', 'Lettura per capitoli', 'Lettura continua', 'Scegli come leggere', 'Continua con cronologia e tavolozza'],
 'vi': ['Đọc từng chương', 'Đọc toàn bộ sách', 'Chương', 'Trong chương này', 'Chương trước', 'Chương sau', 'Trang bìa', 'Giới thiệu', 'Phòng thí nghiệm', 'Đọc theo chương', 'Đọc liên tục', 'Chọn cách đọc', 'Tiếp tục với niên biểu và bảng màu'],
 'id': ['Baca per bab', 'Baca seluruh buku', 'Bab', 'Dalam bab ini', 'Bab sebelumnya', 'Bab berikutnya', 'Sampul', 'Pengantar', 'Laboratorium', 'Baca per bab', 'Baca berkelanjutan', 'Pilih cara membaca', 'Lanjut ke kronologi dan palet'],
}


def plain(value):
    return html.unescape(re.sub(r'<[^>]+>', '', value)).strip()


def inventory(source):
    """Return actual section titles, all anchor owners, and figure mini-contents."""
    sections, owners = {}, {}
    for match in SECTIONS.finditer(source):
        slug, section = match[1], match[0]
        if slug not in CHAPTERS + ['chronology', 'coda']:
            continue
        heading = re.search(r'<h2\b[^>]*>(.*?)</h2>', section, re.S)
        if not heading:
            raise ValueError(f'Missing heading: {slug}')
        figures = re.findall(r'<div class="figure" id="([^"]+)">\s*<div class="figure-head">\s*<span class="figure-title">(.*?)</span>', section, re.S)
        sections[slug] = {'title': plain(heading[1]), 'figures': [(i, plain(t)) for i,t in figures]}
        for anchor in re.findall(r'\bid="([^"]+)"', section):
            if anchor in owners:
                raise ValueError(f'Duplicate book anchor: {anchor}')
            owners[anchor] = slug
    if list(sections) != CHAPTERS + ['chronology', 'coda']:
        raise ValueError('Expected 14 chapters, chronology and coda in source order')
    return sections, owners


def decorate(source, original, lang, base, mode, slug=None):
    sections, owners = inventory(original)
    labels = dict(zip(LABEL_KEYS, LABELS[lang]))
    e = html.escape
    prefix = '' if lang == 'en' else '/' + lang
    root = base + prefix + '/'
    book = root + 'book/'
    lab = base + ('/ko' if lang == 'ko' else '') + '/labs/'
    href = lambda name: root + name + '/'
    source = re.sub(r'<script id="chapter-scroll-shim">.*?</script>', '', source, flags=re.S)
    source = re.sub(r'<nav class="chapnav".*?</nav>', '', source, count=1, flags=re.S)
    source = re.sub(r'<nav class="chapter-nav".*?</nav>', '', source, flags=re.S)
    source = source.replace('<body>', f'<body class="reading-{mode}">', 1)

    if mode == 'cover':
        source = SECTIONS.sub(lambda m: '' if m[1] in sections else m[0], source)
        choices = (f'<nav class="reading-choices" aria-label="{e(labels["choice"])}">'
                   f'<a class="reading-start" href="{href(CHAPTERS[0])}">{e(labels["start"])} →</a>'
                   f'<a href="{book}">{e(labels["full"])}</a>'
                   f'<a href="{lab}">{e(labels["labs"])}</a></nav>')
        source = re.sub(r'<div class="scrollcue".*?</div>', choices, source, count=1, flags=re.S)
        tools = ''
    else:
        # Ordinary links, not a JS-only select: all chapters work without scripts.
        items = ''.join(f'<a href="{href(ch)}"' + (' aria-current="page"' if ch == slug else '') + f'><span>{i:02}</span> {e(sections[ch]["title"])}</a>' for i,ch in enumerate(CHAPTERS,1))
        chapter_menu = f'<details class="reading-menu"><summary>{str(CHAPTERS.index(slug)+1) + " / 14 · " if slug else ""}{e(labels["chapters"])}</summary><nav aria-label="{e(labels["chapters"])}">{items}</nav></details>'
        if mode == 'chapter':
            entries = [(slug + '-h', labels['intro'])] + sections[slug]['figures']
            links = ''.join(f'<a href="#{anchor}" data-reading-anchor="{anchor}">{e(title)}</a>' for anchor,title in entries)
            mini = f'<details class="reading-menu reading-sections"><summary>{e(labels["contents"])} <span id="reading-position" aria-hidden="true"></span></summary><nav aria-label="{e(labels["contents"])}">{links}</nav></details>'
            switch = f'<a class="reading-mode-switch" href="{book}#{slug}">{e(labels["full"])}</a>'
            tools = chapter_menu + mini + switch
            n = CHAPTERS.index(slug)
            previous = (href(CHAPTERS[n-1]), labels['previous'], sections[CHAPTERS[n-1]]['title']) if n else (root, labels['cover'], labels['choice'])
            nxt = (href(CHAPTERS[n+1]), labels['next'], sections[CHAPTERS[n+1]]['title']) if n < 13 else (book+'#chronology', labels['end'], sections['chronology']['title'])
            pager = '<nav class="reading-pager" aria-label="' + e(labels['chapters']) + '">'
            for direction, (url, label, title) in zip(('prev','next'), (previous,nxt)):
                pager += f'<a class="reading-{direction}" href="{url}"><span>{"← " if direction == "prev" else ""}{e(label)}{" →" if direction == "next" else ""}</span><strong>{e(title)}</strong></a>'
            pager += '</nav>'
            source = source.replace('<footer>', pager + '<footer>', 1)
            breadcrumb = f'<p class="reading-location"><a href="{root}">{e(labels["cover"])}</a> / {e(labels["chapter_mode"])} · {n+1} / 14</p>'
            source = source.replace('<main id="top">', '<main id="top">' + breadcrumb, 1)
            source = re.sub(r'<h2 id="' + slug + r'-h">(.*?)</h2>', r'<h1 id="' + slug + r'-h" tabindex="-1">\1</h1>', source, count=1, flags=re.S)
        else:
            tools = chapter_menu + f'<span class="reading-mode-label">{e(labels["full_mode"])}</span><a class="reading-mode-switch" id="reading-chapter-switch" href="{href(CHAPTERS[0])}">{e(labels["start"])}</a>'
            # A small conventional anchor list also includes the two appendices.
            contents = '<nav class="reading-book-contents" aria-label="' + e(labels['contents']) + '">'
            contents += ''.join(f'<a href="#{ch}">{str(i) + ". " if i <= 14 else ""}{e(sections[ch]["title"])}</a>' for i,ch in enumerate(sections,1)) + '</nav>'
            source = re.sub(r'<div class="scrollcue".*?</div>', contents, source, count=1, flags=re.S)
            canonical = book
            source = re.sub(r'(<link rel="canonical" href=")[^"]+', lambda m:m[1]+canonical, source)
            source = re.sub(r'(<meta (?:property="og:url"|name="citation_fulltext_html_url") content=")[^"]+', lambda m:m[1]+canonical, source)
            # Existing alternate links use the same cover route; append /book/.
            source = re.sub(r'(<link rel="alternate" hreflang="[^"]+" href=")([^"]+)', lambda m:m[1]+m[2].rstrip('/')+'/book/', source)

    if tools:
        source = source.replace('</header>', f'</header><div class="reading-tools" id="reading-tools">{tools}</div>', 1)
    # The masthead always leads to the cover, not a huge anchor-based book.
    source = re.sub(r'(<a class="wordmark" href=")[^"]+', lambda m:m[1]+root, source, count=1)
    source = re.sub(r'(<a class="skip-link" href=")[^"]+', lambda m:m[1]+('#'+slug+'-h' if slug else '#top'), source, count=1)
    ids = set(re.findall(r'\bid="([^"]+)"', source))

    def route_anchor(match):
        anchor = match[1]
        if anchor in ids:
            return match[0]
        owner = owners.get(anchor)
        target = href(owner) if owner in CHAPTERS else book
        return f'href="{target}#{anchor}"'

    source = re.sub(r'href="#([^"]+)"', route_anchor, source)
    css = (ROOT / 'reading/navigation.css').read_text()
    source = source.replace('</head>', '<style id="reading-style">'+css+'</style></head>',1)
    config = {'mode':mode, 'root':root, 'book':book, 'chapters':CHAPTERS,
              'anchors':{anchor: (href(owner) if owner in CHAPTERS else book) for anchor,owner in owners.items()} if mode == 'cover' else {}}
    script = '<script id="reading-config" type="application/json">'+json.dumps(config,ensure_ascii=False).replace('</','<\\/')+'</script><script>'+(ROOT/'reading/navigation.js').read_text()+'</script>'
    source = source.replace('</body>', script+'</body>',1)
    return source

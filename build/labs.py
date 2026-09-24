"""Generate self-contained, bilingual static experiment pages and book links."""
import csv
import hashlib
import html
import json
import math
import re
from pathlib import Path
from lab_content import LABS

ROOT = Path(__file__).resolve().parent.parent
EXP = ROOT / 'experiments'
CHAPTER_LABELS = {
    'light': ('1. Light', '1. 빛'), 'eye': ('2. The Eye', '2. 눈'),
    'mixing': ('3. Mixing', '3. 혼색'), 'spaces': ('7. Color Spaces', '7. 색 공간'),
    'interaction': ('8. Interaction', '8. 색의 상호작용'),
    'nature': ('13. Nature', '13. 자연'), 'practice2': ('14. Display & Production', '14. 화면과 제작 환경'),
}


def observer_data():
    data = {}
    for key, name in [('two', '1931_2deg'), ('ten', '1964_10deg')]:
        path = EXP / 'data' / f'CIE_xyz_{name}.csv'
        meta = json.loads(path.with_suffix('.csv_metadata.json').read_text())
        expected = next(c['checksum'] for c in meta['checksums'] if c['hashMethod'] == 'sha256')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'CIE data checksum mismatch: {name}')
        rows = []
        for row in csv.reader(path.read_text().splitlines()):
            if not row:
                continue
            values = list(map(float, row))
            if not (380 <= values[0] <= 780 and values[0] % 5 == 0):
                continue
            # CIE metadata: 1964 z-bar domain ends at 559 nm; zero extrapolation.
            if key == 'ten' and values[0] >= 560:
                values[3] = 0.0
            if not all(math.isfinite(v) for v in values):
                raise ValueError('Unexpected non-finite CIE data')
            rows.append(values)
        assert len(rows) == 81
        data[key] = rows
    return data


def book_links(source, lang):
    """Only compact links, not eight new long sections in the existing book."""
    if 'class="chapter"' not in source or 'class="lab-related"' in source:
        return source
    ko = lang == 'ko'
    prefix = '/ko/labs/' if ko else '/labs/'
    label = '실험실 · 8개의 심화 실험' if ko else 'Laboratory · 8 deeper experiments'
    style = '''<style>.lab-related{border-top:1px solid #aaa69b;margin:36px auto 0;padding:22px 0;max-width:1140px;font:14px/1.8 system-ui,sans-serif}.lab-related strong{display:block;margin-bottom:10px}.lab-related a{display:inline-block;margin:0 22px 10px 0;color:inherit;text-underline-offset:4px;padding:8px 0}.lab-hub-entry{display:block;margin:24px auto;padding:16px 24px;max-width:1140px;color:inherit;font:14px/1.6 system-ui,sans-serif}.lab-related a:focus-visible,.lab-hub-entry:focus-visible{outline:3px solid #215591;outline-offset:3px}</style>'''
    # The existing masthead is fixed and 56 px tall; keep the entry below it.
    style = style.replace('margin:24px auto;padding:16px', 'margin:72px auto 24px;padding:16px')
    source = source.replace('</head>', style + '</head>', 1)
    source = source.replace('</header>', f'</header><a class="lab-hub-entry" href="{prefix}">{label} →</a>', 1)

    def attach(match):
        section, slug = match[0], match[1]
        labs = [lab for lab in LABS if slug in lab['chapters']]
        if not labs:
            return section
        links = ''.join(f'<a href="{prefix}{lab["slug"]}/">{html.escape(lab["title"][int(ko)])} ↗</a>' for lab in labs)
        title = '이 장에서 이어지는 실험' if ko else 'Explore this chapter in the laboratory'
        fallback = '' if lang in ('ko', 'en') else ' · English'
        card = f'<aside class="lab-related" aria-label="{title}"><strong>{title}{fallback}</strong>{links}<a href="{prefix}">{label} →</a></aside>'
        # Keep the card inside the section's final container div.
        end = section.rfind('</div>')
        return section[:end] + card + section[end:]

    return re.sub(r'<section class="chapter" id="([^"]+)"[^>]*>.*?</section>', attach, source, flags=re.S)


def generate(output, base):
    css = (EXP / 'labs.css').read_text()
    js = (EXP / 'color-math.js').read_text() + '\n' + (EXP / 'labs.js').read_text()
    data = json.dumps(observer_data(), separators=(',', ':'), allow_nan=False)
    urls = []
    for lang in ('en', 'ko'):
        ko = lang == 'ko'
        pick = lambda a: a[int(ko)]
        prefix = '/ko' if ko else ''
        href = lambda path: base + prefix + path
        title = pick(['The colour laboratory', '색채 실험실'])
        hub = href('/labs/')
        for index, lab in enumerate([None] + LABS):
            slug = lab['slug'] + '/' if lab else ''
            url = hub + slug
            urls.append(url)
            name = pick(lab['title']) if lab else title
            question = pick(lab['question']) if lab else pick(['Eight experiments connecting light, perception and reproduction.', '빛·지각·색 재현을 연결하는 여덟 가지 실험.'])
            alternate = base + ('' if ko else '/ko') + '/labs/' + slug
            langlinks = f'<a href="{alternate}" lang="{"en" if ko else "ko"}">{"English" if ko else "한국어"}</a>'
            content = f'<div class="breadcrumb"><a href="{href("/")}">{pick(["Book", "책"])}</a> / <a href="{hub}">{title}</a>' + (f' / {index:02}' if lab else '') + '</div>'
            content += f'<div class="kicker">The Book of Color / {"Laboratory " + str(index).zfill(2) if lab else "Eight experiments"}</div><h1>{html.escape(name)}</h1><p class="lead">{html.escape(question)}</p>'
            if lab:
                content += f'<p class="intro">{html.escape(pick(lab["intro"]))}</p>'
                content += '<ol class="steps">' + ''.join(f'<li>{step}</li>' for step in pick([['Predict','Change one variable','Compare','Explain'],['예측하기','변수 하나 바꾸기','비교하기','설명하기']])) + '</ol>'
                content += f'<p class="note">{html.escape(pick(lab["task"]))}</p>'
                content += f'<noscript><p>{pick(["Enable JavaScript to run the experiment. The theory and sources remain readable below.","실험 조작에는 JavaScript가 필요합니다. 아래 이론과 출처는 그대로 읽을 수 있습니다."])}</p></noscript>'
                content += f'<div class="lab-workbench"><form class="controls" id="controls"><h2>{pick(["Change a variable", "변수 조작"])}</h2></form><section class="results" id="results" aria-label="{pick(["Experiment results", "실험 결과"])}"></section></div>'
                content += f'<div class="text-grid"><section><h2>{pick(["What this explains", "이 실험이 설명하는 원리"])}</h2><p>{html.escape(pick(lab["theory"]))}</p><p class="formula">{html.escape(lab["formula"])}</p></section><aside class="note"><h2>{pick(["Model and limits", "모형과 한계"])}</h2><p>{html.escape(pick(lab["limits"]))}</p></aside></div>'
                content += f'<details><summary>{pick(["Sources, data and calculation notes", "출처·데이터·계산 안내"])}</summary><ul class="sources">' + ''.join(f'<li><a href="{url}">{html.escape(label)}</a></li>' for label, url in lab['sources']) + '</ul>'
                content += f'<p>{pick(["All previews are sRGB approximations. Compare numbers and curves as well as patches; display settings and ambient light affect what you see.","모든 미리보기는 sRGB 근사색입니다. 색 패치뿐 아니라 수치와 곡선을 함께 비교하세요. 화면 설정과 주변광은 보이는 결과에 영향을 줍니다."])}</p></details>'
                content += f'<p>{pick(["Read the related chapters: ","관련 장으로 돌아가기: "])}' + ' · '.join(f'<a href="{href("/" + chapter + "/")}">{pick(CHAPTER_LABELS[chapter])}</a>' for chapter in lab['chapters']) + '</p>'
                previous = LABS[index-2] if index > 1 else None
                nxt = LABS[index] if index < len(LABS) else None
                content += '<nav class="pager" aria-label="' + pick(['Experiment navigation','실험 이동']) + '">'
                content += f'<a href="{hub + previous["slug"] + "/" if previous else hub}">← {html.escape(pick(previous["title"])) if previous else title}</a>'
                content += f'<a href="{hub + nxt["slug"] + "/" if nxt else hub}">{html.escape(pick(nxt["title"])) if nxt else title} →</a></nav>'
                content += '<script id="observer-data" type="application/json">' + data + '</script><script id="lab-config" type="application/json">' + json.dumps({'slug':lab['slug'],'lang':lang}) + '</script><script>' + js + '</script>'
            else:
                content += f'<p class="intro">{pick(["One question, one experiment, one page. Start with the first three to connect the book’s visual intuition with colour calculations. Each experiment includes a task, live comparison, explanation and its limits.","하나의 질문, 하나의 실험, 하나의 페이지. 첫 세 실험으로 책에서 얻은 시각적 직관을 색 계산과 연결하세요. 각 실험에는 관찰 과제, 실시간 비교, 원리 설명과 모형의 한계가 담겨 있습니다."])}</p>'
                content += '<div class="cards">' + ''.join(f'<a class="card" href="{hub}{item["slug"]}/"><span class="kicker">{i:02} / {pick(["Experiment", "실험"])}</span><h2>{html.escape(pick(item["title"]))}</h2><p>{html.escape(pick(item["question"]))}</p></a>' for i,item in enumerate(LABS,1)) + '</div>'
                content += f'<p class="note">{pick(["Suggested path: XYZ → mixing → colour difference → rendering and gamut mapping → appearance, printing and structural colour. English and Korean editions are complete; the existing full book remains available.","추천 순서: XYZ → 혼합 → 색차 → 연색과 색역 매핑 → 색 외관·인쇄·구조색. 실험실은 한국어·영어로 제공하며, 기존 전체 책 읽기도 유지합니다."])}</p>'
            footer = pick(['CIE observer data (2019), adapted to 380–780 nm / 5 nm; 1964 z̄ uses zero extrapolation above 559 nm. Dataset and adaptation: CC BY-SA 4.0. Analytical spectra are educational models.', 'CIE 표준 관찰자 데이터(2019)를 380–780 nm / 5 nm로 발췌. 1964 z̄는 559 nm 밖에서 0으로 외삽. 데이터와 변형 데이터: CC BY-SA 4.0. 해석식 스펙트럼은 교육용 모형입니다.'])
            page = f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(name)} — The Book of Color</title><meta name="description" content="{html.escape(question,quote=True)}"><link rel="canonical" href="{url}"><link rel="alternate" hreflang="{lang}" href="{url}"><link rel="alternate" hreflang="{'en' if ko else 'ko'}" href="{alternate}"><meta property="og:title" content="{html.escape(name,quote=True)}"><meta property="og:url" content="{url}"><style>{css}</style></head><body><a class="skip" href="#main">{pick(['Skip to content','본문으로 건너뛰기'])}</a><header class="masthead"><a class="brand" href="{href('/')}">The Book of Color</a><nav aria-label="{pick(['Main navigation','주요 탐색'])}"><a href="{hub}">{pick(['Laboratory','실험실'])}</a>{langlinks}</nav></header><main id="main">{content}</main><footer><p>{footer} <a href="https://doi.org/10.25039/CIE.DS.xvudnb9b">CIE 1931</a> · <a href="https://doi.org/10.25039/CIE.DS.sqksu2n5">CIE 1964</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> · <a href="https://github.com/yalkongs/cspace/tree/main/experiments/data">{pick(['Original data & changes','원본 데이터·변경 내역'])}</a></p></footer></body></html>'''
            target = output / (prefix.strip('/') + '/labs/' + slug).lstrip('/') / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(page, encoding='utf-8')
    return urls

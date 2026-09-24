#!/usr/bin/env python3
"""Build the latest root index<N>.html and i18n JSON into GitHub Pages HTML.

HTML and JavaScript string translations are handled separately. All generated
pages, directory routes and static assets are validated before publication.
"""

import argparse
import datetime
import html as html_lib
import json
import re
import shutil
import subprocess
import sys
import labs
from urllib.parse import urlsplit, urlunsplit
from pathlib import Path

# Build-time timestamp for {LAST_UPDATED} placeholders in the footer.
LAST_UPDATED = datetime.date.today().isoformat()

ROOT = Path(__file__).resolve().parent.parent
SRC_HTML = ROOT / "index32.html"
EN_JSON = ROOT / "i18n" / "en.json"
DIST = ROOT / "site"
BASE_URL = "https://yalkongs.github.io/cspace"
LEGACY_URL = "https://cspace-beryl.vercel.app"
STATIC = ROOT / "static"

LANG_CONFIG = {
    "en": {  # 영문 baseline — 원본 그대로 + hreflang 삽입만
        "json": None,
        "htmlLang": "en",
        "ogLocale": "en_US",
        "canonicalPath": "/",
        "outputDir": DIST / "en",
    },
    "ko": {
        "json": ROOT / "i18n" / "ko.json",
        "htmlLang": "ko",
        "ogLocale": "ko_KR",
        "canonicalPath": "/ko",
        "outputDir": DIST / "ko",
    },
    "ja": {
        "json": ROOT / "i18n" / "ja.json",
        "htmlLang": "ja",
        "ogLocale": "ja_JP",
        "canonicalPath": "/ja",
        "outputDir": DIST / "ja",
    },
    "es": {
        "json": ROOT / "i18n" / "es.json",
        "htmlLang": "es",
        "ogLocale": "es_ES",  # es-419 검토 후 변경 가능
        "canonicalPath": "/es",
        "outputDir": DIST / "es",
    },
    "zh": {
        "json": ROOT / "i18n" / "zh.json",
        "htmlLang": "zh-Hans",
        "ogLocale": "zh_CN",
        "canonicalPath": "/zh",
        "outputDir": DIST / "zh",
    },
    "fr": {
        "json": ROOT / "i18n" / "fr.json",
        "htmlLang": "fr",
        "ogLocale": "fr_FR",
        "canonicalPath": "/fr",
        "outputDir": DIST / "fr",
    },
    "de": {
        "json": ROOT / "i18n" / "de.json",
        "htmlLang": "de",
        "ogLocale": "de_DE",
        "canonicalPath": "/de",
        "outputDir": DIST / "de",
    },
    "pt": {
        "json": ROOT / "i18n" / "pt.json",
        "htmlLang": "pt-BR",
        "ogLocale": "pt_BR",
        "canonicalPath": "/pt",
        "outputDir": DIST / "pt",
    },
    "it": {
        "json": ROOT / "i18n" / "it.json",
        "htmlLang": "it",
        "ogLocale": "it_IT",
        "canonicalPath": "/it",
        "outputDir": DIST / "it",
    },
    "vi": {
        "json": ROOT / "i18n" / "vi.json",
        "htmlLang": "vi",
        "ogLocale": "vi_VN",
        "canonicalPath": "/vi",
        "outputDir": DIST / "vi",
    },
    "id": {
        "json": ROOT / "i18n" / "id.json",
        "htmlLang": "id",
        "ogLocale": "id_ID",
        "canonicalPath": "/id",
        "outputDir": DIST / "id",
    },
}


# Chapter deep-link URLs. Slug == anchor id in index32.html.
# Each chapter is published as its own URL with a chapter-specific
# canonical, title, description, and JSON-LD; the body is the same
# essay and a small inline script scrolls to the anchor on load.
CHAPTERS = [
    # (slug, ch_key in JSON, anchor id, chapter number)
    ('light',       'ch1',  'light',       1),
    ('eye',         'ch2',  'eye',         2),
    ('mixing',      'ch3',  'mixing',      3),
    ('wheel',       'ch4',  'wheel',       4),
    ('space',       'ch5',  'space',       5),
    ('harmony',     'ch6',  'harmony',     6),
    ('spaces',      'ch7',  'spaces',      7),
    ('interaction', 'ch8',  'interaction', 8),
    ('practice',    'ch9',  'practice',    9),
    ('glossary',    'ch10', 'glossary',    10),
    ('names',       'ch11', 'names',       11),
    ('pigments',    'ch12', 'pigments',    12),
    ('nature',      'ch13', 'nature',      13),
    ('practice2',   'ch14', 'practice2',   14),
]
CHAPTER_SLUGS = set(c[0] for c in CHAPTERS)


# SPECIAL_REPLACEMENTS에서 이미 처리한 키 (또는 prefix). 일반 매칭에서 제외.
SPECIAL_HANDLED_PREFIXES = (
    ".hero.titleLine1", ".hero.titleLine2", ".hero.scrollcue",
    ".footer.mark",
    ".ch1.title", ".ch2.title", ".ch3.title", ".ch4.title", ".ch5.title",
    ".ch7.title", ".ch8.title", ".ch9.title",
    ".ch5.fig.picker.axisX",
    ".ch7.fig.cie.legendCmyk", ".ch7.fig.cie.legendP3",
    ".jsStrings.spectralName", ".jsStrings.spectralDesc",
    ".jsStrings.nameRyb", ".jsStrings.nameRgb",
    ".jsStrings.harmoniesCap",
    ".jsStrings.statusMessages.perceivedPrefix",
    ".jsStrings.statusMessages.diskReset",
    ".jsStrings.statusMessages.copyBtnDefault",
    # 짧고 JS 변수명/키워드와 충돌할 위험이 있는 statusMessages 키 — 일반 매칭 금지
    ".jsStrings.statusMessages.saturationPrefix",
    ".jsStrings.statusMessages.valuePrefix",
    ".jsStrings.statusMessages.copyBtnFlash",
    # chronology Kubelka 항목은 title 안에 "&" 포함되어 SPECIAL에서 처리
    ".chronology.fig.events[9].title",
    # footer.fine은 이제 apply_translations의 \s+ regex가 multi-line을 처리하므로
    # SPECIAL에서 제거. (옛 build.py 시절 SPECIAL이 필요했던 흔적.)
)


def collect_pairs(en_node, ko_node, pairs, path=""):
    """en/ko 트리 동기 순회 — 모든 leaf string pair 수집. SPECIAL_HANDLED_PREFIXES 제외."""
    if isinstance(en_node, dict) and isinstance(ko_node, dict):
        for k in en_node:
            if k.startswith("_"):  # _meta 등 비번역 키 스킵
                continue
            if k in ko_node:
                collect_pairs(en_node[k], ko_node[k], pairs, f"{path}.{k}")
    elif isinstance(en_node, list) and isinstance(ko_node, list):
        for i, (en_item, ko_item) in enumerate(zip(en_node, ko_node)):
            collect_pairs(en_item, ko_item, pairs, f"{path}[{i}]")
    elif isinstance(en_node, str) and isinstance(ko_node, str):
        if any(path.startswith(p) for p in SPECIAL_HANDLED_PREFIXES):
            return
        en_node = en_node.strip()
        ko_node_s = ko_node.strip()
        if en_node and en_node != ko_node_s:
            pairs.append((en_node, ko_node, path))


def apply_translations(html: str, pairs: list) -> tuple[str, list]:
    """Translate HTML separately from JS strings; never replace JS identifiers."""
    blocks = re.split(r'(<(?:script|style)\b[^>]*>.*?</(?:script|style)>)', html,
                      flags=re.DOTALL | re.IGNORECASE)
    js_strings = re.compile(r'''//[^\n]*|/\*.*?\*/|(['"`])(?:\\.|(?!\1)[^\\])*?\1''', re.DOTALL)
    pairs_sorted = sorted(pairs, key=lambda p: -len(p[0]))
    missing = []
    for en, ko, path in pairs_sorted:
        found = False
        pattern = re.escape(en).replace(r"\ ", r"\s+")
        for i, block in enumerate(blocks):
            if block.lower().startswith('<style'):
                continue
            if block.lower().startswith('<script'):
                def translate_literal(m):
                    nonlocal found
                    if m.group(1) is None:
                        return m.group(0)  # comment, not a string literal
                    # Keep original escapes; add escapes only to the new text.
                    quote, value = m.group(1), m.group(0)[1:-1]
                    if en not in value:
                        return m.group(0)
                    escaped = (ko.replace('\\', '\\\\').replace(quote, '\\' + quote)
                               .replace('\n', '\\n').replace('\r', '\\r')
                               .replace('</', '<\\/'))
                    if quote == '`':
                        escaped = escaped.replace('${', '\\${')
                    found = True
                    return quote + value.replace(en, escaped) + quote
                blocks[i] = js_strings.sub(translate_literal, block)
            else:
                m = re.search(pattern, block)
                if m:
                    # Attribute translations must not terminate their quotes.
                    prefix = block[:m.start()]
                    in_tag = prefix.rfind('<') > prefix.rfind('>')
                    replacement = html_lib.escape(ko, quote=True) if in_tag else ko
                    blocks[i] = block[:m.start()] + replacement + block[m.end():]
                    found = True
            if found:
                break
        if not found:
            missing.append((path, en[:60]))
    return ''.join(blocks), missing


def js_text(value: str) -> str:
    """Content of a single-quoted JS literal, including HTML-script escaping."""
    return (value.replace('\\', '\\\\').replace("'", "\\'")
            .replace('\n', '\\n').replace('\r', '\\r').replace('</', '<\\/'))


def apply_lang_meta(html: str, cfg: dict) -> str:
    """<html lang>, og:locale, canonical, JSON-LD inLanguage 갱신."""
    if cfg["htmlLang"] != "en":
        html = re.sub(r'<html lang="en"', f'<html lang="{cfg["htmlLang"]}"', html, count=1)
        html = re.sub(
            r'<meta property="og:locale" content="en_US">',
            f'<meta property="og:locale" content="{cfg["ogLocale"]}">',
            html,
            count=1,
        )
        html = re.sub(
            r'"inLanguage":\s*"en"',
            f'"inLanguage": "{cfg["htmlLang"]}"',
            html,
        )
    # canonical은 항상 갱신
    html = re.sub(
        r'<link rel="canonical" href="[^"]*"\s*/?>',
        f'<link rel="canonical" href="{BASE_URL}{cfg["canonicalPath"]}">',
        html,
        count=1,
    )
    return html


LANG_NATIVE_NAMES = {
    "en": ("EN", "English"),
    "ko": ("KO", "한국어"),
    "ja": ("JA", "日本語"),
    "zh": ("ZH", "中文"),
    "vi": ("VI", "Tiếng Việt"),
    "es": ("ES", "Español"),
    "pt": ("PT", "Português"),
    "fr": ("FR", "Français"),
    "it": ("IT", "Italiano"),
    "de": ("DE", "Deutsch"),
    "id": ("ID", "Bahasa Indonesia"),
}

# cspace 디자인 변수 (--wall, --ink, --frame, --serif, --sans) 사용.
# circle5의 lang-selector 구조 + cspace의 Museum Neutral 톤.
LANG_SELECTOR_BLOCK = """
<style id="lang-selector-style">
  .lang-selector {
    position: fixed;
    top: 18px;
    right: 18px;
    z-index: 100;
    font-family: var(--sans);
  }
  .lang-trigger {
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.14em;
    padding: 9px 12px 9px 14px;
    background: rgba(214, 212, 206, 0.92);
    -webkit-backdrop-filter: blur(10px);
    backdrop-filter: blur(10px);
    border: 1px solid var(--frame);
    color: var(--ink-soft);
    cursor: pointer;
    border-radius: 2px;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    transition: color 0.18s, background 0.18s, border-color 0.18s;
    box-shadow: 0 4px 20px var(--shadow);
    min-height: 36px;
  }
  .lang-trigger:hover { color: var(--ink); border-color: var(--ink); }
  .lang-trigger[aria-expanded="true"] {
    background: var(--ink);
    color: var(--wall-lit);
    border-color: var(--ink);
  }
  .lang-chevron {
    font-size: 9px;
    line-height: 1;
    transition: transform 0.22s ease;
    opacity: 0.7;
  }
  .lang-trigger[aria-expanded="true"] .lang-chevron { transform: rotate(180deg); }
  .lang-menu {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    min-width: 210px;
    background: rgba(222, 220, 214, 0.97);
    -webkit-backdrop-filter: blur(14px);
    backdrop-filter: blur(14px);
    border: 1px solid var(--frame);
    border-radius: 2px;
    padding: 4px;
    box-shadow: 0 10px 32px var(--shadow);
    display: flex;
    flex-direction: column;
    gap: 1px;
    opacity: 0;
    transform: translateY(-6px);
    pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease;
    max-height: calc(100vh - 80px);
    overflow-y: auto;
  }
  .lang-menu.open { opacity: 1; transform: translateY(0); pointer-events: auto; }
  .lang-option {
    font-family: var(--sans);
    font-size: 13px;
    padding: 9px 12px;
    background: transparent;
    border: none;
    color: var(--ink-soft);
    cursor: pointer;
    border-radius: 2px;
    text-align: left;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: background 0.12s, color 0.12s;
    min-height: 38px;
    width: 100%;
    text-decoration: none;
  }
  .lang-option:hover { background: var(--wall-deep); color: var(--ink); }
  .lang-option:focus-visible { outline: 2px solid var(--ink); outline-offset: -2px; }
  .lang-option.active { background: var(--ink); color: var(--wall-lit); }
  .lang-option-code {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.14em;
    color: var(--ink-faint);
    min-width: 24px;
  }
  .lang-option.active .lang-option-code { color: var(--wall); }
  .lang-option-native { font-family: var(--serif); font-size: 14px; line-height: 1.1; }

  @media (max-width: 560px) {
    .lang-selector { top: 10px; right: 10px; }
    .lang-trigger { padding: 8px 10px 8px 12px; font-size: 10px; min-height: 34px; }
    .lang-menu { min-width: 190px; }
    .lang-option { padding: 11px 12px; min-height: 42px; }
  }
  @media print { .lang-selector { display: none; } }

  /* Soft language suggestion banner — shown only on the English page when
     the browser's preferred language is one we support and the user hasn't
     yet made a choice. */
  .lang-banner {
    position: fixed; top: 64px; right: 18px; z-index: 99;
    max-width: 360px;
    background: rgba(33,31,28,0.95);
    color: rgba(255,255,255,0.92);
    padding: 12px 14px 12px 16px;
    border-radius: 4px;
    display: flex; align-items: center; gap: 10px;
    font-family: var(--sans); font-size: 13px; line-height: 1.45;
    box-shadow: 0 8px 28px rgba(33,31,28,0.28);
    opacity: 0; transform: translateY(-6px);
    transition: opacity 0.22s ease, transform 0.22s ease;
  }
  .lang-banner.shown { opacity: 1; transform: translateY(0); }
  .lang-banner-q { flex: 1; }
  .lang-banner-yes {
    background: rgba(255,255,255,0.95); color: var(--ink);
    padding: 6px 12px; border-radius: 3px;
    text-decoration: none; font-weight: 600; font-size: 12.5px;
    white-space: nowrap; flex: none;
  }
  .lang-banner-yes:hover { background: white; }
  .lang-banner-no {
    background: transparent; color: rgba(255,255,255,0.55);
    border: none; cursor: pointer; padding: 6px 4px;
    font-family: inherit; font-size: 18px; line-height: 1;
  }
  .lang-banner-no:hover { color: white; }
  @media (max-width: 560px) {
    .lang-banner { top: auto; bottom: 12px; left: 12px; right: 12px; max-width: none; }
  }
  @media print { .lang-banner { display: none; } }
</style>

<nav class="lang-selector" aria-label="Language">
  <button class="lang-trigger" id="langTrigger" type="button"
          aria-haspopup="listbox" aria-expanded="false" aria-controls="langMenu">
    <span class="lang-trigger-code" id="langTriggerCode">EN</span>
    <span class="lang-chevron" aria-hidden="true">▾</span>
  </button>
  <div class="lang-menu" id="langMenu" role="listbox" aria-label="Choose language">
__LANG_OPTIONS__
  </div>
</nav>

<script>
(function(){
  var trigger = document.getElementById('langTrigger');
  var menu    = document.getElementById('langMenu');
  var codeEl  = document.getElementById('langTriggerCode');
  if(!trigger || !menu || !codeEl) return;

  // 현재 언어 감지 — path 첫 segment ("/ko" → "ko", "/" → "en")
  var basePath = __BASE_PATH__;
  var relativePath = location.pathname.slice(basePath.length);
  var segments = relativePath.split('/').filter(Boolean);
  var seg = (segments[0] || '').toLowerCase();
  var current = __LANG_CODES__.indexOf(seg) >= 0 ? seg : 'en';
  var chapter = segments[segments.length - 1] || '';
  var isChapter = __CHAPTER_CODES__.indexOf(chapter) >= 0;
  function langTarget(lang){
    return basePath + '/' + (lang === 'en' ? '' : lang + '/') + (isChapter ? chapter + '/' : '') + location.hash;
  }
  codeEl.textContent = current.toUpperCase();

  document.querySelectorAll('.lang-option').forEach(function(opt){
    if(opt.getAttribute('data-lang') === current) opt.classList.add('active');
  });

  function close(){
    menu.classList.remove('open');
    trigger.setAttribute('aria-expanded', 'false');
  }
  function open(){
    menu.classList.add('open');
    trigger.setAttribute('aria-expanded', 'true');
  }
  trigger.addEventListener('click', function(e){
    e.stopPropagation();
    if(menu.classList.contains('open')) close(); else open();
  });
  document.addEventListener('click', function(e){
    if(!menu.contains(e.target) && e.target !== trigger) close();
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && menu.classList.contains('open')){ close(); trigger.focus(); }
  });
  document.querySelectorAll('.lang-option').forEach(function(opt){
    opt.addEventListener('click', function(e){
      e.preventDefault();
      var lang = opt.getAttribute('data-lang');
      // Remember the user's explicit choice — used by the banner logic
      // below and by the auto-redirect on the English landing page.
      try { localStorage.setItem('cspace.lang', lang); } catch(_){}
      var target = langTarget(lang);
      if(location.pathname !== target) location.href = target;
      else close();
    });
  });

  /* ---- Language preference: banner + remember + auto-redirect ----
     Strategy: never auto-redirect blindly. On the English page, if the
     browser's preferred non-English language is one we ship, offer a small
     banner. If the user accepts (or has accepted before), remember it and
     auto-redirect future visits to /. If they dismiss, stay quiet forever.
     Bots and screenshot crawlers are skipped via user-agent. */
  var BANNER_MSG = {
    ko: { q: '이 페이지를 한국어로 보시겠어요?', yes: '네' },
    ja: { q: 'このページを日本語で表示しますか？', yes: 'はい' },
    es: { q: '¿Leer esta página en español?', yes: 'Sí' },
    zh: { q: '用中文阅读此页面？', yes: '是' },
    fr: { q: 'Lire cette page en français ?', yes: 'Oui' },
    de: { q: 'Diese Seite auf Deutsch lesen?', yes: 'Ja' },
    pt: { q: 'Ler esta página em português?', yes: 'Sim' },
    it: { q: 'Leggere questa pagina in italiano?', yes: 'Sì' },
    vi: { q: 'Đọc trang này bằng tiếng Việt?', yes: 'Có' },
    id: { q: 'Baca halaman ini dalam Bahasa Indonesia?', yes: 'Ya' }
  };
  function pickPreferred(){
    var langs = navigator.languages || [navigator.language || ''];
    for(var i=0;i<langs.length;i++){
      var code = (langs[i]||'').toLowerCase().split('-')[0];
      if(BANNER_MSG[code]) return code;
    }
    return null;
  }
  function isBot(){
    return /bot|crawler|spider|crawling|slurp|googlebot|bingbot|baiduspider/i
      .test(navigator.userAgent || '');
  }

  // Only run language preference logic on the English (default) page.
  if(current === 'en' && !isChapter && !isBot()){
    var saved=null;
    try { saved = localStorage.getItem('cspace.lang'); } catch(_){}

    // (1) Auto-redirect if the user has previously picked a non-English language.
    if(saved && saved !== 'en' && BANNER_MSG[saved]){
      location.replace(langTarget(saved));
      return;
    }

    // (2) Offer the banner if no choice/dismissal yet and the browser prefers
    //     a supported non-English language.
    var dismissed=null;
    try { dismissed = localStorage.getItem('cspace.langPrompt'); } catch(_){}
    if(!saved && !dismissed){
      var pref = pickPreferred();
      if(pref){
        var msg = BANNER_MSG[pref];
        var banner = document.createElement('div');
        banner.className = 'lang-banner';
        banner.setAttribute('role','dialog');
        banner.setAttribute('aria-live','polite');
        banner.innerHTML =
          '<span class="lang-banner-q">'+msg.q+'</span>'+
          '<a class="lang-banner-yes" href="'+langTarget(pref)+'">'+msg.yes+'</a>'+
          '<button class="lang-banner-no" type="button" aria-label="Dismiss">×</button>';
        document.body.appendChild(banner);
        // animate in next frame
        requestAnimationFrame(function(){ banner.classList.add('shown'); });
        banner.querySelector('.lang-banner-yes').addEventListener('click', function(){
          try { localStorage.setItem('cspace.lang', pref); } catch(_){}
        });
        banner.querySelector('.lang-banner-no').addEventListener('click', function(){
          try { localStorage.setItem('cspace.langPrompt', 'dismissed'); } catch(_){}
          banner.classList.remove('shown');
          setTimeout(function(){ banner.remove(); }, 220);
        });
      }
    }
  }
})();
</script>
"""


# 비영문 페이지에서 chapter fade-in JS init이 실패해도 콘텐트 보이게 강제.
# (원본 CSS `.js .chapter { opacity:0; ... }` 가 IntersectionObserver 콜백 의존이라
# 한국어/일본어 등에서 JS 런타임 일부 실패 시 영원히 숨겨질 수 있음.)
CHAPTER_FORCE_VISIBLE = """
<style id="lang-chapter-visible">
  .js .chapter, .js .chapter.in { opacity: 1 !important; transform: none !important; }
</style>
"""

LANG_FONT_FALLBACK = {
    "ko": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', 'Apple SD Gothic Neo', 'Noto Serif KR', 'Nanum Myeongjo', Georgia, 'Times New Roman', serif;
    --sans:  'Inter', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'D2Coding', 'Apple SD Gothic Neo', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "de": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', Georgia, 'Times New Roman', serif;
    --sans:  'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "fr": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', Georgia, 'Times New Roman', serif;
    --sans:  'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "es": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', Georgia, 'Times New Roman', serif;
    --sans:  'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "it": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', Georgia, 'Times New Roman', serif;
    --sans:  'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "pt": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', Georgia, 'Times New Roman', serif;
    --sans:  'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "ja": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', 'Hiragino Mincho ProN', 'Yu Mincho', 'Noto Serif JP', Georgia, serif;
    --sans:  'Inter', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Noto Sans JP', system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'Source Han Mono JP', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "zh": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', 'Songti SC', 'Source Han Serif SC', 'Noto Serif SC', Georgia, serif;
    --sans:  'Inter', 'PingFang SC', 'Source Han Sans SC', 'Noto Sans SC', system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
    "vi": """
<style id="lang-font-fallback">
  :root {
    --serif: 'Spectral', 'Noto Serif', Georgia, serif;
    --sans:  'Inter', 'Noto Sans', system-ui, sans-serif;
    --mono:  'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  }
</style>
""",
}


def inject_font_fallback(html: str, lang: str) -> str:
    blocks = []
    fb = LANG_FONT_FALLBACK.get(lang)
    if fb:
        blocks.append(fb)
    # 비영문 lang은 chapter fade-in 강제 가시 (JS init 실패해도 보이게)
    if lang != "en":
        blocks.append(CHAPTER_FORCE_VISIBLE)
    if not blocks:
        return html
    combined = "".join(blocks)
    if "</head>" in html:
        return html.replace("</head>", combined + "</head>", 1)
    return html


def render_lang_selector() -> str:
    options = []
    for lang_code in LANG_CONFIG.keys():
        code_up, native = LANG_NATIVE_NAMES.get(lang_code, (lang_code.upper(), lang_code))
        options.append(
            f'    <button class="lang-option" type="button" data-lang="{lang_code}" role="option">'
            f'<span class="lang-option-code">{code_up}</span>'
            f'<span class="lang-option-native">{native}</span></button>'
        )
    options_html = "\n".join(options)
    lang_codes_js = "[" + ",".join(f"'{c}'" for c in LANG_CONFIG.keys()) + "]"
    block = LANG_SELECTOR_BLOCK.replace("__LANG_OPTIONS__", options_html)
    block = block.replace("__LANG_CODES__", lang_codes_js)
    block = block.replace("__BASE_PATH__", json.dumps(urlsplit(BASE_URL).path))
    block = block.replace("__CHAPTER_CODES__", json.dumps(sorted(CHAPTER_SLUGS)))
    return block


def inject_lang_selector(html: str) -> str:
    selector = render_lang_selector()
    if "</body>" in html:
        return html.replace("</body>", selector + "\n</body>", 1)
    return html + selector


# Inline script that scrolls to the chapter anchor on chapter-deep-link
# pages (e.g. /light, /ko/eye). Skips main pages (/, /ko, etc.).
CHAPTER_SCROLL_SCRIPT = """
<script id="chapter-scroll-shim">
(function(){
  var langs = ['en','ko','ja','es','zh','fr','de','pt','it','vi'];
  var chapters = ['light','eye','mixing','wheel','space','harmony','spaces','interaction','practice','glossary','names','pigments','nature','practice2'];
  var path = location.pathname.replace(/\\/$/,'').split('/').filter(Boolean);
  var slug = path[path.length-1];
  if(chapters.indexOf(slug) < 0) return;
  // Wait for layout before scrolling.
  window.addEventListener('DOMContentLoaded', function(){
    var el = document.getElementById(slug);
    if(el){
      // 'instant' so the user lands on the chapter, not animates to it.
      setTimeout(function(){
        el.scrollIntoView({block:'start'});
      }, 30);
    }
  });
})();
</script>
"""


def inject_chapter_scroll(html: str) -> str:
    if "</body>" in html:
        return html.replace("</body>", CHAPTER_SCROLL_SCRIPT + "</body>", 1)
    return html + CHAPTER_SCROLL_SCRIPT


def inject_tube_label_i18n(html: str, lang_json: dict) -> str:
    """Inject window.jsStrings.tubeLabel for §12 fig-tube interactive readout.
    Falls back silently if ch12.fig.tube isn't present in the language json."""
    tube = lang_json.get('ch12', {}).get('fig', {}).get('tube')
    if not tube:
        return html
    payload = {
        "prompt": tube.get('readoutPrompt', 'Hover a label above to read what it means.'),
        "labels": {
            "name":   [tube.get('name', ''),       tube.get('seriesNote', '')],
            "series": [tube.get('series', ''),     tube.get('seriesNote', '')],
            "ci":     [tube.get('ci', ''),         tube.get('ciNote', '')],
            "lf":     [tube.get('lf', ''),         tube.get('lfNote', '')],
            "conf":   [tube.get('conf', ''),       tube.get('confNote', '')],
            "hue":    [tube.get('hue', ''),        tube.get('hueNote', '')],
        }
    }
    # 'name' uses a richer title row; use the colour name only with a short note
    # that places it in context. We reuse seriesNote? No — keep the inline JS
    # fallback which described what the commercial name means. For i18n simplicity
    # the readout for the colour name row will use the same content as the JS
    # fallback's English by setting both to the localised seriesNote (good enough
    # first pass; the seriesNote talks about Series 4 which directly explains
    # the price tier shown next to the name).
    # Better: pass the localised name with a stub that says "see Series 4 next".
    payload["labels"]["name"] = [tube.get('name', ''),
                                 tube.get('seriesNote', '')]
    inject = (
        '\n<script>\n'
        'window.jsStrings = window.jsStrings || {};\n'
        'window.jsStrings.tubeLabel = ' + json.dumps(payload, ensure_ascii=False) + ';\n'
        '</script>\n'
    )
    # Place just before the fig-tube div so the inline JS module reads it.
    needle = '<div class="figure" id="fig-tube">'
    if needle in html:
        return html.replace(needle, inject + needle, 1)
    return html


def inject_timeline_i18n(html: str, lang_json: dict) -> str:
    """Inject window.jsStrings.timelinePigments for §12 fig-timeline.
    Expects ch12.fig.timeline.pigments as a list of 17 {name, story} pairs."""
    pigs = (lang_json.get('ch12', {}).get('fig', {})
            .get('timeline', {}).get('pigments'))
    if not pigs or not isinstance(pigs, list):
        return html
    inject = (
        '\n<script>\n'
        'window.jsStrings = window.jsStrings || {};\n'
        'window.jsStrings.timelinePigments = ' + json.dumps(pigs, ensure_ascii=False) + ';\n'
        '</script>\n'
    )
    needle = '<div class="figure" id="fig-timeline">'
    if needle in html:
        return html.replace(needle, inject + needle, 1)
    return html


def inject_specs_i18n(html: str, lang_json: dict) -> str:
    """Inject window.jsStrings.monitorSpecs for §14 fig-specs table.
    Expects ch14.fig.specs.specs (5 use-cases × 7 values) and ch14.fig.specs.rows
    (list of [label, key] pairs)."""
    specs_obj = lang_json.get('ch14', {}).get('fig', {}).get('specs', {})
    specs = specs_obj.get('specs')
    rows = specs_obj.get('rows')
    if not specs or not rows:
        return html
    payload = {'specs': specs, 'rows': rows}
    inject = (
        '\n<script>\n'
        'window.jsStrings = window.jsStrings || {};\n'
        'window.jsStrings.monitorSpecs = ' + json.dumps(payload, ensure_ascii=False) + ';\n'
        '</script>\n'
    )
    needle = '<div class="figure" id="fig-specs">'
    if needle in html:
        return html.replace(needle, inject + needle, 1)
    return html


def chapter_meta(json_data: dict, ch_key: str, lang: str) -> dict:
    """Extract a chapter's title and standfirst from the JSON tree."""
    ch = json_data.get(ch_key) or {}
    title = ch.get('title') or ''
    standfirst = ch.get('standfirst') or ''
    num = ch.get('num') or ''
    # Site name in the host language — falls back to the English wordmark.
    site_name = (json_data.get('page', {}).get('og', {}).get('siteName')
                 or 'The Book of Color')
    return {'title': title, 'standfirst': standfirst, 'num': num,
            'site_name': site_name}


def reduce_to_chapter(html: str, chapter_n: int) -> str:
    """Trim the full essay HTML down to a single chapter page.

    Removes: <section class="hero">, the other 13 chapter <section>s,
    the CHRONOLOGY and CODA sections. Keeps: topbar, lang selector,
    the chosen chapter <section>, footer, modal, and all <style>/<script>.

    Returns the original HTML if any section count doesn't match (safe
    fallback so the build doesn't silently break)."""
    # 1) Drop hero
    html = re.sub(
        r'\s*<section class="hero"[^>]*>.*?</section>\s*',
        '\n', html, count=1, flags=re.DOTALL,
    )
    # 2) Drop chronology
    html = re.sub(
        r'\s*<!--\s*=+\s*CHRONOLOGY\s*=+\s*-->\s*<section class="chapter" id="chronology"[^>]*>.*?</section>\s*',
        '\n', html, count=1, flags=re.DOTALL,
    )
    # 3) Drop coda (palette generator)
    html = re.sub(
        r'\s*<!--\s*=+\s*CODA[^=]*=+\s*-->\s*<section[^>]*id="coda"[^>]*>.*?</section>\s*',
        '\n', html, count=1, flags=re.DOTALL,
    )
    # 4) Drop the other 13 chapter sections (keep only the chosen one).
    pattern = re.compile(
        r'\s*<!--\s*=+\s*§\d+[^=]*=+\s*-->\s*<section class="chapter" id="[a-z0-9]+"[^>]*>.*?</section>\s*',
        re.DOTALL,
    )
    matches = list(pattern.finditer(html))
    if len(matches) != 14:
        # Structure changed; bail and serve the full page (safe).
        return html
    keep_idx = chapter_n - 1
    # Remove from end to start so earlier offsets stay valid.
    for i in range(len(matches) - 1, -1, -1):
        if i == keep_idx:
            continue
        m = matches[i]
        html = html[:m.start()] + '\n' + html[m.end():]
    return html


def build_chapter_html(base_html: str, cfg: dict, lang: str,
                       chapter_slug: str, ch_key: str,
                       chapter_n: int, json_data: dict) -> str:
    """Build a chapter-deep-link variant of the main essay HTML.

    The body is reduced to just the chosen chapter (hero, the other 13
    chapters, chronology, and coda are stripped). All global styles,
    scripts, topbar, footer, lang selector, and the paint-tube modal
    remain so each chapter page is self-contained.
    """
    meta = chapter_meta(json_data, ch_key, lang)
    # Build the chapter URL path: '/light' for English, '/ko/light' for Korean.
    if cfg["htmlLang"] == "en":
        canonical = f"{BASE_URL}/{chapter_slug}"
    else:
        canonical = f"{BASE_URL}{cfg['canonicalPath']}/{chapter_slug}"

    # Compose the page <title>. Pattern: "{Chapter number} · {Title} · {Site name}"
    # using the host language's site_name (e.g. "색에 관하여" in Korean).
    # A few chapters get extra SEO keywords appended (English universal):
    # §7 surfaces OKLCH/HSL/RGB so the page can rank for those terms.
    CHAPTER_KEYWORDS = {
        7: "RGB · HSL · OKLCH · CIE 1931",
        8: "Albers · simultaneous contrast · Hering",
        2: "trichromatic vision · metamerism · cones",
    }
    site = meta['site_name']
    extra = f" · {CHAPTER_KEYWORDS[chapter_n]}" if chapter_n in CHAPTER_KEYWORDS else ""
    if meta['num'] and meta['title']:
        page_title = f"{meta['num']} · {meta['title']}{extra} · {site}"
    elif meta['title']:
        page_title = f"{meta['title']}{extra} · {site}"
    else:
        page_title = site

    # Description: prefer the chapter's standfirst, fall back to the chapter title.
    desc = meta['standfirst'] or meta['title'] or page_title

    # Reduce the body to just this chapter (hero / other chapters / chronology
    # / coda stripped). All global styles and scripts stay.
    html = reduce_to_chapter(base_html, chapter_n)
    # Replace <title>
    html = re.sub(r'<title>[^<]*</title>',
                  f'<title>{page_title}</title>', html, count=1)
    # Replace canonical
    html = re.sub(r'<link rel="canonical" href="[^"]+">',
                  f'<link rel="canonical" href="{canonical}">', html, count=1)
    # Replace meta description
    html = re.sub(r'<meta name="description" content="[^"]*">',
                  f'<meta name="description" content="{desc}">', html, count=1)
    # Replace og:title, og:description, twitter:title, twitter:description, og:url
    html = re.sub(r'<meta property="og:title" content="[^"]*">',
                  f'<meta property="og:title" content="{page_title}">', html, count=1)
    html = re.sub(r'<meta property="og:description" content="[^"]*">',
                  f'<meta property="og:description" content="{desc}">', html, count=1)
    html = re.sub(r'<meta name="twitter:title" content="[^"]*">',
                  f'<meta name="twitter:title" content="{page_title}">', html, count=1)
    html = re.sub(r'<meta name="twitter:description" content="[^"]*">',
                  f'<meta name="twitter:description" content="{desc}">', html, count=1)
    # Add og:url right after og:locale
    if '<meta property="og:url"' not in html:
        html = re.sub(r'(<meta property="og:locale"[^>]+>)',
                      f'\\1\n<meta property="og:url" content="{canonical}">',
                      html, count=1)
    else:
        html = re.sub(r'<meta property="og:url" content="[^"]+">',
                      f'<meta property="og:url" content="{canonical}">', html, count=1)

    # Google Scholar citation metadata — override per chapter.
    html = re.sub(r'<meta name="citation_title" content="[^"]*">',
                  f'<meta name="citation_title" content="{page_title}">', html, count=1)
    html = re.sub(r'<meta name="citation_language" content="[^"]*">',
                  f'<meta name="citation_language" content="{cfg["htmlLang"]}">', html, count=1)
    # citation_fulltext_html_url — the page itself (for now; PDF in Phase B.7)
    if '<meta name="citation_fulltext_html_url"' not in html:
        html = re.sub(r'(<meta name="citation_language"[^>]+>)',
                      f'\\1\n<meta name="citation_fulltext_html_url" content="{canonical}">',
                      html, count=1)

    # Inject a Prev/Next chapter nav between the article and the footer.
    # Only on chapter deep-link pages, not on the main essay — strengthens
    # internal linking (B.15) without altering the i18n JSON.
    nav_items = []
    base_path = "" if cfg["htmlLang"] == "en" else cfg["canonicalPath"]
    # Prev
    if chapter_n > 1:
        prev_slug, prev_key, _, _ = CHAPTERS[chapter_n - 2]
        prev_ch = json_data.get(prev_key, {})
        prev_num = prev_ch.get('num', '')
        prev_title = prev_ch.get('title', prev_slug)
        nav_items.append(
            f'<a class="chapter-nav-prev" href="{base_path}/{prev_slug}">'
            f'<span class="label">← {prev_num}</span>'
            f'<span class="title">{prev_title}</span></a>'
        )
    # Next
    if chapter_n < len(CHAPTERS):
        next_slug, next_key, _, _ = CHAPTERS[chapter_n]
        next_ch = json_data.get(next_key, {})
        next_num = next_ch.get('num', '')
        next_title = next_ch.get('title', next_slug)
        nav_items.append(
            f'<a class="chapter-nav-next" href="{base_path}/{next_slug}">'
            f'<span class="label">{next_num} →</span>'
            f'<span class="title">{next_title}</span></a>'
        )
    if nav_items:
        nav_html = '<nav class="chapter-nav" aria-label="Chapter navigation">' + ''.join(nav_items) + '</nav>'
        html = html.replace('<footer', nav_html + '\n<footer', 1)

    # Inject BreadcrumbList JSON-LD so each chapter shows up in Google
    # rich snippets with a breadcrumb back to the main book.
    book_root = (f"{BASE_URL}/" if cfg["htmlLang"] == "en"
                 else f"{BASE_URL}{cfg['canonicalPath']}")
    breadcrumb = (
        '<script type="application/ld+json">\n'
        '{"@context":"https://schema.org","@type":"BreadcrumbList",'
        '"itemListElement":['
        '{"@type":"ListItem","position":1,"name":"' + meta['site_name'].replace('"', '\\"') + '","item":"' + book_root + '"},'
        '{"@type":"ListItem","position":2,"name":"' + page_title.replace('"', '\\"') + '","item":"' + canonical + '"}'
        ']}\n'
        '</script>'
    )
    # Insert breadcrumb just before </head>
    html = html.replace('</head>', breadcrumb + '\n</head>', 1)

    # Replace hreflang block with chapter-specific URLs so each chapter
    # page points to its own translations in other languages.
    new_links = []
    for lc_code, lc in LANG_CONFIG.items():
        if lc["htmlLang"] == "en":
            chap_url = f"{BASE_URL}/{chapter_slug}"
        else:
            chap_url = f"{BASE_URL}{lc['canonicalPath']}/{chapter_slug}"
        new_links.append(
            f'<link rel="alternate" hreflang="{lc["htmlLang"]}" href="{chap_url}">'
        )
    new_links.append(
        f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}/{chapter_slug}">'
    )
    new_block = "\n".join(new_links)
    # Match all consecutive hreflang links (the entire block).
    html = re.sub(
        r'(<link rel="alternate" hreflang="[^"]+" href="[^"]+">\s*)+',
        new_block + "\n", html, count=1,
    )
    return html


def generate_sitemap() -> str:
    """Build sitemap.xml: root URLs + chapter URLs + /about, all 10 langs.

    Format follows sitemaps.org 0.9 with xhtml:link hreflang annotations
    on each <url>. Per Google guidance, each language version's <url>
    block lists every other version including itself.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap-0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]

    def hreflang_links(slug_or_empty: str) -> list[str]:
        """Return hreflang link blocks for a given chapter slug
        (or '' for the root/main page)."""
        out = []
        for lc_code, lc in LANG_CONFIG.items():
            base = lc["canonicalPath"]
            if lc["htmlLang"] == "en":
                url = (f"{BASE_URL}/{slug_or_empty}" if slug_or_empty
                       else f"{BASE_URL}/")
            else:
                url = (f"{BASE_URL}{base}/{slug_or_empty}" if slug_or_empty
                       else f"{BASE_URL}{base}")
            out.append(
                f'    <xhtml:link rel="alternate" hreflang="{lc["htmlLang"]}" href="{url}"/>'
            )
        xdef = (f"{BASE_URL}/{slug_or_empty}" if slug_or_empty
                else f"{BASE_URL}/")
        out.append(
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{xdef}"/>'
        )
        return out

    # Root + per-language root URLs
    for lc_code, lc in LANG_CONFIG.items():
        if lc["htmlLang"] == "en":
            loc = f"{BASE_URL}/"
            priority = "1.0"
        else:
            loc = f"{BASE_URL}{lc['canonicalPath']}"
            priority = "0.9"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.extend(hreflang_links(""))
        lines.append(f"    <lastmod>{LAST_UPDATED}</lastmod>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")

    # Chapter URLs (10 chapters × 10 langs = 100)
    for slug, _ch_key, _anchor, _ch_n in CHAPTERS:
        for lc_code, lc in LANG_CONFIG.items():
            if lc["htmlLang"] == "en":
                loc = f"{BASE_URL}/{slug}"
            else:
                loc = f"{BASE_URL}{lc['canonicalPath']}/{slug}"
            lines.append("  <url>")
            lines.append(f"    <loc>{loc}</loc>")
            lines.extend(hreflang_links(slug))
            lines.append(f"    <lastmod>{LAST_UPDATED}</lastmod>")
            lines.append("    <changefreq>monthly</changefreq>")
            lines.append("    <priority>0.8</priority>")
            lines.append("  </url>")

    # /about (English only for now; multi-lang in Phase C)
    lines.append("  <url>")
    lines.append(f"    <loc>{BASE_URL}/about</loc>")
    lines.append(f"    <lastmod>{LAST_UPDATED}</lastmod>")
    lines.append("    <changefreq>yearly</changefreq>")
    lines.append("    <priority>0.5</priority>")
    lines.append("  </url>")

    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def apply_hreflang(html: str, cfg: dict) -> str:
    """hreflang link tags를 canonical 직후에 삽입."""
    html = re.sub(r'<link rel="alternate" hreflang="[^"]+"[^>]*>\s*', '', html)
    links = []
    for lang_code, lc in LANG_CONFIG.items():
        links.append(
            f'<link rel="alternate" hreflang="{lc["htmlLang"]}" href="{BASE_URL}{lc["canonicalPath"]}">'
        )
    links.append(f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}/">')
    hreflang_block = "\n".join(links)
    canonical_re = re.compile(r'(<link rel="canonical" href="[^"]+">)\s*')
    html = canonical_re.sub(r"\1\n" + hreflang_block + '\n', html, count=1)
    return html


# 언어별 hard-coded HTML entity 변환 (axisX nbsp + Kubelka & + CMYK/P3 nbsp + ARIA template)
LANG_OVERRIDES = {
    "id": {
        "kubelka_title": "Kubelka &amp; Munk pigment theory",
        "axisX_nbsp": "↑ light · value · dark ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← grey · saturation · vivid →",
        "offset_nbsp": "Offset\xa0print (CMYK)",
        "aria_nanometres": "' nanometres — '+spectralName(wl)",
        "aria_degrees": "' degrees'",
        "aria_kelvin": "' Kelvin — '",
        "aria_pct_ambient": "' percent ambient light — '",
    },
    "ko": {
        "kubelka_title": "쿠벨카–뭉크 안료 이론",
        "axisX_nbsp": "↑ 밝음 · 명도 · 어두움 ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← 회색 · 채도 · 선명 →",
        "offset_nbsp": "오프셋\xa0인쇄 (CMYK)",
        "aria_nanometres": "' 나노미터 — '+spectralName(wl)",
        "aria_degrees": "' 도'",
        "aria_kelvin": "' 켈빈 — '",
        "aria_pct_ambient": "' 퍼센트 주변광 — '",
    },
    "ja": {
        "kubelka_title": "クーベルカ・ムンク顔料理論",
        "axisX_nbsp": "↑ 明 · 明度 · 暗 ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← 灰 · 彩度 · 鮮 →",
        "offset_nbsp": "オフセット\xa0印刷 (CMYK)",
        "aria_nanometres": "' ナノメートル — '+spectralName(wl)",
        "aria_degrees": "' 度'",
        "aria_kelvin": "' ケルビン — '",
        "aria_pct_ambient": "' パーセント環境光 — '",
    },
    "es": {
        "kubelka_title": "Teoría de pigmentos de Kubelka y Munk",
        "axisX_nbsp": "↑ claro · valor · oscuro ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← gris · saturación · vivo →",
        "offset_nbsp": "Impresión\xa0offset (CMYK)",
        "aria_nanometres": "' nanómetros — '+spectralName(wl)",
        "aria_degrees": "' grados'",
        "aria_kelvin": "' Kelvin — '",
        "aria_pct_ambient": "' por ciento de luz ambiente — '",
    },
    "zh": {
        "kubelka_title": "库贝尔卡与蒙克的颜料理论",
        "axisX_nbsp": "↑ 亮 · 明度 · 暗 ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← 灰 · 饱和度 · 鲜艳 →",
        "offset_nbsp": "胶印\xa0(CMYK)",
        "aria_nanometres": "' 纳米 — '+spectralName(wl)",
        "aria_degrees": "' 度'",
        "aria_kelvin": "' 开尔文 — '",
        "aria_pct_ambient": "' 百分比环境光 — '",
    },
    "fr": {
        "kubelka_title": "Théorie des pigments de Kubelka–Munk",
        "axisX_nbsp": "↑ clair · valeur · sombre ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← gris · saturation · vif →",
        "offset_nbsp": "Impression\xa0offset (CMJN)",
        "aria_nanometres": "' nanomètres — '+spectralName(wl)",
        "aria_degrees": "' degrés'",
        "aria_kelvin": "' kelvin — '",
        "aria_pct_ambient": "' pour cent de lumière ambiante — '",
    },
    "de": {
        "kubelka_title": "Kubelka–Munk Pigmenttheorie",
        "axisX_nbsp": "↑ hell · Helligkeitswert · dunkel ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← grau · Sättigung · leuchtend →",
        "offset_nbsp": "Offsetdruck\xa0(CMYK)",
        "aria_nanometres": "' Nanometer — '+spectralName(wl)",
        "aria_degrees": "' Grad'",
        "aria_kelvin": "' Kelvin — '",
        "aria_pct_ambient": "' Prozent Umgebungslicht — '",
    },
    "pt": {
        "kubelka_title": "Teoria dos pigmentos Kubelka–Munk",
        "axisX_nbsp": "↑ claro · valor · escuro ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← cinza · saturação · vívido →",
        "offset_nbsp": "Impressão\xa0offset (CMYK)",
        "aria_nanometres": "' nanômetros — '+spectralName(wl)",
        "aria_degrees": "' graus'",
        "aria_kelvin": "' Kelvin — '",
        "aria_pct_ambient": "' por cento de luz ambiente — '",
    },
    "it": {
        "kubelka_title": "Teoria dei pigmenti Kubelka–Munk",
        "axisX_nbsp": "↑ chiaro · valore · scuro ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← grigio · saturazione · vivido →",
        "offset_nbsp": "Stampa\xa0offset (CMYK)",
        "aria_nanometres": "' nanometri — '+spectralName(wl)",
        "aria_degrees": "' gradi'",
        "aria_kelvin": "' Kelvin — '",
        "aria_pct_ambient": "' per cento di luce ambiente — '",
    },
    "vi": {
        "kubelka_title": "Lý thuyết sắc tố Kubelka–Munk",
        "axisX_nbsp": "↑ sáng · giá trị · tối ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← xám · độ bão hòa · rực rỡ →",
        "offset_nbsp": "In\xa0offset (CMYK)",
        "aria_nanometres": "' nanomet — '+spectralName(wl)",
        "aria_degrees": "' độ'",
        "aria_kelvin": "' Kelvin — '",
        "aria_pct_ambient": "' phần trăm ánh sáng môi trường — '",
    },
}


def special_replacements(d: dict, lang: str = "ko") -> list:
    """짧은 라벨 + JS 함수 + HTML entity — context-aware string replacement.
    d = 언어 dict (ko/ja/...), lang = 언어 코드."""
    return special_replacements_ko(d, lang)


def special_replacements_ko(ko: dict, lang: str = "ko") -> list:
    """짧은 라벨 + JS 함수 + HTML entity — context-aware string replacement."""
    ov = LANG_OVERRIDES.get(lang, LANG_OVERRIDES["ko"])
    # These fields are interpolated into single-quoted JavaScript literals.
    def escape_tree(value):
        if isinstance(value, str):
            return js_text(value)
        if isinstance(value, list):
            return [escape_tree(v) for v in value]
        if isinstance(value, dict):
            return {k: escape_tree(v) for k, v in value.items()}
        return value
    js = escape_tree(ko["jsStrings"])
    sn = js["spectralName"]
    sd = js["spectralDesc"]
    nr_y = ko["jsStrings"]["nameRyb"]
    nr_g = ko["jsStrings"]["nameRgb"]
    hc = js["harmoniesCap"]
    sm = js["statusMessages"]
    av = js["ariaValueText"]
    repl = [
        # ── Short HTML labels (chapter h2 titles + hero h1 + scrollcue + footer.mark) ──
        ('<h1>The Book of<br><span class="spectral">Color</span></h1>',
         f'<h1>{ko["hero"]["titleLine1"]}<br><span class="spectral">{ko["hero"]["titleLine2"]}</span></h1>'),
        ('<h2 id="light-h">Light</h2>', f'<h2 id="light-h">{ko["ch1"]["title"]}</h2>'),
        ('<h2 id="eye-h">The Eye</h2>', f'<h2 id="eye-h">{ko["ch2"]["title"]}</h2>'),
        ('<h2 id="mixing-h">Mixing</h2>', f'<h2 id="mixing-h">{ko["ch3"]["title"]}</h2>'),
        ('<h2 id="wheel-h">The Wheel</h2>', f'<h2 id="wheel-h">{ko["ch4"]["title"]}</h2>'),
        ('<h2 id="space-h">Three Dimensions</h2>', f'<h2 id="space-h">{ko["ch5"]["title"]}</h2>'),
        ('<h2 id="spaces-h">Color Spaces</h2>', f'<h2 id="spaces-h">{ko["ch7"]["title"]}</h2>'),
        ('<h2 id="interaction-h">The Interaction of Color</h2>',
         f'<h2 id="interaction-h">{ko["ch8"]["title"]}</h2>'),
        ('<h2 id="practice-h">Color in Practice</h2>', f'<h2 id="practice-h">{ko["ch9"]["title"]}</h2>'),
        ('Begin\n        <svg', f'{ko["hero"]["scrollcue"]}\n        <svg'),
        ('class="footer-mark">The Book of Color</p>',
         f'class="footer-mark">{ko["footer"]["mark"]}</p>'),
        # ── HTML entities (nbsp, amp) ──
        ('Display\xa0P3 gamut', f'Display\xa0P3 {ko["ch7"]["fig"]["cie"]["legendP3"].split(" ", 1)[1] if " " in ko["ch7"]["fig"]["cie"]["legendP3"] else "색역"}'),
        ('Offset\xa0print (CMYK)', ov["offset_nbsp"]),
        ('Kubelka &amp; Munk pigment theory', ov["kubelka_title"]),
        # footer.fine은 collect_pairs로 일반 처리 (이전엔 hard-coded pair 였음).
        ('↑ light · value · dark ↓&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;← grey · saturation · vivid →',
         ov["axisX_nbsp"]),
        # ── JS spectralName function body ──
        (
            """function spectralName(wl){
    if(wl<420) return 'deep violet';
    if(wl<450) return 'violet';
    if(wl<485) return 'blue';
    if(wl<500) return 'cyan';
    if(wl<545) return 'green';
    if(wl<575) return 'yellow-green';
    if(wl<590) return 'yellow';
    if(wl<620) return 'orange';
    if(wl<670) return 'red';
    return 'deep red';
  }""",
            f"""function spectralName(wl){{
    if(wl<420) return '{sn["deepViolet"]}';
    if(wl<450) return '{sn["violet"]}';
    if(wl<485) return '{sn["blue"]}';
    if(wl<500) return '{sn["cyan"]}';
    if(wl<545) return '{sn["green"]}';
    if(wl<575) return '{sn["yellowGreen"]}';
    if(wl<590) return '{sn["yellow"]}';
    if(wl<620) return '{sn["orange"]}';
    if(wl<670) return '{sn["red"]}';
    return '{sn["deepRed"]}';
  }}""",
        ),
        # ── JS spectralDesc function body ──
        (
            """function spectralDesc(wl){
    if(wl<430) return 'The shortest waves the eye admits. Sensitivity is low here — the violet looks dim however bright the light.';
    if(wl<485) return 'Short waves. The S cone is near its peak; the world of sky and shadow.';
    if(wl<500) return 'The blue-green hinge, where the S and M cones trade the lead.';
    if(wl<560) return 'Medium waves. The eye is most alert here — green reads as the brightest hue of all.';
    if(wl<590) return 'The L and M cones fire almost together. A small shift in wavelength swings the hue quickly.';
    if(wl<625) return 'Long waves. The L cone dominates; the M cone is fading out.';
    return 'The longest waves the eye can catch. Past this edge lies infrared — heat you feel but cannot see.';
  }""",
            f"""function spectralDesc(wl){{
    if(wl<430) return '{sd[0]}';
    if(wl<485) return '{sd[1]}';
    if(wl<500) return '{sd[2]}';
    if(wl<560) return '{sd[3]}';
    if(wl<590) return '{sd[4]}';
    if(wl<625) return '{sd[5]}';
    return '{sd[6]}';
  }}""",
        ),
        # ── JS NAME_RYB / NAME_RGB ──
        (
            "var NAME_RYB=['red','red-orange','orange','yellow-orange','yellow','yellow-green',\n                  'green','blue-green','blue','blue-violet','violet','red-violet'];",
            f"var NAME_RYB=[{','.join(repr(n) for n in nr_y)}];",
        ),
        (
            "var NAME_RGB=['red','orange','yellow','chartreuse','green','spring green',\n                  'cyan','azure','blue','violet','magenta','rose'];",
            f"var NAME_RGB=[{','.join(repr(n) for n in nr_g)}];",
        ),
        # ── JS HARMONIES (labels are i18n from ch6 buttons + caps from jsStrings) ──
        (
            "complementary:{ label:'Complementary', offs:[0,180],\n        cap:'Two hues straight across the wheel — the sharpest contrast a pair can hold.' },",
            f"complementary:{{ label:'{js_text(ko['ch6']['fig']['harmony']['btnComplementary'])}', offs:[0,180],\n        cap:'{hc['complementary']}' }},",
        ),
        (
            "analogous:{ label:'Analogous', offs:[0,-30,30],\n        cap:'Three neighbouring hues — one family, quietly at ease together.' },",
            f"analogous:{{ label:'{js_text(ko['ch6']['fig']['harmony']['btnAnalogous'])}', offs:[0,-30,30],\n        cap:'{hc['analogous']}' }},",
        ),
        (
            "triadic:{ label:'Triadic', offs:[0,120,240],\n        cap:'Three hues an equal third of the circle apart — balanced, lively, and stable.' },",
            f"triadic:{{ label:'{js_text(ko['ch6']['fig']['harmony']['btnTriadic'])}', offs:[0,120,240],\n        cap:'{hc['triadic']}' }},",
        ),
        (
            "split:{ label:'Split-complementary', offs:[0,150,210],\n        cap:'A base hue with the two neighbours of its complement — tension, gently softened.' },",
            f"split:{{ label:'{js_text(ko['ch6']['fig']['harmony']['btnSplit'])}', offs:[0,150,210],\n        cap:'{hc['split']}' }},",
        ),
        (
            "tetradic:{ label:'Tetradic', offs:[0,90,180,270],\n        cap:'Four hues at the wheel’s quarter-points — two complementary pairs, a rich chord that wants one color to lead.' },",
            f"tetradic:{{ label:'{js_text(ko['ch6']['fig']['harmony']['btnTetradic'])}', offs:[0,90,180,270],\n        cap:'{hc['tetradic']}' }},",
        ),
        (
            "monochromatic:{ label:'Monochromatic', offs:[0], mono:true,\n        cap:'A single hue, varied only in value and chroma — the most serene scheme of all.' }",
            f"monochromatic:{{ label:'{js_text(ko['ch6']['fig']['harmony']['btnMonochromatic'])}', offs:[0], mono:true,\n        cap:'{hc['monochromatic']}' }}",
        ),
        # ── JS ARIA / status string fragments ──
        ("'Your brain reports: '", f"'{js_text(ko['ch2']['fig']['cone']['verdictPrefix'])}'"),
        ("'perceived ≈ '", f"'{sm['perceivedPrefix']}'"),
        ("'The three disks were returned to their starting positions.'", f"'{sm['diskReset']}'"),
        ("copyBtn.textContent=msg; setTimeout(function(){ copyBtn.textContent='Copy palette'; }",
         f"copyBtn.textContent=msg; setTimeout(function(){{ copyBtn.textContent='{sm['copyBtnDefault']}'; }}"),
        ("' nanometres — '+spectralName(wl)", ov["aria_nanometres"]),
        ("' degrees'", ov["aria_degrees"]),
        ("' Kelvin — '", ov["aria_kelvin"]),
        ("' percent ambient light — '", ov["aria_pct_ambient"]),
    ]
    return repl


def apply_special(html: str, repl: list) -> tuple[str, int]:
    """SPECIAL_REPLACEMENTS 순회. 매칭 카운트 반환."""
    n = 0
    for old, new in repl:
        if old in html:
            html = html.replace(old, new, 1)
            n += 1
    return html, n


def build_lang(lang: str) -> None:
    cfg = LANG_CONFIG[lang]
    print(f"[build] {lang} → {cfg['outputDir']}", file=sys.stderr)

    src = SRC_HTML.read_text(encoding="utf-8")
    en = json.loads(EN_JSON.read_text(encoding="utf-8"))

    if cfg["json"] is None:
        # 영문 baseline — 번역 안 함, meta + hreflang + lang-selector만 처리
        html = apply_lang_meta(src, cfg)
        html = apply_hreflang(html, cfg)
        html = inject_lang_selector(html)
        html = inject_font_fallback(html, lang)
        html = inject_chapter_scroll(html)
        html = inject_timeline_i18n(html, en)
        html = inject_specs_i18n(html, en)
        html = html.replace("{LAST_UPDATED}", LAST_UPDATED)
        cfg["outputDir"].mkdir(parents=True, exist_ok=True)
        out_path = cfg["outputDir"] / "index.html"
        write_page(out_path, html, lang)
        # 영문은 dist root에도 복사 (Vercel `/` 라우팅)
        if cfg["htmlLang"] == "en":
            write_page(DIST / "index.html", html, lang)
            print(f"[build] also wrote {DIST/'index.html'} (root)", file=sys.stderr)
        # Generate chapter deep-link variants. English baseline uses en.json
        # so we load it on demand here.
        en_json = json.loads(EN_JSON.read_text(encoding="utf-8"))
        for slug, ch_key, anchor, ch_n in CHAPTERS:
            ch_html = build_chapter_html(html, cfg, lang, slug, ch_key, ch_n, en_json)
            ch_path = cfg["outputDir"] / slug / "index.html"
            write_page(ch_path, ch_html, lang)
            if cfg["htmlLang"] == "en":
                write_page(DIST / slug / "index.html", ch_html, lang)
        print(f"[build] wrote {out_path} + {len(CHAPTERS)} chapter variants ({len(html)} bytes each)", file=sys.stderr)
        return

    if not cfg["json"].exists():
        raise FileNotFoundError(cfg['json'])

    ko = json.loads(cfg["json"].read_text(encoding="utf-8"))

    # Phase 1: SPECIAL_REPLACEMENTS (짧은 라벨, JS 함수, HTML entity)
    special = special_replacements(ko, lang)
    src, n_special = apply_special(src, special)
    print(f"[build] applied {n_special}/{len(special)} special replacements", file=sys.stderr)

    # Phase 2: 본문 일반 매칭
    pairs = []
    collect_pairs(en, ko, pairs)
    print(f"[build] collected {len(pairs)} translation pairs", file=sys.stderr)

    html, missing = apply_translations(src, pairs)
    html = apply_lang_meta(html, cfg)
    html = apply_hreflang(html, cfg)
    html = inject_lang_selector(html)
    html = inject_font_fallback(html, lang)
    html = inject_chapter_scroll(html)
    _ljson = ko if cfg["json"] is not None else en
    html = inject_timeline_i18n(html, _ljson)
    html = inject_specs_i18n(html, _ljson)
    html = html.replace("{LAST_UPDATED}", LAST_UPDATED)

    cfg["outputDir"].mkdir(parents=True, exist_ok=True)
    out_path = cfg["outputDir"] / "index.html"
    write_page(out_path, html, lang)

    # Generate chapter deep-link variants (10 per language).
    for slug, ch_key, anchor, ch_n in CHAPTERS:
        ch_html = build_chapter_html(html, cfg, lang, slug, ch_key, ch_n, ko)
        ch_path = cfg["outputDir"] / slug / "index.html"
        write_page(ch_path, ch_html, lang)
    print(f"[build] {lang}: +{len(CHAPTERS)} chapter variants", file=sys.stderr)
    print(f"[build] wrote {out_path} ({len(html)} bytes)", file=sys.stderr)

    if missing:
        print(f"\n[build] WARNING: {len(missing)} key(s) not found in source HTML:",
              file=sys.stderr)
        for path, snippet in missing[:20]:
            print(f"  {path}: {snippet!r}", file=sys.stderr)
        if len(missing) > 20:
            print(f"  … and {len(missing) - 20} more", file=sys.stderr)


def public_url(value: str) -> str:
    """Map local URLs to GitHub project Pages, with directory-index routes."""
    value = value.replace(LEGACY_URL, BASE_URL)
    base = urlsplit(BASE_URL)
    url = urlsplit(value)
    if value.startswith('/') and not value.startswith('//'):
        path = url.path
        if base.path and not (path == base.path or path.startswith(base.path + '/')):
            path = base.path + path
        url = url._replace(path=path)
    elif url.scheme != base.scheme or url.netloc != base.netloc:
        return value
    elif base.path and not (url.path == base.path or url.path.startswith(base.path + '/')):
        return value
    path = url.path
    if path and not Path(path).suffix and not path.endswith('/'):
        path += '/'
    return urlunsplit(url._replace(path=path))


def prepare_page(html: str, lang: str = 'en') -> str:
    html = labs.book_links(html, lang)
    html = html.replace(LEGACY_URL, BASE_URL)
    html = re.sub(r'\b(href|src)=("|\')([^"\']*)\2',
                  lambda m: m[1] + '=' + m[2] + public_url(m[3]) + m[2], html)
    canonical_match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    canonical = canonical_match[1] if canonical_match else None
    def metadata(m):
        data = json.loads(m[1])
        def urls(value):
            if isinstance(value, str):
                return public_url(value) if value.startswith(BASE_URL) else value
            if isinstance(value, list):
                return [urls(v) for v in value]
            if isinstance(value, dict):
                return {k: urls(v) for k, v in value.items()}
            return value
        data = urls(data)
        if data.get('@type') == 'Article' and canonical:
            data['url'] = canonical
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + '</script>'
    html = re.sub(r'<script type="application/ld\+json">(.*?)</script>', metadata, html, flags=re.S)
    html = re.sub(r'(<meta name="citation_language" content=")[^"]*',
                  lambda m: m[1] + LANG_CONFIG[lang]['htmlLang'], html)
    # Chapter variants omit other sections: send their cross-references to
    # the full book rather than leaving dead anchors behind.
    ids = set(re.findall(r'\bid="([^"]+)"', html))
    book_path = public_url('/' if lang == 'en' else '/' + lang)
    html = re.sub(r'href="#([^"]+)"',
                  lambda m: m[0] if m[1] in ids else f'href="{book_path}#{m[1]}"', html)
    return html


def write_page(path: Path, html: str, lang: str = 'en') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prepare_page(html, lang), encoding='utf-8')


def copy_static() -> None:
    required = ['tube.png', 'og-image.png', 'about.html', 'cite.html', '404.html']
    required += [f'pdf/book-of-color-{lang}.pdf' for lang in LANG_CONFIG if lang != 'id']
    for name in required:
        src = STATIC / name
        if not src.is_file():
            raise FileNotFoundError(f'Missing static source: {src}')
        if src.suffix == '.html':
            target = DIST / (name if name == '404.html' else src.stem + '/index.html')
            write_page(target, src.read_text(encoding='utf-8'))
        else:
            target = DIST / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
    (DIST / '.nojekyll').touch()
    (DIST / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n')


def main():
    global SRC_HTML, DIST, BASE_URL
    parser = argparse.ArgumentParser(description='Build static HTML for GitHub Pages.')
    parser.add_argument('langs', nargs='*')
    parser.add_argument('--source', type=Path, help='Default: highest numbered index<N>.html in project root')
    parser.add_argument('--output', type=Path, default=DIST)
    parser.add_argument('--base-url', default=BASE_URL)
    args = parser.parse_args()
    if args.source:
        SRC_HTML = args.source.resolve()
    else:
        sources = [p for p in ROOT.glob('index*.html') if re.fullmatch(r'index\d+\.html', p.name)]
        SRC_HTML = max(sources, key=lambda p: int(re.search(r'\d+', p.stem)[0]))
    DIST = args.output.resolve()
    BASE_URL = args.base_url.rstrip('/')
    langs = args.langs or list(LANG_CONFIG)
    if any(lang not in LANG_CONFIG for lang in langs):
        parser.error('Unknown language: ' + ', '.join(set(langs) - set(LANG_CONFIG)))
    for lang, cfg in LANG_CONFIG.items():
        cfg['outputDir'] = DIST / lang
    print(f'[build] source: {SRC_HTML.name}; site: {BASE_URL}/', file=sys.stderr)
    for lang in langs:
        build_lang(lang)
    copy_static()
    lab_urls = labs.generate(DIST, BASE_URL)
    if not args.langs:
        sitemap = generate_sitemap()
        sitemap = re.sub(r'https://[^<"\s]+', lambda m: public_url(m[0]), sitemap)
        sitemap = sitemap.replace('</urlset>', ''.join(f'<url><loc>{url}</loc></url>\n' for url in lab_urls) + '</urlset>')
        (DIST / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    subprocess.run(['node', str(ROOT / 'build/validate.mjs'), str(DIST), BASE_URL], check=True)


if __name__ == "__main__":
    main()

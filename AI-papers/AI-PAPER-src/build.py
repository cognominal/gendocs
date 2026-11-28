#!/usr/bin/env python3
"""Build ~/AI-papers/AI-PAPER.pdf from manifest.json + resumes/NN.html.

Usage: python3 -I build.py            (French, needs chromium)
       LANG_DOC=ru python3 -I build.py  (Russian -> AI-PAPER.ru.pdf)

The Russian edition reads ru/parts/*.json (manifest overlay), ru/glossary.json,
ru/resumes/NN.html and ru/chapters/<dossier>.html (missing dossiers are skipped).

index.json lists the proper names (people, organisations) of the French edition:
aliases are matched in the text and linked to the index, which is built in two
chromium passes (the second one knows the PDF page of every occurrence).
"""
import html, json, os, re, subprocess, unicodedata, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # ~/AI-papers
M = json.load(open(os.path.join(HERE, 'manifest.json')))
LANG = os.environ.get('LANG_DOC', 'fr')
SRC = HERE if LANG == 'fr' else os.path.join(HERE, LANG)

T = {
 'fr': {
  'todo': 'Résumé détaillé à venir.', 'local': 'Fichier local', 'source': 'Source',
  'detail': 'Résumé détaillé', 'card': 'fiche', 'intro_in': 'Introduit dans',
  'origin': 'Origine', 'see': 'Voir', 'dossier': 'Dossier',
  'annex': 'Dossiers et annexe',
  'transformer': 'Dossier : le Transformer, de l\'attention aux grands modèles de langage',
  'mcts': 'Dossier : la recherche arborescente Monte-Carlo (MCTS)',
  'renforcement': 'Dossier : l\'apprentissage par renforcement des LLM, du RLHF au RLVR',
  'attention': 'Dossier : attention efficace et cache KV',
  'alignement': 'Dossier : l\'alignement, des lois d\'Asimov au bouton d\'arrêt',
  'harnais': 'Dossier : les harnais, de la boucle d\'agent aux routeurs de modèles',
  'short': {'transformer': 'Transformer', 'mcts': 'MCTS', 'renforcement': 'Renforcement', 'attention': 'Attention et cache KV', 'alignement': 'Alignement', 'harnais': 'Harnais'},
  'gloss_n': 'Glossaire ({n} termes)', 'gloss': 'Glossaire',
  'engloss_n': 'Lexique anglais-français ({n} termes)', 'engloss': 'Lexique anglais-français',
  'engloss_intro': 'Les termes anglais du glossaire, classés par ordre alphabétique. Chaque terme français '
                   'renvoie à son entrée dans le glossaire.',
  'gloss_intro': 'Termes techniques employés dans ce document, classés par ordre alphabétique. '
                 '« Introduit dans » renvoie à la fiche du papier qui a introduit ou popularisé le concept ; '
                 '« Origine » cite le travail fondateur quand il ne fait pas partie de la collection ; '
                 '« Voir » renvoie aux fiches où le concept joue un rôle important.',
  'timeline': "L'évolution de l'IA à travers ses papiers", 'toc': 'Sommaire',
  'chrono': 'Sommaire chronologique',
  'chrono_intro': 'Les papiers de la collection classés par année de première publication, avec les travaux '
                  'et œuvres hors collection (en italique) dont parlent les dossiers ; ceux-ci renvoient à la '
                  'section du dossier qui les présente.',
  'see_dossier': 'Voir le dossier', 'index': 'Index des noms propres',
  'index_n': 'Index des noms propres ({n} noms)', 'pp': 'p.',
  'index_intro': 'Personnes et organisations citées. Les numéros renvoient aux pages du PDF où le nom apparaît ; '
                 'le lien Wikipédia mène à l\'article français, ou à défaut anglais. Dans le texte, chaque nom '
                 'est un lien discret (souligné en pointillé) vers son entrée ici.',
  'pdf': 'AI-PAPER.pdf', 'html': 'AI-PAPER.html',
 },
 'ru': {
  'todo': 'Подробное резюме будет позже.', 'local': 'Локальный файл', 'source': 'Источник',
  'detail': 'Подробное резюме', 'card': 'карточка', 'intro_in': 'Введено в',
  'origin': 'Происхождение', 'see': 'См.', 'dossier': 'Досье',
  'annex': 'Досье и приложение',
  'transformer': 'Досье: Transformer, от внимания к большим языковым моделям',
  'mcts': 'Досье: поиск по дереву методом Монте-Карло (MCTS)',
  'renforcement': 'Досье: обучение с подкреплением для LLM, от RLHF до RLVR',
  'attention': 'Досье: эффективное внимание и KV-кэш',
  'alignement': 'Досье: согласование ИИ, от законов Азимова до кнопки выключения',
  'harnais': 'Досье: обвязки агентов, от агентного цикла до маршрутизаторов моделей',
  'short': {'transformer': 'Transformer', 'mcts': 'MCTS', 'renforcement': 'Обучение с подкреплением', 'attention': 'Внимание и KV-кэш', 'alignement': 'Согласование', 'harnais': 'Обвязки'},
  'gloss_n': 'Глоссарий ({n} терминов)', 'gloss': 'Глоссарий',
  'engloss_n': 'Англо-русский словарь ({n} терминов)', 'engloss': 'Англо-русский словарь',
  'engloss_intro': 'Английские термины глоссария в алфавитном порядке. Каждый русский термин '
                   'ведёт к своей статье в глоссарии.',
  'gloss_intro': 'Технические термины, используемые в этом документе, в алфавитном порядке. '
                 '«Введено в» отсылает к карточке статьи, которая ввела или популяризировала понятие; '
                 '«Происхождение» указывает основополагающую работу, если она не входит в подборку; '
                 '«См.» отсылает к карточкам, где понятие играет важную роль.',
  'timeline': 'Эволюция ИИ в его статьях', 'toc': 'Содержание',
  'chrono': 'Хронологическое содержание',
  'chrono_intro': 'Статьи подборки по году первой публикации, а также работы и произведения вне подборки '
                  '(курсивом), о которых говорится в досье; они ведут к разделу досье, где о них идёт речь.',
  'see_dossier': 'См. досье', 'index': 'Указатель имён', 'index_n': 'Указатель имён ({n})', 'pp': 'с.',
  'index_intro': '',
  'pdf': 'AI-PAPER.ru.pdf', 'html': 'AI-PAPER.ru.html',
 },
}[LANG]

DOSSIERS = ['transformer', 'mcts', 'renforcement', 'attention', 'alignement', 'harnais']
# each dossier is chapters/<id>.html, or a folder chapters/<id>/ whose *.html parts are
# concatenated in name order; anchor #<id>. Parts may open with <h3 class="part" id="...">,
# which are listed under the dossier in the table of contents.

SECTION_NAMES = {}
if LANG != 'fr':
    # overlay translated fields; section keys stay French (colours, secintro)
    for part in sorted(os.listdir(os.path.join(SRC, 'parts'))):
        D = json.load(open(os.path.join(SRC, 'parts', part)))
        if part.startswith('entries'):
            for e in M['entries']:
                if str(e['n']) in D:
                    e.update(D[str(e['n'])])
        else:
            SECTION_NAMES = D.pop('sections', SECTION_NAMES)
            M.update(D)
    missing = [e['n'] for e in M['entries'] if not any(
        str(e['n']) in json.load(open(os.path.join(SRC, 'parts', p)))
        for p in os.listdir(os.path.join(SRC, 'parts')) if p.startswith('entries'))]
    assert not missing, f'untranslated entries: {missing}'


def sec_name(s):
    return SECTION_NAMES.get(s, s)

SECTION_COLORS = {
    'Fondateurs': '#6b6b6b',
    'Anthropic': '#c4623a',
    'OpenAI': '#10a37f',
    'DeepSeek': '#4d6bfe',
    'Dernières nouveautés (septembre 2026)': '#8a3ffc',
    'Autres papiers importants de 2026': '#c2410c',
    'Raisonnement, agents et chaîne de pensée': '#b45309',
    'Autres papiers de référence': '#0e7490',
    'Nouveautés octobre–novembre 2026': '#be185d',
    'Contrôle et arrêt des IA': '#991b1b',
    'Harnais, outils et routage': '#0e7490',
}
DEFAULT_COLOR = '#0f766e'


def esc(s):
    return html.escape(s, quote=True)


def file_href(name):
    return '../' + urllib.parse.quote(name)


PAPER_REF = re.compile(r'\b([Pp]apiers?|[Ff]iches?|[Сс]тать[яиюей]) (\d+(?:(?:, | et | à | и | – )\d+)*)')


def link_papers(src, known):
    """Link "papier 18", "papiers 25, 26 et 23" (Russian: "статья 33", "статьи 22 и 21") to the
    papers' summaries; text already inside a link is left alone."""
    def sub(m):
        word, nums = m.groups()
        parts = re.split(r'(\d+)', nums)  # ['', '25', ', ', '26', ' et ', '23', '']
        out = []
        for i, x in enumerate(parts):
            if x.isdigit() and int(x) in known:
                text = f'{word} {x}' if i == 1 else x
                out.append(f'<a href="#p{x}">{text}</a>')
            else:
                out.append(f'{word} {x}' if i == 1 else x)
        return ''.join(out)
    out, in_a = [], False
    for tok in re.split(r'(<[^>]+>)', src):
        if tok.startswith('<'):
            if re.match(r'<a\b', tok, re.I):
                in_a = True
            elif re.match(r'</a\s*>', tok, re.I):
                in_a = False
            out.append(tok)
        else:
            out.append(tok if in_a else PAPER_REF.sub(sub, tok))
    return ''.join(out)


def entry_html(e):
    n = e['n']
    detail_path = os.path.join(SRC, 'resumes', f'{n:02d}.html')
    detail = link_papers(open(detail_path).read(), {x['n'] for x in M['entries']}) \
        if os.path.exists(detail_path) else f'<p class="todo">{T["todo"]}</p>'
    bullets = ''.join(f'<li>{esc(b)}</li>' for b in e.get('bullets', []))
    return f'''
<article class="paper" id="p{n}">
  <h3>{n}. {esc(e['title'])}</h3>
  <div class="meta">{esc(e['meta'])}</div>
  <div class="links">{T['local']} : <a href="{file_href(e['file'])}">{esc(e['file'])}</a>
    &nbsp;·&nbsp; {T['source']} : <a href="{esc(e['source'])}">{esc(e['source'])}</a></div>
  <div class="tldr">
    <p class="lead">{esc(e['summary'])}</p>
    <ul>{bullets}</ul>
  </div>{see_dossiers(n)}
  <section class="detail">
    <div class="detail-label">{T['detail']}</div>
    {detail}
  </section>
</article>'''


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def sort_key(t):
    """Alphabetical key: ASCII slug for Latin terms, lower-case for Cyrillic ones."""
    if re.search('[а-яёА-ЯЁ]', t[:3]):
        return re.sub(r'[^0-9a-zа-яё]+', '-', t.lower().replace('ё', 'е')).strip('-')
    return slug(t)


def short_title(e):
    t = re.split(r'\s+[—:]\s*|:\s', e['title'])[0]
    return t if len(t) <= 48 else t[:46] + '…'


AVAILABLE = set()  # dossiers actually built (filled in main)
FICHE_DOSSIERS = {  # fiche number -> dossiers that develop its subject
    'transformer': [3, 6, 9, 10, 24, 32, 36, 37, 47, 53, 65, 86, 87, 88, 89, 91, 93, 96],
    'mcts': [8, 33, 59, 70, 73],
    'renforcement': [16, 27, 29, 33, 34, 44, 52, 55, 61, 69, 71, 72, 74, 75, 76, 80, 82],
    'attention': [9, 31, 32, 35, 45, 51, 87],
    'alignement': [2, 16, 17, 18, 19, 20, 27, 28, 29, 58, 74, 80, 82, 99, 101, 103, 104, 105, 106],
    'harnais': [44, 56, 57, 60, 64, 95, 107, 108, 109, 110, 111, 112, 113, 114, 115],
}


def chapter_parts_toc(c):
    parts = re.findall(r'<h3 class="part[^"]*" id="([^"]+)">(.*?)</h3>', c, re.S)
    if not parts:
        return ''
    return ('<ol class="toc-parts">' + ''.join(
        f'<li><a href="#{i}">{re.sub(r"<[^>]+>", "", t)}</a></li>' for i, t in parts) + '</ol>')


HEAD_NUM = re.compile(r'<h4(\s[^>]*)?>(\s*)([\dIVX]+(?:\.\d+)*)(\.?\s)')


def number_headings(d, c):
    """Give each numbered <h4> of dossier d an id "d-<number>" ("alignement-1", "transformer-5.4")."""
    def sub(m):
        attrs = m.group(1) or ''
        if ' id=' in attrs:
            return m.group(0)
        return f'<h4 id="{d}-{m.group(3)}"{attrs}>{m.group(2)}{m.group(3)}{m.group(4)}'
    return HEAD_NUM.sub(sub, c)


def chrono_html(entries, chapters):
    """Papers by year of first publication, interleaved with works outside the collection
    (chrono_extra.json) that link to the dossier section discussing them."""
    years = {}
    for e in entries:
        y = int(re.search(r'\b(?:19|20)\d\d\b', e['meta']).group())
        years.setdefault(y, []).append(
            f'<li><a href="#p{e["n"]}"><span class="cn">{e["n"]}.</span> {esc(e["title"])}</a></li>')
    for x in json.load(open(os.path.join(HERE, 'chrono_extra.json'))):
        to = next(((d, k) for d, k in x['to'] if d in chapters), None)
        if to is None:
            continue
        years.setdefault(x['y'], []).append(
            f'<li class="cx"><a href="#{to[0]}-{to[1]}">{esc(x[LANG])}</a> '
            f'<span class="cd">→ {T["short"][to[0]]} § {to[1]}</span></li>')
    return ''.join(f'<div class="cy"><h3>{y}</h3><ul>{"".join(items)}</ul></div>'
                   for y, items in sorted(years.items()))


def see_dossiers(n):
    ds = [d for d in DOSSIERS if d in AVAILABLE and n in FICHE_DOSSIERS.get(d, [])]
    if not ds:
        return ''
    return (f'<div class="see-dossier">{T["see_dossier"]} : '
            + ', '.join(f'<a href="#{d}">{T["short"][d]}</a>' for d in ds) + '</div>')


# ---- index of proper names (index.json: id, name, sort, kind p|o, aliases, wiki) ----
SKIP_TAGS = {'a', 'h1', 'h2', 'h3', 'h4', 'svg', 'style', 'title', 'code', 'pre', 'script'}


def load_index():
    path = os.path.join(SRC, 'index.json')
    if not os.path.exists(path):
        return []
    return json.load(open(path))


def name_regex(I):
    """One alternation over all aliases, longest first; group name = entry position."""
    alts = []
    for i, e in enumerate(I):
        # organisations must not swallow product names (DeepSeek-V3), people may be
        # hyphenated with another name (Taylor-Wiles) but not with a suffix (Hinton-like-...)
        tail = r'(?![\w-])' if e['kind'] == 'o' else r'(?!\w)(?!-[a-z0-9])'
        for a in e['aliases']:
            rx = a[3:] if a.startswith('re:') else re.escape(html.escape(a, quote=False)).replace("'", "(?:'|&#x27;|’)")
            alts.append((len(a), rf'(?<!\w)(?:{rx}){tail}', i))
    alts.sort(key=lambda t: -t[0])
    return re.compile('|'.join(f'(?P<n{i}_{k}>{rx})' for k, (_, rx, i) in enumerate(alts)))


def link_names(src, I, rx, occ):
    """Wrap proper names in text nodes with links to their index entry; record ids in occ."""
    out, skip, depth = [], None, 0
    for tok in re.split(r'(<[^>]+>)', src):
        if tok.startswith('<'):
            m = re.match(r'<(/?)([a-zA-Z0-9]+)', tok)
            if m:
                close, name = m.group(1) == '/', m.group(2).lower()
                selfclose = tok.endswith('/>')
                if skip:
                    if name == skip and not selfclose:
                        depth += -1 if close else 1
                        if depth == 0:
                            skip = None
                elif not close and not selfclose and (name in SKIP_TAGS or
                                                      (name == 'div' and 'class="links"' in tok)):
                    skip, depth = name, 1
            out.append(tok)
        elif skip or not tok.strip():
            out.append(tok)
        else:
            def sub(m):
                i = int(m.lastgroup[1:].split('_')[0])
                eid = I[i]['id']
                occ.setdefault(eid, []).append(f'o-{eid}-{len(occ.get(eid, [])) + 1}')
                return f'<a class="np" id="{occ[eid][-1]}" href="#i-{eid}">{m.group()}</a>'
            out.append(rx.sub(sub, tok))
    return ''.join(out)


def index_html(I, occ, pages):
    """pages: occurrence id -> PDF page (None on the first pass: link every occurrence)."""
    rows, letter = [], None
    for e in sorted((e for e in I if occ.get(e['id'])), key=lambda e: sort_key(e['sort'])):
        L = sort_key(e['sort'])[0].upper()
        if L != letter:
            letter = L
            rows.append(f'<div class="gl-letter">{L}</div>')
        if e['kind'] == 'p':  # "Surname, Given names"; sort may be "Surname Given" (Chen Kai)
            sur = e['sort'] if e['sort'] in e['name'] else e['sort'].split()[0]
            rest = ' '.join(w for w in e['name'].split() if w not in sur.split())
            head = f'<b>{esc(sur)}</b>, {esc(rest)}' if rest else f'<b>{esc(e["name"])}</b>'
        else:
            head = f'<b>{esc(e["name"])}</b>'
        if pages is None:
            refs = ' '.join(f'<a href="#{o}">·</a>' for o in occ[e['id']])
        else:
            seen = {}
            for o in occ[e['id']]:
                seen.setdefault(pages[o], o)
            refs = ', '.join(f'<a href="#{o}">{pg}</a>' for pg, o in sorted(seen.items()))
        w = ''
        if e.get('wiki'):
            lab = 'Wikipédia' if '//fr.' in e['wiki'] else 'Wikipedia (en)'
            w = f' · <a class="wk" href="{esc(e["wiki"])}">{lab}</a>'
        rows.append(f'<div class="ix" id="i-{e["id"]}">{head} — {T["pp"]} {refs}{w}</div>')
    return '\n'.join(rows)


def pdf_dests(pdf):
    """Named destination -> 1-based page number, read with qpdf."""
    J = json.loads(subprocess.run(['qpdf', '--json', pdf], capture_output=True, check=True).stdout)
    objs = J['qpdf'][1]
    page_no = {p['object']: k + 1 for k, p in enumerate(J['pages'])}
    val = lambda ref: objs[f'obj:{ref}']['value'] if isinstance(ref, str) and ref.endswith(' R') else ref
    root = val(objs['trailer']['value']['/Root'])
    out = {}

    def add(name, d):
        d = val(d)
        if isinstance(d, dict):
            d = val(d['/D'])
        out[name.lstrip('/').removeprefix('u:')] = page_no.get(d[0])
    if '/Dests' in root:
        for k, v in val(root['/Dests']).items():
            add(k, v)
    names = val(root.get('/Names', {})) or {}
    stack = [val(names['/Dests'])] if '/Dests' in names else []
    while stack:
        node = stack.pop()
        stack += [val(k) for k in node.get('/Kids', [])]
        arr = node.get('/Names', [])
        for k in range(0, len(arr), 2):
            add(arr[k], arr[k + 1])
    return out


def glossary_html(by_n):
    G = json.load(open(os.path.join(SRC, 'glossary.json')))
    for g in G:
        g.setdefault('id', slug(g['t']))
    G.sort(key=lambda g: sort_key(g['t']))
    ids = [g['id'] for g in G]
    assert len(ids) == len(set(ids)), 'duplicate glossary ids'

    def refs(ns):
        return ', '.join(f'<a href="#p{n}">{T["card"]} {n}</a> <span class="gt">({esc(short_title(by_n[n]))})</span>'
                         for n in ns)
    out, letter = [], None
    for g in G:
        L = sort_key(g['t'])[0].upper()
        if L != letter:
            letter = L
            out.append(f'<div class="gl-letter">{L}</div>')
        en = f' <span class="gen">({esc(g["en"])})</span>' if g.get('en') else ''
        lines = []
        if g.get('src'):
            lines.append(f'<span class="glab">{T["intro_in"]}</span> {refs(g["src"])}')
        if g.get('ext'):
            lines.append(f'<span class="glab">{T["origin"]}</span> {esc(g["ext"])}')
        if g.get('see'):
            lines.append(f'<span class="glab">{T["see"]}</span> {refs(g["see"])}')
        ds = [d for d in (['mcts'] if g.get('mcts') else []) + g.get('dossiers', []) if d in AVAILABLE]
        if ds:
            lines.append(f'<span class="glab">{T["dossier"]}</span> '
                         + ', '.join(f'<a href="#{d}">{T["short"][d]}</a>' for d in ds))
        out.append(f'<div class="gl" id="g-{g["id"]}"><b>{esc(g["t"])}</b>{en}. {esc(g["d"])}'
                   + ''.join(f'<div class="gref">{x}</div>' for x in lines) + '</div>')
    return len(G), set(ids), '\n'.join(out), G


def en_keys(g, fr_keys):
    """English names of a glossary entry: explicit en_keys (French glossary, or borrowed from it via
    the shared 'en' value), else the comma-separated 'en', else the term itself when it is Latin-script."""
    if g.get('en_keys'):
        return g['en_keys']
    if g.get('en'):
        return fr_keys.get(g['en']) or [k.strip() for k in g['en'].split(',')]
    t = re.sub(r'\s*\(.*?\)', '', g['t'])
    return [] if re.search('[а-яёА-ЯЁ]', t) else [t]


def english_html(G):
    """English -> glossary lexicon: one line per English key, linking to every entry it names."""
    fr = json.load(open(os.path.join(HERE, 'glossary.json')))
    fr_keys = {g['en']: g['en_keys'] for g in fr if g.get('en') and g.get('en_keys')}
    by_key = {}
    for g in G:
        for k in en_keys(g, fr_keys):
            by_key.setdefault(k, []).append(g)
    out, letter = [], None
    for k in sorted(by_key, key=lambda k: (slug(k), k)):
        L = slug(k)[0].upper()
        if L != letter:
            letter = L
            out.append(f'<div class="gl-letter">{L}</div>')
        out.append(f'<div class="en-l"><span class="en-k">{esc(k)}</span> '
                   + ', '.join(f'<a href="#g-{g["id"]}">{esc(g["t"])}</a>' for g in by_key[k]) + '</div>')
    return len(by_key), '\n'.join(out)


def main():
    entries = M['entries']
    by_n = {e['n']: e for e in entries}
    chapters = {}
    for d in DOSSIERS:
        path = os.path.join(SRC, 'chapters', f'{d}.html')
        folder = os.path.join(SRC, 'chapters', d)
        if os.path.isdir(folder):
            chapters[d] = '\n'.join(open(os.path.join(folder, f)).read()
                                    for f in sorted(os.listdir(folder)) if f.endswith('.html'))
        elif os.path.exists(path):
            chapters[d] = open(path).read()
        else:
            print(f'warning: {path} missing, dossier skipped')
    known = {e['n'] for e in entries}
    chapters = {d: number_headings(d, link_papers(c, known)) for d, c in chapters.items()}
    AVAILABLE.update(chapters)
    n_gloss, gids, gloss, G = glossary_html(by_n)
    n_en, english = english_html(G)
    sections = []
    for e in entries:
        if not sections or sections[-1][0] != e['section']:
            sections.append((e['section'], []))
        sections[-1][1].append(e)

    toc = ''.join(
        f'<li><a class="toc-sec" href="#s-{slug(s)}" style="color:{SECTION_COLORS.get(s, DEFAULT_COLOR)}">{esc(sec_name(s))}</a>'
        f'<ol start="{es[0]["n"]}">' +
        ''.join(f'<li><a href="#p{e["n"]}">{esc(e["title"])}</a></li>' for e in es) +
        '</ol></li>' for s, es in sections)
    toc = f'<li><a class="toc-sec" href="#chrono" style="color:#7c2d12">{T["chrono"]}</a></li>' + toc
    chrono = chrono_html(entries, chapters)
    toc += (f'<li><a class="toc-sec" href="#{next(iter(chapters), "lexique")}" style="color:#7c2d12">{T["annex"]}</a><ul class="toc-x">'
            + ''.join(f'<li><a href="#{d}">{T[d]}</a>{chapter_parts_toc(c)}</li>' for d, c in chapters.items()) +
            f'<li><a href="#lexique">{T["engloss_n"].format(n=n_en)}</a></li>'
            f'<li><a href="#glossaire">{T["gloss_n"].format(n=n_gloss)}</a></li>'
            '{{INDEX_TOC}}</ul></li>')

    body = ''
    for s, es in sections:
        intro = M['secintro'].get(s, '')
        body += (f'<section class="sec" id="s-{slug(s)}"><h2 style="color:{SECTION_COLORS.get(s, DEFAULT_COLOR)}">{esc(sec_name(s))}</h2>'
                 + (f'<p class="secintro">{esc(intro)}</p>' if intro else '')
                 + ''.join(entry_html(e) for e in es) + '</section>')
    body += ''.join(f'<section class="sec chap" id="{d}"><h2 style="color:#7c2d12">{T[d]}</h2>{c}</section>'
                    for d, c in chapters.items())
    body += (f'<section class="sec" id="lexique"><h2 style="color:#7c2d12">{T["engloss"]}</h2>'
             f'<p class="secintro">{T["engloss_intro"]}</p>'
             f'<div class="gloss">{english}</div></section>')
    body += (f'<section class="sec" id="glossaire"><h2 style="color:#7c2d12">{T["gloss"]}</h2>'
             f'<p class="secintro">{T["gloss_intro"]}</p>'
             f'<div class="gloss">{gloss}</div></section>')
    timeline = M['timeline_html'] if 'timeline_html' in M else '<p>' + esc(M['intro']) + '</p>'
    # proper names: link every occurrence to the index (French edition only: aliases are Latin-script)
    I = load_index() if LANG == 'fr' else []
    occ = {}
    if I:
        rx = name_regex(I)
        timeline = link_names(timeline, I, rx, occ)
        body = link_names(body, I, rx, occ)
        unused = [e['id'] for e in I if e['id'] not in occ]
        if unused:
            print('warning: index entries never found in the text:', ', '.join(unused))
        n_idx = sum(1 for e in I if e['id'] in occ)
        toc = toc.replace('{{INDEX_TOC}}', f'<li><a href="#index">{T["index_n"].format(n=n_idx)}</a></li>')
        body += (f'<section class="sec" id="index"><h2 style="color:#7c2d12">{T["index"]}</h2>'
                 f'<p class="secintro">{T["index_intro"]}</p><div class="gloss">{{{{INDEX}}}}</div></section>')
    toc = toc.replace('{{INDEX_TOC}}', '')
    # every internal link must resolve
    anchors = ({f'p{n}' for n in by_n} | {f'g-{i}' for i in gids} | set(chapters) | {'glossaire', 'lexique', 'chrono'}
               | {i for c in chapters.values() for i in re.findall(r'\sid="([^"]+)"', c)}
               | {f's-{slug(s)}' for s, _ in sections}
               | ({'index'} | {f'i-{i}' for i in occ} | {o for os_ in occ.values() for o in os_} if occ else set()))
    bad = sorted({h for h in re.findall(r'href="#([^"]+)"', body + toc + timeline + chrono) if h not in anchors})
    assert not bad, f'broken internal links: {bad}'

    doc = f'''<!doctype html><html lang="{LANG}"><head><meta charset="utf-8">
<title>IA-PAPER</title>
<style>
@page {{ size: A4; margin: 18mm 18mm 20mm 18mm; }}
body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10.3pt;
       line-height: 1.5; color: #1f1f1f; background: #fff; }}
a {{ color: #1d4ed8; }}
h1 {{ text-align: center; font-size: 26pt; margin: 0 0 2pt; }}
.subtitle {{ text-align: center; color: #666; margin-bottom: 18pt; }}
h2 {{ font-size: 18pt; page-break-before: always; margin-top: 0; }}
h2.first {{ page-break-before: auto; }}
.timeline h3 {{ font-size: 12pt; margin: 12pt 0 3pt; }}
.timeline p {{ text-align: justify; margin: 0 0 6pt; }}
.secintro, .intro {{ color: #666; text-align: justify; }}
.toc ol {{ margin: 2pt 0 6pt; padding-left: 22pt; }}
.toc > ul {{ list-style: none; padding: 0; columns: 1; }}
.toc li {{ margin: 1pt 0; font-size: 9.5pt; }}
.toc a {{ color: #1d4ed8; text-decoration: none; }}
.toc li a:hover {{ text-decoration: underline; }}
.toc a.toc-sec {{ font-weight: bold; font-size: 11pt; text-decoration: none; }}
.paper {{ margin-top: 16pt; }}
.paper + .paper {{ page-break-before: always; }}
.paper h3 {{ font-size: 14pt; margin: 0 0 2pt; }}
.meta {{ color: #777; font-style: italic; }}
.links {{ font-size: 8pt; word-break: break-all; margin: 2pt 0 6pt; }}
.tldr {{ background: #f5f5f4; border-left: 3px solid #bbb; padding: 4pt 10pt; margin: 6pt 0 10pt; }}
.tldr .lead {{ margin: 4pt 0; text-align: justify; }}
.tldr ul {{ margin: 2pt 0 4pt; padding-left: 16pt; font-size: 9.5pt; }}
.detail-label {{ font-size: 8pt; text-transform: uppercase; letter-spacing: .08em; color: #999; }}
.detail h4 {{ font-size: 11pt; margin: 9pt 0 2pt; }}
.detail p {{ text-align: justify; margin: 0 0 5pt; }}
.detail ul {{ margin: 0 0 5pt; padding-left: 16pt; }}
.detail li {{ margin-bottom: 2pt; text-align: justify; }}
.todo {{ color: #b91c1c; }}
.cys {{ columns: 2; column-gap: 16pt; }}
.cy {{ break-inside: avoid-column; }}
.cy h3 {{ font-size: 10.5pt; color: #7c2d12; margin: 6pt 0 1pt; border-bottom: 1px solid #e5e7eb; }}
.cy ul {{ list-style: none; padding: 0; margin: 0; }}
.cy li {{ font-size: 8.6pt; margin: 1pt 0; padding-left: 12pt; text-indent: -12pt; }}
.cy a {{ color: #1d4ed8; text-decoration: none; }}
.cy .cn {{ color: #6b7280; }}
.cy li.cx a {{ font-style: italic; color: #92400e; }}
.cy .cd {{ color: #9ca3af; font-size: 7.6pt; }}
.toc-x {{ list-style: none; padding-left: 22pt; margin: 2pt 0 6pt; }}
.chap h4 {{ font-size: 12pt; margin: 12pt 0 3pt; color: #7c2d12; break-after: avoid; page-break-after: avoid; }}
.chap h3.part {{ font-size: 15pt; color: #7c2d12; border-bottom: 2px solid #e7d5c9; padding-bottom: 2pt;
                margin: 0 0 6pt; page-break-before: always; }}
.chap h3.part.first {{ page-break-before: auto; margin-top: 14pt; }}
.chap h5 {{ font-size: 10.5pt; margin: 8pt 0 2pt; color: #444; }}
.toc-parts {{ margin: 1pt 0 3pt; padding-left: 18pt; font-size: 9pt; list-style: none; }}
.box {{ background: #fbf6f2; border: 1px solid #e7d5c9; border-radius: 4pt; padding: 5pt 10pt; margin: 6pt 0 10pt;
       break-inside: avoid; font-size: 9.6pt; }}
.box .box-t {{ font-weight: bold; color: #7c2d12; margin-bottom: 2pt; }}
.chap p {{ text-align: justify; margin: 0 0 6pt; }}
.chap li {{ margin-bottom: 3pt; text-align: justify; }}
.chap .chap-lead {{ font-size: 11pt; color: #444; }}
.formula {{ text-align: center !important; font-family: "Times New Roman", serif; font-size: 12.5pt; margin: 6pt 0 8pt !important; }}
.fig {{ margin: 8pt 0 10pt; break-inside: avoid; }}
.fig figcaption {{ font-size: 8.5pt; color: #777; text-align: center; }}
pre.code {{ background: #f5f5f4; border-left: 3px solid #b45309; padding: 6pt 10pt; font-size: 8.3pt;
           line-height: 1.35; white-space: pre-wrap; break-inside: avoid; }}
.refs {{ font-size: 9pt; }}
.chap-table {{ border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 4pt 0 10pt; break-inside: avoid; }}
.chap-table th, .chap-table td {{ border-bottom: 1px solid #e7d5c9; padding: 3pt 5pt; text-align: left; vertical-align: top; }}
.chap-table th {{ color: #7c2d12; }}
.gloss {{ columns: 2; column-gap: 16pt; font-size: 8.8pt; line-height: 1.38; }}
.gl {{ break-inside: avoid; margin: 0 0 5pt; text-align: justify; }}
.gl-letter {{ font-weight: bold; font-size: 13pt; color: #7c2d12; border-bottom: 1px solid #e7d5c9;
             margin: 6pt 0 3pt; break-after: avoid; }}
.gen {{ color: #777; font-style: italic; }}
.en-l {{ break-inside: avoid; margin: 0 0 1.5pt; padding-left: 10pt; text-indent: -10pt; }}
.en-k {{ font-style: italic; }}
.en-k::after {{ content: " \\2192"; color: #b45309; font-style: normal; }}
.en-l a {{ text-decoration: none; }}
.gref {{ font-size: 8pt; color: #555; padding-left: 8pt; }}
.glab {{ font-variant: small-caps; color: #7c2d12; }}
.gt {{ color: #888; }}
.see-dossier {{ font-size: 9pt; margin: -4pt 0 8pt; color: #7c2d12; }}
a.np {{ color: inherit; text-decoration: none; border-bottom: 1px dotted #9ca3af; }}
.ix {{ break-inside: avoid; margin: 0 0 2pt; padding-left: 10pt; text-indent: -10pt; }}
.ix a {{ text-decoration: none; }}
.ix a.wk {{ color: #6b7280; font-size: 8pt; }}
</style></head><body>
<h1>IA-PAPER</h1>
<div class="subtitle">{esc(M.get('subtitle', ''))}</div>
<section class="timeline"><h2 class="first">{T['timeline']}</h2>
{timeline}
</section>
<section class="toc"><h2>{T['toc']}</h2><ul>{toc}</ul></section>
<section class="sec chrono" id="chrono"><h2 style="color:#7c2d12">{T['chrono']}</h2>
<p class="secintro">{T['chrono_intro']}</p><div class="cys">{chrono}</div></section>
{body}
</body></html>'''
    out_html = os.path.join(HERE, T['html'])
    out_pdf = os.environ.get('OUT_PDF', os.path.join(ROOT, T['pdf']))

    def render(d):
        open(out_html, 'w').write(d)
        subprocess.run(['chromium', '--headless', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={out_pdf}', 'file://' + out_html],
                       check=True, stderr=subprocess.DEVNULL)
    if occ:
        # pass 1 links every occurrence so chromium emits a named destination for each;
        # pass 2 replaces them by page numbers (the index is last, earlier pages don't move)
        render(doc.replace('{{INDEX}}', index_html(I, occ, None)))
        dests = pdf_dests(out_pdf)
        missing = [o for os_ in occ.values() for o in os_ if not dests.get(o)]
        assert not missing, f'occurrences without a page: {missing[:10]}'
        doc = doc.replace('{{INDEX}}', index_html(I, occ, dests))
    render(doc)
    print(out_pdf)


if __name__ == '__main__':
    main()

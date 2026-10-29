import os, re, json, glob, html
from os import path

ROOT = path.dirname(path.abspath(__file__))
os.chdir(ROOT)

DESIGN     = 'assets'
FRAME_STEP = 10      # segundos entre frames
RELATED    = 8       # vídeos relacionados por post

# ================ config (setups_1234.yml) ================ #
def load_vars(f):
    """lê chave: "valor" (ignora linhas comentadas com #)"""
    out = {}
    for line in open(f, encoding='utf-8'):
        m = re.match(r'\s*([A-Za-z_]\w*)\s*:\s*"?([^"#\n]*?)"?\s*(?:#.*)?$', line)
        if m and not line.lstrip().startswith('#'):
            out[m.group(1)] = m.group(2)
    return out


def input_timeout(prompt, seconds=5):
    """pergunta com tempo limite (Windows e Linux/Mac); vazio/timeout = None"""
    import sys, time
    print(prompt, end='', flush=True)
    buf = ''
    end = time.time() + seconds
    if os.name == 'nt':
        import msvcrt
        while time.time() < end:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\r', '\n'):
                    print()
                    return buf.strip() or None
                if ch == '\b':
                    buf = buf[:-1]
                else:
                    buf += ch
                print(ch if ch != '\b' else '\b \b', end='', flush=True)
                end = time.time() + seconds      # digitando: renova o tempo
            else:
                time.sleep(0.05)
    else:
        import select
        r, _, _ = select.select([sys.stdin], [], [], seconds)
        if r:
            return sys.stdin.readline().strip() or None
    print()
    return None


def choose_theme(default):
    """lista os temas numerados; 5s para escolher, senão usa o default do YAML"""
    themes = sorted(d for d in os.listdir(f'{DESIGN}/themes') if path.isdir(f'{DESIGN}/themes/{d}'))
    for i, t in enumerate(themes, 1):
        print(f'  {i:2d}) {t}' + ('   <- default' if t == default else ''))
    ans = input_timeout(f'Tema [1-{len(themes)}] (5s, Enter = {default}): ')
    if ans and ans.isdigit() and 1 <= int(ans) <= len(themes):
        return themes[int(ans) - 1]
    if ans:
        print(f'"{ans}" inválido, usando {default}')
    return default


VARS         = load_vars('setups_1234.yml')
THEME        = choose_theme(VARS['front_theme'])
USER_NUM     = int(VARS['user_num'])
PAGE_COUNTER = VARS['page_counter']

if not path.isdir(f'{DESIGN}/themes/{THEME}'):
    raise SystemExit(f'Tema não encontrado: {THEME}')
NAME = json.load(open(f'{DESIGN}/themes/{THEME}/manifest.json', encoding='utf-8'))['name']
print(f'tema={THEME} user_num={USER_NUM} page_counter={PAGE_COUNTER}')


# ================ helpers ================ #
def num_of(f):
    m = re.match(r'(\d+)', path.basename(f))
    return int(m.group(1)) if m else None


def files_of(folder, num, exts):
    return [f for f in sorted(glob.glob(f'{folder}/*'))
            if num_of(f) == num and f.lower().endswith(exts)]


def frames_of(num):
    """frames do vídeo: arquivos soltos (001_*.jpg) ou dentro de videos_frames/001/"""
    exts, out = ('.jpg', '.jpeg', '.png', '.webp'), []
    for f in sorted(glob.glob('videos_frames/*')):
        if num_of(f) != num:
            continue
        if path.isdir(f):
            out += sorted(g for g in glob.glob(f'{f}/*') if g.lower().endswith(exts))
        elif f.lower().endswith(exts):
            out.append(f)
    return out


def title_of(num):
    for suf, key in (('extract', 'title'), ('download', 'input_title')):
        for f in glob.glob(f'videos_data/*_{suf}.json'):
            if num_of(f) == num:
                try:
                    t = json.load(open(f, encoding='utf-8')).get(key)
                    if t:
                        return t
                except Exception:
                    pass
    return None    # sem título


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-') or 'video'


def esc(s):
    return html.escape(s, quote=True)


def url(f):
    return '/' + f.replace('\\', '/')


def read(f):
    return open(f, encoding='utf-8').read()


def write(f, s):
    os.makedirs(path.dirname(f) or '.', exist_ok=True)
    open(f, 'w', encoding='utf-8').write(s)


# ================ vídeos prontos (hls + poster) ================ #
ids = sorted({num_of(f) for f in glob.glob('videos_hls/*') if num_of(f) is not None}, reverse=True)

posts = []
for n in ids:
    posters = files_of('videos_posters', n, ('.jpg', '.jpeg', '.png', '.webp'))
    if not posters:
        print(f'PULOU {n:03d}: falta poster')
        continue
    trailers = files_of('videos_trailers', n, ('.mp4', '.webm'))
    name     = title_of(n)                      # None = sem nome -> /videos/NNN.html
    title    = name or f'Video {n:03d}'
    if not frames_of(n):
        print(f'AVISO {n:03d}: sem frames (previews vazios)')
    posts.append(dict(
        num=n, title=title, file=f'{n:03d}-{slugify(name)}.html' if name else f'{n:03d}.html',
        poster=posters[0], trailer=trailers[0] if trailers else None,
        frames=frames_of(n)))

if not posts:
    print('AVISO: nenhum vídeo pronto (videos_hls + videos_posters): buildando home vazia')


def card(p):
    src = f' src="{url(p["trailer"])}"' if p['trailer'] else ''
    return (f'<a href="/videos/{p["file"]}" title="{esc(p["title"])}">'
            f'<video poster="{url(p["poster"])}"{src} muted loop preload="none"></video></a>')


# ================ template -> página ================ #
def base(tpl, kind):
    """tema escolhido + nome do site (kind = 'home' | 'post')"""
    tpl = tpl.replace('/assets/themes/bellessa/style-home.css', f'/assets/themes/{THEME}/style-{kind}.css')
    tpl = tpl.replace('/assets/themes/bellessa/', f'/assets/themes/{THEME}/')
    tpl = tpl.replace('/assets/manifest.json',    f'/assets/themes/{THEME}/manifest.json')
    return tpl.replace('__SITE_NAME__', esc(NAME))


def set_inner(tpl, section_id, items):
    """troca o conteúdo do primeiro <div> dentro de <section id="...">"""
    pat = rf'(<section id="{section_id}"[^>]*>.*?<div>).*?(</div>)'
    return re.sub(pat, lambda m: m.group(1) + '\n' + '\n'.join(items) + '\n' + m.group(2), tpl, count=1, flags=re.S)


def rel(page, prefix):
    """/assets/x -> assets/x (index) ou ../assets/x (videos): abre também por file://"""
    return re.sub(r'(href|src|poster)="/(?!/)', rf'\1="{prefix}', page)


# ---- barra de páginas (page_counter = atual) ---- #
cur    = int(PAGE_COUNTER)
last   = cur    # página mais recente (maior numeração)
prev_n = cur + 1 if cur < last else 1
next_n = max(cur - 1, 1)
site   = lambda n: f'https://{THEME}-{n:03d}.pages.dev'
btn    = lambda n, txt: f'<a href="{site(n)}" ><button><h3>{txt}</h3></button></a>'
BAR    = '\n'.join([btn(prev_n, '◀')] + [btn(n, f'{n:02d}') for n in range(cur, 0, -1)] + [btn(next_n, '▶')])


def set_pages(page, carrousel=False):
    """barra #webpages (home e vídeos); carrousel=True também ajusta as setas laterais da home"""
    page = re.sub(r'(<div id="webpages"[^>]*>).*?(</div>)',
                  lambda m: m.group(1) + '\n' + BAR + '\n' + m.group(2), page, count=1, flags=re.S)
    if carrousel:
        for bid, n in (('prev', prev_n), ('next', next_n)):
            page = re.sub(rf'href="[^"]*"( ><button class="carrousel" id="{bid}")',
                          lambda m, n=n: f'href="{site(n)}"' + m.group(1), page)
    return page


# ---- index.html ----
home = base(read(f'{DESIGN}/template_home.html'), 'home')
home = set_inner(home, 'posts', [card(p) for p in posts])
home = set_pages(home, carrousel=True)

write('index.html', rel(home, ''))

# ---- videos/NNN-nome.html ----
tpl   = base(read(f'{DESIGN}/template_post.html'), 'post')
total = len(posts)

# limpa páginas antigas (inclusive os NNN-postname.html vazios)
for f in glob.glob('videos/*.html'):
    os.remove(f)

# limpa páginas antigas (inclusive os placeholders NNN-postname.html)

FILES = {p['num']: p['file'] for p in posts}    # número -> arquivo (o mesmo que glob 'videos/NNN*.html')

for i, p in enumerate(posts):
    # número +1 / -1: se existir, vai pra ele (NNN-nome.html ou NNN.html); se não, NNN.html -> 404 -> home
    n_new, n_old = p['num'] + 1, p['num'] - 1
    newer = '/videos/' + FILES.get(n_new, f'{n_new:03d}.html')
    older = '/videos/' + FILES.get(n_old, f'{n_old:03d}.html')

    page = tpl.replace('__POST_TITLE__', esc(p['title']))
    # ◀ (id=prev) -> mais novo | ▶ (id=next) -> mais antigo
    page = page.replace('../__POST_NEXT__', newer)
    page = page.replace('../__POST_PREV__', older)
    page = page.replace('poster="poster.jpg"', f'poster="{url(p["poster"])}"')
    page = set_inner(page, 'previews', [
        f'<a href="#movie" ><img src="{url(f)}" data-time="{k * FRAME_STEP}" loading="lazy" /></a>'
        for k, f in enumerate(p['frames'])])
    page = set_inner(page, 'posts', [card(q) for q in posts if q is not p][:RELATED])
    page = set_pages(page)
    write(f'videos/{p["file"]}', rel(page, '../'))

print(f'\nOK: tema {THEME} ({NAME}) -> index.html + {total} página(s) em videos/')

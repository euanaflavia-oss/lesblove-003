import os, re, json, glob, shutil, struct, threading, webbrowser
import subprocess as subp
from os import path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

FRAMES  = 'videos_frames'
POSTERS = 'videos_posters'
PORT    = 8765
os.makedirs(POSTERS, exist_ok=True)

HTML = """<!doctype html>
<meta charset="utf-8">
<title>Posters</title>
<style>
  body { margin: 0; background: #111; color: #eee; }
  header { position: sticky; top: 0; z-index: 1; display: flex; gap: 16px; align-items: center;
           padding: 12px 20px; background: #000; border-bottom: 1px solid #333; }
  header b { font-size: 18px; }
  header span { color: #999; }
  button { background: #222; color: #eee; border: 1px solid #444; padding: 8px 16px; cursor: pointer; }
  button:hover { background: #333; }
  .sp { flex: 1; }
  #grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; padding: 16px; }
  figure { margin: 0; position: relative; cursor: pointer; border: 3px solid transparent; }
  figure:hover { border-color: #c9a45c; }
  figure img { display: block; width: 100%; height: auto; background: #222; }
  figure.sel { border-color: #c9a45c; }
  figure .n { position: absolute; top: 6px; right: 6px; width: 28px; height: 28px; line-height: 28px;
              text-align: center; background: #c9a45c; color: #000; font-weight: bold; }
  #grid.portrait { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); align-items: start; }
  figcaption { position: absolute; left: 0; bottom: 0; padding: 2px 8px; background: #000a; font-size: 12px; }
  #end { padding: 80px; text-align: center; font-size: 20px; }
</style>
<header>
  <b id="t"></b><span id="p"></span><span class="sp"></span>
  <button id="ok" hidden>Confirmar (Enter)</button>
  <button id="reset" hidden>Limpar</button>
  <button id="skip">Pular (S)</button>
  <button id="quit">Sair</button>
</header>
<div id="grid"></div>
<div id="end" hidden>Pronto. Pode fechar esta aba.</div>
<script>
let vids = [], i = 0, sel = [];
const $ = s => document.querySelector(s);

async function load() {
  vids = await (await fetch('/api/state')).json();
  show();
}

function need() { return vids[i].orientation === 'portrait' ? Math.min(3, vids[i].frames.length) : 1; }

function show() {
  sel = [];
  if (i >= vids.length) {
    $('#grid').innerHTML = ''; $('header').hidden = true; $('#end').hidden = false;
    fetch('/api/done', { method: 'POST' });
    return;
  }
  const v = vids[i];
  $('#grid').className = v.orientation;
  $('#t').textContent = 'Vídeo ' + v.id + ' · ' + v.orientation + ' (' + v.width + 'x' + v.height + ')';
  $('#grid').innerHTML = v.frames.map(f =>
    `<figure data-f="${f.name}"><img loading="lazy" src="/frame/${v.id}/${f.name}"><figcaption>${f.t}s</figcaption></figure>`
  ).join('');
  document.querySelectorAll('figure').forEach(fig => fig.onclick = () => toggle(fig));
  refresh();
  window.scrollTo(0, 0);
}

function refresh() {
  const v = vids[i], n = need();
  $('#p').textContent = (i + 1) + ' / ' + vids.length + ' · escolha ' + n + (n > 1 ? ' frames, em ordem (esq → dir): ' + sel.length + '/' + n : ' frame');
  document.querySelectorAll('figure').forEach(fig => {
    const k = sel.indexOf(fig.dataset.f);
    fig.classList.toggle('sel', k >= 0);
    let b = fig.querySelector('.n');
    if (k >= 0 && n > 1) { if (!b) { b = document.createElement('div'); b.className = 'n'; fig.appendChild(b); } b.textContent = k + 1; }
    else if (b) b.remove();
  });
  $('#ok').hidden = $('#reset').hidden = n === 1;
  $('#ok').disabled = sel.length !== n;
}

function toggle(fig) {
  const f = fig.dataset.f, k = sel.indexOf(f);
  if (need() === 1) return pick([f]);
  if (k >= 0) sel.splice(k, 1); else if (sel.length < need()) sel.push(f);
  refresh();
}

async function pick(frames) {
  await fetch('/api/pick', { method: 'POST', body: JSON.stringify({ id: vids[i].id, frames }) });
  i++; show();
}

$('#ok').onclick = () => { if (sel.length === need()) pick(sel); };
$('#reset').onclick = () => { sel = []; refresh(); };
$('#skip').onclick = () => { i++; show(); };
$('#quit').onclick = async () => { await fetch('/api/done', { method: 'POST' }); document.body.innerHTML = '<div id="end">Encerrado.</div>'; };
document.onkeydown = e => {
  if (e.key.toLowerCase() === 's') $('#skip').click();
  if (e.key === 'Enter') $('#ok').click();
};
load();
</script>
"""


def frame_t(name):
    m = re.fullmatch(r'img_(\d+)\.jpg', name)
    return int(m.group(1)) if m else None


def jpeg_size(f):
    """(largura, altura) lendo o cabeçalho do JPEG"""
    with open(f, 'rb') as fh:
        fh.read(2)
        while True:
            b = fh.read(1)
            while b and b != b'\xff': b = fh.read(1)
            m = fh.read(1)
            while m == b'\xff': m = fh.read(1)
            if not m: return 0, 0
            if m[0] in (0xD8, 0x01) or 0xD0 <= m[0] <= 0xD7: continue
            n = struct.unpack('>H', fh.read(2))[0]
            if 0xC0 <= m[0] <= 0xCF and m[0] not in (0xC4, 0xC8, 0xCC):
                _, h, w = struct.unpack('>BHH', fh.read(5))
                return w, h
            fh.seek(n - 2, 1)


def pending():
    """vídeos com frames e sem poster"""
    out = []
    for d in sorted(glob.glob(f'{FRAMES}/[0-9]*')):
        vid = path.basename(d)
        if path.exists(f'{POSTERS}/{vid}.jpg'):
            continue
        frames = sorted(
            ({'name': n, 't': frame_t(n)} for n in os.listdir(d) if frame_t(n) is not None),
            key=lambda f: f['t'])
        if frames:
            w, h = jpeg_size(f'{d}/{frames[0]["name"]}')
            out.append({'id': vid, 'frames': frames, 'width': w, 'height': h,
                        'orientation': 'portrait' if w < h else 'landscape'})
    return out


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body=b'', ctype='text/plain'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            return self.send(200, HTML.encode('utf-8'), 'text/html; charset=utf-8')
        if self.path == '/api/state':
            return self.send(200, json.dumps(pending()).encode(), 'application/json')
        m = re.fullmatch(r'/frame/(\d+)/(img_\d+\.jpg)', self.path)
        if m:
            f = f'{FRAMES}/{m.group(1)}/{m.group(2)}'
            if path.exists(f):
                return self.send(200, open(f, 'rb').read(), 'image/jpeg')
        self.send(404)

    def do_POST(self):
        if self.path == '/api/pick':
            n = int(self.headers.get('Content-Length', 0))
            j = json.loads(self.rfile.read(n) or b'{}')
            vid, names = str(j.get('id', '')), [str(x) for x in j.get('frames', [])]
            srcs = [f'{FRAMES}/{vid}/{n}' for n in names]
            ok = re.fullmatch(r'\d+', vid) and names and all(frame_t(n) is not None and path.exists(f) for n, f in zip(names, srcs))
            if ok:
                w, h = jpeg_size(srcs[0])
                avail = len([x for x in os.listdir(f'{FRAMES}/{vid}') if frame_t(x) is not None])
                need = min(3, avail) if w < h else 1
                out = f'{POSTERS}/{vid}.jpg'
                if len(srcs) == need == 1:
                    shutil.copyfile(srcs[0], out)
                elif len(srcs) == need and need > 1:
                    ins = ' '.join(f'-i "{f}"' for f in srcs)
                    r = subp.run(f'ffmpeg -y -v error {ins} -filter_complex hstack=inputs={need} -q:v 1 "{out}"', shell=True)
                    if r.returncode or not path.exists(out):
                        return self.send(500)
                else:
                    return self.send(400)
                print('OK', out, f'(de {", ".join(names)})')
                return self.send(200, b'ok')
            return self.send(400)
        if self.path == '/api/done':
            self.send(200, b'ok')
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self.send(404)


todo = pending()
if not todo:
    print('Nada pendente (sem frames novos ou todos já têm poster).')
    raise SystemExit(0)

print(f'{len(todo)} vídeo(s) sem poster -> http://localhost:{PORT}')
srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
threading.Timer(0.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
try:
    srv.serve_forever()
except KeyboardInterrupt:
    pass
print('Fim.')

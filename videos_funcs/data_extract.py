import os, re, json, glob
import subprocess as subp
from os import path

FULL = 'videos_full'
DATA = 'videos_data'

KEYS = ['id', 'title', 'description', 'uploader', 'channel', 'upload_date',
        'view_count', 'like_count', 'tags', 'categories', 'extractor_key',
        'webpage_url', 'thumbnail']


def probe(mp4):
    out = subp.run(
        f'ffprobe "{mp4}" -v error -select_streams v:0 '
        f'-show_entries stream=width,height,r_frame_rate:format=duration,size -of json',
        shell=True, capture_output=True, text=True)
    try:
        j = json.loads(out.stdout)
        s, f = j['streams'][0], j['format']
        n, d = s['r_frame_rate'].split('/')
        return dict(width=int(s['width']), height=int(s['height']),
                    fps=round(int(n) / int(d), 2) if int(d) else None,
                    duration=int(float(f['duration'])), size=int(f['size']))
    except Exception:
        return {}


index = []
for f in sorted(glob.glob(f'{DATA}/[0-9]*_download.json')):
    m = re.fullmatch(r'(\d+)_download\.json', path.basename(f))
    if not m:
        continue
    vid = m.group(1)
    raw = json.load(open(f, encoding='utf-8'))

    d = {'id': vid, 'title': raw.get('input_title') or raw.get('title') or '', 'url': raw.get('input_url', '')}
    d['source'] = {k: raw.get(k) for k in KEYS if raw.get(k) not in (None, '', [])}

    mp4 = f'{FULL}/{vid}.mp4'
    d.update(probe(mp4) if path.exists(mp4) else
             {k: raw.get(k) for k in ('width', 'height', 'duration', 'fps')})
    d['orientation'] = 'portrait' if (d.get('width') or 0) < (d.get('height') or 0) else 'landscape'

    json.dump(d, open(f'{DATA}/{vid}_extract.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
    index.append(d)
    print('OK', vid, d['title'])

print(f'{len(index)} vídeos')

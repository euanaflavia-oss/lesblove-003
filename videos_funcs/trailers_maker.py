import os, glob
import subprocess as subp
from os import path

CUT      = 'videos_cut'
TRAILERS = 'videos_trailers'
PARTS    = 6
TOTAL    = 12      # duração aproximada do trailer (s)
XFADE    = 0.20
WIDTH    = 480
os.makedirs(TRAILERS, exist_ok=True)


def duration(mp4):
    p = subp.run(f'ffprobe "{mp4}" -v error -show_entries format=duration -of csv=p=0',
                 shell=True, capture_output=True, text=True)
    try:    return float(p.stdout.strip())
    except: return 0


for mp4 in sorted(glob.glob(f'{CUT}/[0-9]*.mp4')):
    vid = path.splitext(path.basename(mp4))[0]
    out = f'{TRAILERS}/{vid}.mp4'
    if path.exists(out) and path.getsize(out) > 0:
        print('PULOU', vid); continue

    dur = duration(mp4)
    if dur <= 0:
        print('ERRO', vid); continue

    step = dur / PARTS
    clip = min(TOTAL / PARTS, step)

    v_chains, prev = [], 'nv0'
    for i in range(1, PARTS):
        cur = f'v{i}'
        v_chains.append(f'[{prev}][nv{i}]xfade=transition=fade:duration={XFADE}:offset={(clip - XFADE) * i}[{cur}]')
        prev = cur

    norm = ';'.join(f'[{i}:v]setpts=PTS-STARTPTS[nv{i}]' for i in range(PARTS))
    fc   = norm + ';' + ';'.join(v_chains) + f';[{prev}]scale={WIDTH}:-2[v]'
    inp  = ' '.join(f'-ss {step * i} -t {clip} -i "{mp4}"' for i in range(PARTS))

    subp.run(f'ffmpeg -y -v error {inp} -filter_complex "{fc}" -map "[v]" '
             f'-c:v libx264 -crf 23 -preset fast "{out}"', shell=True)

    if path.exists(out) and path.getsize(out) > 0:
        print('OK', out, f'({path.getsize(out) / 1024**2:.1f} MB)')
    else:
        print('ERRO', vid)

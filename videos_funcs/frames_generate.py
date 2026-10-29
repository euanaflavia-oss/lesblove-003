import os, sys, time, glob
import subprocess as subp
from os import path

CUT    = 'videos_cut'
FRAMES = 'videos_frames'
DEFAULT = 30
TIMEOUT = 10


def ask(prompt, timeout, default):
    print(f'{prompt} [{default}] ({timeout}s): ', end='', flush=True)
    buf = ''
    if os.name == 'nt':
        import msvcrt
        end = time.time() + timeout
        while time.time() < end:
            if msvcrt.kbhit():
                c = msvcrt.getwche()
                if c in '\r\n': print(); return buf.strip() or default
                if c == '\b':   buf = buf[:-1]
                else:           buf += c
            time.sleep(0.02)
    else:
        import select
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.readline().strip() or default
    print()
    return default


while True:
    try:    STEP = int(float(ask('STEP (s)', TIMEOUT, DEFAULT))); assert STEP > 0; break
    except: print('Valor inválido')

for mp4 in sorted(glob.glob(f'{CUT}/[0-9]*.mp4')):
    vid = path.splitext(path.basename(mp4))[0]
    out = f'{FRAMES}/{vid}'
    os.makedirs(out, exist_ok=True)

    p = subp.run(f'ffprobe "{mp4}" -v error -show_entries format=duration -of csv=p=0',
                 shell=True, capture_output=True, text=True)
    try:    dur = int(float(p.stdout.strip()))
    except: print('ERRO', vid); continue

    for x in range(0, dur, STEP):
        img = f'{out}/img_{x}.jpg'
        if path.exists(img): continue
        subp.run(f'ffmpeg -y -v error -ss {x} -i "{mp4}" -vframes 1 -q:v 2 "{img}"', shell=True)

    print('OK', vid, f'{len(os.listdir(out))} frames')

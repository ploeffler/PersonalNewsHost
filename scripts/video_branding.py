"""Shared transparent station logo and the red short-update label."""
from pathlib import Path
import re

DEFAULT_LOGO = 'assets/logo-video.png'


def apply_branding(args, filters, current, root, config, breaking=False):
    logo_width, logo_height = 90, 90
    relative = str(config.get('station_logo', DEFAULT_LOGO)).strip()
    if relative:
        if not re.fullmatch(r'assets/[A-Za-z0-9_./-]+', relative) or '..' in relative:
            raise ValueError('Invalid station logo path')
        # Old form exports used the opaque site logo as the video default.
        if relative == 'assets/logo.png' and (Path(root) / DEFAULT_LOGO).is_file():
            relative = DEFAULT_LOGO
        logo = Path(root) / relative
        if logo.is_file():
            from PIL import Image
            with Image.open(logo) as image:
                width, height = image.size
            scale = min(160 / width, 90 / height)
            logo_width, logo_height = round(width * scale), round(height * scale)
            index = args.count('-i')
            args += ['-loop', '1', '-framerate', '5', '-i', str(logo)]
            filters.append(f'[{index}:v]scale=160:90:force_original_aspect_ratio=decrease,format=rgba,setsar=1[stationlogo]')
            filters.append(f'[{current}][stationlogo]overlay=x=W-w-30:y=30:eof_action=repeat:shortest=0[withstationlogo]')
            current = 'withstationlogo'
        else:
            print('WARNING: station logo missing; rendering without station logo')
    if breaking:
        filters.append(f"[{current}]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                       f"text='AKTUELL':fontcolor=0xff3038:fontsize=28:x=w-tw-{logo_width + 46}:y={30 + (logo_height - 28) // 2}[withaktuellticker]")
        current = 'withaktuellticker'
    return current

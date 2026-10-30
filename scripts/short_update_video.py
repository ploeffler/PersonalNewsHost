"""Render a narrated short-update card with transparent station branding."""
import datetime as dt
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap

try:
    from scripts.video_branding import apply_branding
except ModuleNotFoundError:
    from video_branding import apply_branding


def render_short_update(update, audio, output, root, config):
    audio, output = Path(audio), Path(output)
    if not audio.is_file():
        raise FileNotFoundError('Short-update audio missing')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        headline = textwrap.wrap(update['title'], width=43)[:3]
        body = update.get('text', '')
        if body.startswith(update['title']):
            body = body[len(update['title']):].lstrip('.\n ')
        lines = textwrap.wrap(' '.join(body.split()), width=80)
        if len(lines) > 8:
            lines = lines[:8]; lines[-1] = lines[-1].rstrip('., ') + ' …'
        stamp = dt.datetime.fromtimestamp(update['created_at'], dt.timezone.utc).strftime('%d.%m.%Y · %H:%M UTC')
        captions = [('headline', '\n'.join(headline), 42, 72, 160, 'white'),
                    ('body', '\n'.join(lines), 27, 72, 330, '0xd6e5f4'),
                    ('source', 'Quelle: ' + str(update.get('source', ''))[:100], 20, 72, 650, '0x9fb7ce'),
                    ('time', stamp, 20, 72, 60, '0x9fb7ce')]
        args = ['ffmpeg', '-y', '-v', 'error', '-filter_complex_threads', '1',
                '-f', 'lavfi', '-i', 'color=c=0x13243a:s=1280x720:r=5', '-i', str(audio)]
        filters = []
        current = '0:v'
        for name, text, size, x, y, color in captions:
            for row, line in enumerate(text.splitlines()):
                label = name + str(row)
                file = tmp / (label + '.txt');file.write_text(line, encoding='utf-8')
                safe = str(file).replace(':', '\\:')
                filters.append(f"[{current}]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                               f"textfile='{safe}':expansion=none:fontsize={size}:fontcolor={color}:"
                               f"x={x}:y={y + row * (size + 10)}[{label}]")
                current = label
        current = apply_branding(args, filters, current, root, config, breaking=True)
        temporary = output.with_suffix('.rendering.mp4')
        try:
            subprocess.run(args + ['-filter_complex', ';'.join(filters), '-map', f'[{current}]', '-map', '1:a',
                                   '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
                                   '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', '-shortest',
                                   '-movflags', '+faststart', str(temporary)], check=True, timeout=180,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
    return output

"""Reusable news cards, rendered locally and timed to measured narration."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def fit_lines(draw, text, font, width, limit):
    """Pixel-based wrapping, including long words and an ellipsis on overflow."""
    lines, line = [], ''
    for word in str(text).split():
        candidate = (line + ' ' + word).strip()
        if draw.textlength(candidate, font=font) <= width:
            line = candidate
            continue
        if line:
            lines.append(line)
            line = ''
        for char in word:
            if line and draw.textlength(line + char, font=font) > width:
                lines.append(line)
                line = ''
            line += char
    if line:
        lines.append(line)
    if len(lines) > limit:
        lines = lines[:limit]
        while lines[-1] and draw.textlength(lines[-1] + '…', font=font) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + '…'
    return lines


def add_news_card(args, filters, current, root, tmp, index, title, source,
                  section, start, end, has_media, font):
    if end <= start:
        return current
    template = Path(root) / 'assets/motion/news-card.json'
    if not template.is_file():
        template = Path(__file__).resolve().parents[1] / 'assets/motion/news-card.json'
    style = json.loads(template.read_text())
    width, padding = style['width'], style['padding']
    height, y = (200, 425) if has_media else (325, 195)
    image = Image.new('RGBA', (width, height), style['background'])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 6, height), fill=style['accent'])
    label_font = ImageFont.truetype(font, 18)
    title_font = ImageFont.truetype(font, 28 if has_media else 34)
    available = width - 2 * padding
    label = fit_lines(draw, section.upper(), label_font, available, 1)
    draw.text((padding, 12), '\n'.join(label), font=label_font, fill=style['accent'])
    lines = fit_lines(draw, title, title_font, available, 3)
    draw.multiline_text((padding, 43), '\n'.join(lines), font=title_font,
                        fill=style['text'], spacing=8)
    credit = fit_lines(draw, 'Quelle: ' + source, label_font, available, 1)
    draw.text((padding, height - 30), '\n'.join(credit), font=label_font, fill=style['accent'])
    path = Path(tmp) / f'motion_card_{index}.png'
    image.save(path)
    input_index = args.count('-i')
    args += ['-loop', '1', '-framerate', '20', '-i', str(path)]
    duration = end - start
    fade = min(style['fade_seconds'], duration / 3)
    card, output = f'motioncard{index}', f'motionstory{index}'
    filters.append(
        f'[{input_index}:v]format=rgba,trim=duration={duration:.6f},'
        f'fade=t=in:st=0:d={fade:.6f}:alpha=1,'
        f'fade=t=out:st={duration-fade:.6f}:d={fade:.6f}:alpha=1,'
        f'setpts=PTS-STARTPTS+{start:.6f}/TB[{card}]')
    filters.append(
        f"[{current}][{card}]overlay=x=55:y={y}:eof_action=pass:"
        f"enable='gte(t,{start:.6f})*lt(t,{end:.6f})'[{output}]")
    return output

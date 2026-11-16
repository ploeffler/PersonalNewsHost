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


def load_style(root):
    template = Path(root) / 'assets/motion/news-card.json'
    if not template.is_file():
        template = Path(__file__).resolve().parents[1] / 'assets/motion/news-card.json'
    return json.loads(template.read_text())


def add_news_card(args, filters, current, root, tmp, index, title, source,
                  section, start, end, has_media, font):
    if end <= start:
        return current
    style = load_style(root)
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


def section_transition_end(section_ids, index, start, end, enabled, seconds):
    """A bumper shares the current story's time; it never delays narration."""
    if (not enabled or end <= start or
            (index > 0 and section_ids[index] == section_ids[index - 1])):
        return start
    return min(end, start + max(0, seconds))


def add_section_transition(args, filters, current, root, tmp, index,
                           section, start, end, font):
    if end <= start:
        return current
    style = load_style(root)
    width, padding = style['width'], style['padding']
    image = Image.new('RGBA', (width, 100), style['background'])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 6, 99), fill=style['accent'])
    small = ImageFont.truetype(font, 16)
    large = ImageFont.truetype(font, 32)
    draw.text((padding, 12), 'RUBRIK', font=small, fill=style['accent'])
    title = fit_lines(draw, section, large, width - padding * 2, 1)
    draw.text((padding, 38), '\n'.join(title), font=large, fill=style['text'])
    path = Path(tmp) / f'section_transition_{index}.png'
    image.save(path)
    input_index = args.count('-i')
    args += ['-loop', '1', '-framerate', '20', '-i', str(path)]
    duration = end - start
    fade = min(style['fade_seconds'], duration / 3)
    card, output = f'sectioncard{index}', f'sectionstory{index}'
    filters.append(
        f'[{input_index}:v]format=rgba,trim=duration={duration:.6f},'
        f'fade=t=in:st=0:d={fade:.6f}:alpha=1,'
        f'fade=t=out:st={duration-fade:.6f}:d={fade:.6f}:alpha=1,'
        f'setpts=PTS-STARTPTS+{start:.6f}/TB[{card}]')
    # Cubic ease-out: starts outside the canvas and settles at the safe margin.
    progress = f'min(1,max(0,(t-{start:.6f})/{fade:.6f}))'
    x = f'55-({width}+55)*pow(1-{progress},3)'
    filters.append(
        f"[{current}][{card}]overlay=x='{x}':y=60:eof_action=pass:"
        f"enable='gte(t,{start:.6f})*lt(t,{end:.6f})'[{output}]")
    return output

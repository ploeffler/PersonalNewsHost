"""Subtitle timing from the synthesized speech itself (T063).

No speech recognition and no extra models: the speech WAV of each segment is
scanned for pauses. Piper inserts a fixed pause after every sentence
(``--sentence_silence``) and eSpeak pauses at sentence ends, so sentence
boundaries can be located in the audio. Cues never span two sentences; inside
a sentence, cue boundaries are estimated by character share and snapped to a
nearby pause (for example at a comma) when one exists.
"""
import re
import sys
import textwrap
import wave
from array import array

FRAME_SECONDS = 0.01
MIN_SENTENCE_GAP = 0.15
MIN_INNER_GAP = 0.08
SNAP_SECONDS = 0.6
_ABBREVIATION = re.compile(r'\d+\.|[A-Za-zÄÖÜäöü]\.|(?:bzw|ca|vgl|usw|etc|inkl|exkl|evtl|ggf|bspw|sog|u\.a|z\.B|Nr|Dr|Prof|St|Mio|Mrd|Abs|Art|Jh|Jän|Feb|Okt|Nov|Dez|Std|Min|Mag|Ing)\.', re.I)
_SENTENCE_END = re.compile(r'(?<=[.!?…])["»“”\')]*\s+(?=\S)')


def split_sentences(text):
    """Sentence units as spoken; abbreviations like 'z. B.' or '3. November' stay together."""
    text = ' '.join(str(text).split())
    if not text:
        return []
    parts, start = [], 0
    for match in _SENTENCE_END.finditer(text):
        before = text[start:match.start()]
        after = text[match.end():match.end() + 1]
        last = before.rsplit(' ', 1)[-1]
        # Ordinals, single-letter and lower-case abbreviations do not end a sentence.
        if _ABBREVIATION.fullmatch(last) or (after and after.islower()):
            continue
        parts.append(text[start:match.start()].strip())
        start = match.end()
    parts.append(text[start:].strip())
    return [p for p in parts if p]


def frame_levels(path):
    """RMS level per 10 ms frame for 8/16-bit PCM WAV files."""
    with wave.open(str(path), 'rb') as source:
        rate, width, channels = source.getframerate(), source.getsampwidth(), source.getnchannels()
        data = source.readframes(source.getnframes())
    if width == 2:
        samples = array('h')
        samples.frombytes(data)
        if sys.byteorder == 'big':  # WAV PCM is little-endian
            samples.byteswap()
        values = samples[::channels]
    elif width == 1:
        values = [b - 128 for b in data[::channels]]
    else:
        raise ValueError('Unsupported WAV sample width')
    size = max(1, round(rate * FRAME_SECONDS))
    levels = []
    for offset in range(0, len(values), size):
        frame = values[offset:offset + size]
        levels.append((sum(v * v for v in frame) / len(frame)) ** 0.5 if len(frame) else 0.0)
    return levels, len(values) / rate


def speech_map(path):
    """Speech start/end and pauses ``(start, end)`` in seconds within one WAV file."""
    levels, duration = frame_levels(path)
    peak = max(levels, default=0)
    if peak <= 0:
        return 0.0, 0.0, []
    threshold = max(peak * 0.03, 30.0)
    voiced = [level > threshold for level in levels]
    if not any(voiced):
        return 0.0, 0.0, []
    first = voiced.index(True)
    last = len(voiced) - 1 - voiced[::-1].index(True)
    gaps, run = [], None
    for index in range(first, last + 1):
        if not voiced[index]:
            run = index if run is None else run
        elif run is not None:
            gaps.append((run * FRAME_SECONDS, index * FRAME_SECONDS))
            run = None
    return first * FRAME_SECONDS, min(duration, (last + 1) * FRAME_SECONDS), gaps


def _choose_breaks(expected, gaps, span):
    """Pick one gap per expected break, in order, close to the estimate and preferably long."""
    k, n = len(expected), len(gaps)
    if k == 0:
        return []
    if n < k:
        return None
    inf = float('inf')

    def cost(i, j):
        start, end = gaps[j]
        # Distance to the estimate in shares of the segment, minus pause length in seconds:
        # a pause 0.15 s longer outweighs an estimate that is 15 % of the segment off.
        return abs((start + end) / 2 - expected[i]) / span - (end - start)
    best = [[inf] * n for _ in range(k)]
    back = [[-1] * n for _ in range(k)]
    for j in range(n):
        best[0][j] = cost(0, j)
    for i in range(1, k):
        running, arg = inf, -1
        for j in range(n):
            if j - 1 >= 0 and best[i - 1][j - 1] < running:
                running, arg = best[i - 1][j - 1], j - 1
            if arg >= 0:
                best[i][j] = running + cost(i, j)
                back[i][j] = arg
    j = min(range(n), key=lambda x: best[k - 1][x])
    if best[k - 1][j] == inf:
        return None
    chosen = [j]
    for i in range(k - 1, 0, -1):
        j = back[i][j]
        chosen.append(j)
    return [gaps[x] for x in reversed(chosen)]


def sentence_times(sentences, path):
    """``(intervals, pauses)``: spoken interval of every sentence relative to the WAV start."""
    start, end, gaps = speech_map(path)
    if not sentences or end <= start:
        return [], gaps
    weights = [max(1, len(s)) for s in sentences]
    total, span = sum(weights), end - start
    expected, acc = [], 0
    for weight in weights[:-1]:
        acc += weight
        expected.append(start + span * acc / total)
    breaks = _choose_breaks(expected, [g for g in gaps if g[1] - g[0] >= MIN_SENTENCE_GAP], span)
    if breaks is None:  # not enough pauses: proportional fallback
        breaks = [(t, t) for t in expected]
    edges = [start] + [b for gap in breaks for b in gap] + [end]
    return [(edges[2 * i], edges[2 * i + 1]) for i in range(len(sentences))], gaps


def cue_chunks(sentence, width=42, lines=2):
    rows = textwrap.wrap(sentence, width=width, break_long_words=False, break_on_hyphens=False)
    return ['\n'.join(rows[i:i + lines]) for i in range(0, len(rows), lines)]


def aligned_cues(text, path, offset=0.0, limit=None):
    """Cues ``(start_ms, end_ms, text)`` for one spoken segment, aligned to its audio."""
    sentences = split_sentences(text)
    times, gaps = sentence_times(sentences, path)
    if not times:
        return []
    inner = [g for g in gaps if g[1] - g[0] >= MIN_INNER_GAP]
    cues = []
    for sentence, (s_start, s_end) in zip(sentences, times):
        chunks = cue_chunks(sentence)
        total = sum(len(c) for c in chunks)
        bounds, consumed = [s_start], 0
        for chunk in chunks[:-1]:
            consumed += len(chunk)
            estimate = s_start + (s_end - s_start) * consumed / total
            near = [g for g in inner if s_start < g[0] and g[1] < s_end and abs((g[0] + g[1]) / 2 - estimate) <= SNAP_SECONDS]
            if near:
                gap = min(near, key=lambda g: abs((g[0] + g[1]) / 2 - estimate))
                estimate = (gap[0] + gap[1]) / 2
            bounds.append(max(bounds[-1], estimate))
        bounds.append(s_end)
        for chunk, a, b in zip(chunks, bounds, bounds[1:]):
            start_ms, end_ms = round((offset + a) * 1000), round((offset + b) * 1000)
            if limit is not None:
                end_ms = min(end_ms, round(limit * 1000))
            if end_ms > start_ms:
                cues.append((start_ms, end_ms, chunk))
    return cues

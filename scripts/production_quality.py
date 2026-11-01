"""Validate an isolated edition before replacing the last successful output."""
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


class QualityError(RuntimeError):
    pass


def check_edition(folder, config):
    folder = Path(folder)
    try:
        groups = json.loads((folder / 'story-groups.json').read_text())
        timeline = json.loads((folder / 'timeline.json').read_text())
        settings = config.get('quality', {})
        minimum = settings.get('min_items', 1)
        if type(minimum) is not int or minimum < 1:
            raise QualityError('Invalid minimum story count')
        if not isinstance(groups, list) or len(groups) < minimum:
            raise QualityError('Too few stories')
        for group in groups:
            if not group.get('headline', '').strip() or not group.get('sources'):
                raise QualityError('Empty story or missing sources')
            if not all(isinstance(source.get('url'), str) and source['url'].startswith(('https://', 'http://'))
                       for source in group['sources']):
                raise QualityError('Missing source URL')
        segments = timeline['segments']
        if not segments or sum(s.get('type') == 'story' for s in segments) != len(groups):
            raise QualityError('Story timeline mismatch')
        previous = 0.0
        for segment in segments:
            start, end = float(segment['start']), float(segment['end'])
            if not all(math.isfinite(v) for v in (start, end)) or end <= start or abs(start - previous) > 0.01:
                raise QualityError('Empty or discontinuous section')
            previous = end
        expected = float(timeline['duration'])
        if not math.isfinite(expected) or expected <= 0 or abs(expected - previous) > 0.01:
            raise QualityError('Invalid timeline duration')
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                                 '-of', 'json', str(folder / 'latest.mp4')],
                                capture_output=True, text=True, check=True, timeout=30)
        media = json.loads(result.stdout)
        streams = media['streams']
        if not any(s.get('codec_type') == 'video' for s in streams):
            raise QualityError('Missing video stream')
        if not any(s.get('codec_type') == 'audio' for s in streams):
            raise QualityError('Missing audio stream')
        duration = float(media['format']['duration'])
        low = float(settings.get('min_duration_seconds', 0.1))
        high = float(settings.get('max_duration_seconds', config.get('target_duration_seconds', expected + 1)))
        if not all(math.isfinite(v) for v in (duration, low, high)) or low <= 0 or high < low:
            raise QualityError('Invalid duration bounds')
        if not low <= duration <= high or abs(duration - expected) > max(1, expected * 0.02):
            raise QualityError('Video duration outside target range')
        if not (folder / 'transcript.txt').read_text().strip():
            raise QualityError('Empty transcript')
        return {'status': 'passed', 'stories': len(groups), 'duration_seconds': duration}
    except QualityError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError):
        raise QualityError('Edition metadata or media could not be validated') from None


@contextmanager
def staged_edition(destination):
    """Keep all old edition files until render and validation succeed.

    A failed editorial attempt may refresh only its diagnostic report. Swapping
    directories assumes one producer; multi-process locking belongs to T182.
    """
    destination = Path(destination)
    if destination.is_symlink() or (destination.exists() and any(p.is_symlink() for p in destination.rglob('*'))):
        raise QualityError('Output directory must not be a symlink')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.pnh-edition-', dir=destination.parent))
    candidate, backup = staging / 'candidate', staging / 'previous'
    try:
        if destination.exists():
            shutil.copytree(destination, candidate, symlinks=True)
        else:
            candidate.mkdir()
        # Do not mistake the old edition's generated contract files for new ones.
        for name in ('latest.mp4', 'timeline.json', 'story-groups.json', 'transcript.txt', 'editorial-report.json'):
            (candidate / name).unlink(missing_ok=True)
        yield candidate
        existed = destination.exists()
        if existed:
            os.replace(destination, backup)
        try:
            os.replace(candidate, destination)
        except OSError:
            if existed:
                os.replace(backup, destination)
            raise
    except Exception:
        report = candidate / 'editorial-report.json'
        if report.is_file() and not report.is_symlink():
            destination.mkdir(exist_ok=True)
            shutil.copyfile(report, destination / 'editorial-report.json')
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)

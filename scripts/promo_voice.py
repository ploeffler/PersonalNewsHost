"""Local production voice profile shared with main; never uploads text."""
import math
from pathlib import Path
import shutil
import subprocess
import wave

PRODUCTION_VOICE = {
    'tts_engine': 'piper', 'voice_model': 'de_DE-thorsten-high',
    'piper_length_scale': 1.06, 'sentence_silence': 0.38,
    'voice_pitch_semitones': -1.5, 'voice': 'de',
    'source': 'main:config.json + scripts/generate.py',
}


def synthesize(text, path, root, *, profile=None, fallback=None):
    settings = dict(PRODUCTION_VOICE, **(profile or {}))
    engine = settings['tts_engine']
    if engine not in {'piper', 'espeak'}:
        raise ValueError('Unsupported speech engine')
    length = float(settings['piper_length_scale'])
    silence = float(settings['sentence_silence'])
    pitch = float(settings['voice_pitch_semitones'])
    if not all(math.isfinite(v) for v in (length, silence, pitch)) or not (.5 <= length <= 2 and 0 <= silence <= 2 and -6 <= pitch <= 6):
        raise ValueError('Invalid voice settings')
    model_name = settings['voice_model']
    if model_name != 'de_DE-thorsten-high':
        raise ValueError('Install and explicitly support the selected local voice model')
    model = Path(root) / 'models' / (model_name + '.onnx')
    binary = shutil.which('piper')
    local_binary = Path(root) / '.venv-promo/bin/piper'
    if not binary and local_binary.is_file():
        binary = str(local_binary)
    path = Path(path)
    actual = engine
    if engine == 'piper':
        if not binary or not model.is_file() or not model.with_suffix('.onnx.json').is_file():
            raise RuntimeError('Production voice requires Piper and models/de_DE-thorsten-high.onnx plus .onnx.json; select espeak explicitly for fallback')
        subprocess.run([binary, '--model', str(model), '--length-scale', str(length),
                        '--sentence-silence', str(silence), '--output-file', str(path)],
                       input=text, text=True, check=True, timeout=180, stdout=subprocess.DEVNULL)
    else:
        if fallback is None:
            raise RuntimeError('No local eSpeak adapter supplied')
        fallback(text, path)
    with wave.open(str(path), 'rb') as audio:
        rate = audio.getframerate()
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or not audio.getnframes():
            raise ValueError('Speech engine must produce nonempty mono PCM16 WAV')
    if abs(pitch) >= .01:
        target = path.with_name(path.stem + '-pitch.wav')
        factor = 2 ** (pitch / 12)
        try:
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(path), '-af',
                            f'asetrate={rate}*{factor:.8f},aresample={rate},atempo={1/factor:.8f}',
                            '-ar', str(rate), '-c:a', 'pcm_s16le', str(target)], check=True, timeout=180)
            target.replace(path)
        finally:
            target.unlink(missing_ok=True)
    return dict(settings, actual_engine=actual)

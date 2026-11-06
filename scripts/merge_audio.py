"""Local chapter assembly with a configurable additional boundary pause."""
import array
import json
import math
from pathlib import Path
import subprocess
import tempfile
import uuid
import wave
from core import read, save, digest, tool, audio

def merge_audio(project, manifest):
    project = Path(project).resolve()
    config = read(Path(__file__).resolve().parents[1] / 'configs/defaults.json')
    pause = config['chapter_pause_seconds']
    if isinstance(pause, bool) or not isinstance(pause, (int, float)) or not math.isfinite(pause) or pause < 0:
        raise ValueError('chapter_pause_seconds must be a finite nonnegative number')
    chapters = read(manifest)['chapters']
    if not chapters:
        raise ValueError('Empty chapter manifest')
    rate = 24000
    sources = []
    out = project / 'audio' / ('merged_' + uuid.uuid4().hex + '.mp3')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'merged.wav'
        with wave.open(str(wav), 'wb') as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(rate)
            for index, chapter in enumerate(chapters):
                source = Path(chapter['file'])
                if not source.is_absolute():
                    source = project / source
                if index:
                    writer.writeframes(bytes(round(pause * rate) * 2))
                pcm = subprocess.run([tool('ffmpeg'), '-v', 'error', '-xerror', '-i', str(source),
                    '-f', 's16le', '-ac', '1', '-ar', str(rate), '-'], capture_output=True, check=True).stdout
                if not pcm:
                    raise ValueError('Empty decoded chapter')
                writer.writeframes(pcm)
                sources.append(dict(file=str(source), sha256=digest(source)))
        subprocess.run([tool('ffmpeg'), '-v', 'error', '-n', '-i', str(wav),
                        '-c:a', 'libmp3lame', '-b:a', '128k', str(out)], check=True)
    result = audio(project, out)
    save(out.with_suffix('.json'), dict(chapters=sources, chapter_pause_seconds=pause,
         inserted_pause_count=len(chapters)-1, final=result))
    return result

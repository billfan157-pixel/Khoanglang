"""Measure source PCM and export reproducible spectrum evidence (not listening QA)."""

import hashlib
import csv
import json
from pathlib import Path
import wave

import numpy as np

root = Path(__file__).resolve().parents[1]
out = root / 'docs/agent/EVIDENCE'
out.mkdir(parents=True, exist_ok=True)
report = {'method': '16-bit PCM; unweighted sample RMS/peak in dBFS (not LUFS); '
          'Welch power with 4096-sample Hann windows, 50% overlap; channel power averaged',
          'scope': 'Source files only, not the Unreal mix or perceived audio quality',
          'files': []}
spectra = {}

def db(value):
    return round(20 * np.log10(max(float(value), 1e-12)), 3)

for path in sorted((root / 'Content/KhoangLang/SourceAudio').glob('*.wav')):
    with wave.open(str(path), 'rb') as source:
        if source.getsampwidth() != 2:
            raise ValueError('Expected 16-bit PCM: ' + path.name)
        rate, channels = source.getframerate(), source.getnchannels()
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype='<i2')
    samples = pcm.astype(float).reshape(-1, channels) / 32768.0
    n = min(4096, len(samples))
    hop = max(1, n // 2)
    window = np.hanning(n)[:, None]
    power = np.zeros(n // 2 + 1)
    count = 0
    for start in range(0, len(samples) - n + 1, hop):
        fft = np.fft.rfft(samples[start:start+n] * window, axis=0)
        power += np.mean(np.abs(fft) ** 2, axis=1)
        count += 1
    power /= max(1, count)
    hz = np.fft.rfftfreq(n, 1 / rate)
    total = max(float(power.sum()), 1e-24)
    bands = {}
    for lo, hi in ((0, 200), (200, 1000), (1000, 4000), (4000, rate / 2 + 1)):
        bands['%d-%dHz' % (lo, hi)] = round(float(power[(hz >= lo) & (hz < hi)].sum()) / total, 6)
    report['files'].append({
        'file': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'duration_s': round(len(samples) / rate, 6), 'sample_rate': rate, 'channels': channels,
        'sample_peak_dbfs': db(np.max(np.abs(samples))),
        'sample_rms_dbfs': db(np.sqrt(np.mean(samples ** 2))),
        'clipped_samples': int(np.count_nonzero((pcm == 32767) | (pcm == -32768))),
        'dc_offset': round(float(np.mean(samples)), 8),
        'spectral_centroid_hz': round(float(np.sum(hz * power) / total), 2),
        'power_fraction_by_band': bands,
    })
    spectra[path.stem] = (hz, power)

(out / 'G1_source_audio_measurements.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
with (out / 'G1_T2_source_spectrum.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(['frequency_hz', 'masked_power_relative_peak_db', 'clear_power_relative_peak_db'])
    hz, masked = spectra['S_KL_T2_Masked']
    clear_hz, clear = spectra['S_KL_T2_Clear']
    if not np.array_equal(hz, clear_hz):
        raise ValueError('T2 spectra have different frequency axes')
    masked = 10 * np.log10(np.maximum(masked / max(float(masked.max()), 1e-24), 1e-12))
    clear = 10 * np.log10(np.maximum(clear / max(float(clear.max()), 1e-24), 1e-12))
    writer.writerows(zip(hz, masked, clear))
print(json.dumps({'files': len(report['files']), 'report': 'G1_source_audio_measurements.json'}))

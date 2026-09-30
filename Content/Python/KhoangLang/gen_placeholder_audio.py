"""
Khoang Lang 02:17 - Milestone 1 placeholder audio generator.

Synthesises ORIGINAL, procedurally generated placeholder audio (no third-party
assets, no recorded speech). Voices are formant-synthesised "voice-like" tones
that carry the cadence of speech but are NOT real words. All spoken content is
delivered to the player as on-screen subtitles / journal text (accessibility
requirement H).

Canon notes (V3) honoured by this file:
  * T2 "ban phat" was CHE (buried under noise), never erased: 65 answers mixed
    into a noise layer, recoverable only by light filtering.
  * The 43-second nightly broadcast, operator line at 02:16:34.
  * Two very quiet small voices (chi Tuyet + be Bong) that almost no one hears.
  * Nhi's answer is cut off mid-sentence: "Con! Con em o..."
  * Roll call (Nguoi Cho Diem Danh) is anchored to the school speaker line.
"""

import math
import os
import random
import struct
import wave

SR = 32000
OUT_DIR = os.environ.get("KL_AUDIO_OUT", "")


# --------------------------------------------------------------------------- #
# small DSP toolbox
# --------------------------------------------------------------------------- #

def buf(n):
    return [0.0] * n


def norm(x, peak=0.92):
    m = 0.0
    for v in x:
        a = abs(v)
        if a > m:
            m = a
    if m < 1e-9:
        return x
    k = peak / m
    return [v * k for v in x]


def fade_edges(x, ms=12):
    n = int(SR * ms / 1000.0)
    n = min(n, len(x) // 2)
    for i in range(n):
        g = i / float(n)
        x[i] *= g
        x[-1 - i] *= g
    return x


def loopify(x, ms=250):
    """Cross-fade the tail into the head so the buffer loops seamlessly."""
    n = int(SR * ms / 1000.0)
    n = min(n, len(x) // 3)
    out = x[:len(x) - n]
    for i in range(n):
        g = i / float(n)
        out[i] = out[i] * g + x[len(x) - n + i] * (1.0 - g)
    return fade_edges(out, 8)


def resonator(src, f0, bw, sr=SR, gain=1.0):
    """Two-pole resonator - cheap formant filter."""
    r = math.exp(-math.pi * bw / sr)
    theta = 2.0 * math.pi * f0 / sr
    a1 = 2.0 * r * math.cos(theta)
    a2 = -r * r
    k = (1.0 - r) * math.sqrt(max(1e-6, 1.0 - 2.0 * r * math.cos(2.0 * theta) + r * r))
    y = buf(len(src))
    y1 = 0.0
    y2 = 0.0
    for i, x in enumerate(src):
        v = gain * k * x + a1 * y1 + a2 * y2
        y[i] = v
        y2 = y1
        y1 = v
    return y


def lowpass(src, cutoff, sr=SR):
    """2x cascaded one-pole low-pass (gentle, phase-tolerant)."""
    a = math.exp(-2.0 * math.pi * cutoff / sr)
    y = buf(len(src))
    z = 0.0
    for i, x in enumerate(src):
        z = (1.0 - a) * x + a * z
        y[i] = z
    for _ in range(2):
        z = 0.0
        for i in range(len(y)):
            z = (1.0 - a) * y[i] + a * z
            y[i] = z
    return y


def highpass(src, cutoff, sr=SR):
    lp = lowpass(src, cutoff, sr)
    return [src[i] - lp[i] for i in range(len(src))]


def noise(n, rng):
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def mix_into(dst, src, at, gain=1.0):
    for i, v in enumerate(src):
        j = at + i
        if 0 <= j < len(dst):
            dst[j] += v * gain


def env(n, attack=0.02, release=0.08, sustain=1.0):
    a = max(1, int(n * attack))
    r = max(1, int(n * release))
    out = buf(n)
    for i in range(n):
        if i < a:
            g = i / float(a)
        elif i > n - r:
            g = max(0.0, (n - i) / float(r))
        else:
            g = 1.0
        out[i] = sustain * g
    return out


# --------------------------------------------------------------------------- #
# voice-like sources
# --------------------------------------------------------------------------- #

# (f0, formants[(hz, bw, amp), ...]) for the voice "types" used in the level.
VOICE_ADULT_F = (185.0, [(560.0, 90.0, 1.0), (1720.0, 130.0, 0.55), (2700.0, 200.0, 0.22)])
VOICE_ADULT_M = (120.0, [(500.0, 80.0, 1.0), (1180.0, 120.0, 0.5), (2500.0, 190.0, 0.2)])
VOICE_CHILD = (255.0, [(760.0, 110.0, 1.0), (2100.0, 170.0, 0.5), (3050.0, 240.0, 0.2)])

VOICE_TYPES = (VOICE_ADULT_F, VOICE_ADULT_M, VOICE_CHILD)


def glottal(n, f0, sr=SR, jitter=0.0, rng=None):
    """Band-limited-ish glottal source (sawtooth with soft roll-off)."""
    out = buf(n)
    ph = 0.0
    for i in range(n):
        f = f0 * (1.0 + jitter * ((rng.random() * 2.0 - 1.0) if rng else 0.0))
        ph += f / sr
        ph -= math.floor(ph)
        # soft sawtooth: sharpen then low-pass the whole thing later
        out[i] = 2.0 * ph - 1.0
    return out


def shape_voice(src, formants, sr=SR, breath=0.012, rng=None):
    y = src
    for (f0, bw, amp) in formants:
        y = resonator(y, f0, bw, sr, amp)
    # breath / fricative noise floor
    if breath > 0.0:
        hn = highpass(noise(len(y), rng or random.Random(7)), 2200.0, sr)
        y = [y[i] + hn[i] * breath for i in range(len(y))]
    return y


def syllable(dur, voice, sr=SR, amp=1.0, f0_scale=1.0, rng=None, breath=0.012):
    n = int(dur * sr)
    f0, fmts = voice
    src = glottal(n, f0 * f0_scale, sr, jitter=0.012, rng=rng)
    v = shape_voice(src, fmts, sr, breath=breath, rng=rng)
    v = [s * amp for s in v]
    e = env(n, attack=0.18, release=0.30)
    return [v[i] * e[i] for i in range(n)]


def consonant(dur, rng, center=2600.0, bw=1400.0, amp=1.0, sr=SR):
    n = int(dur * sr)
    hn = highpass(noise(n, rng), 1400.0, sr)
    hn = resonator(hn, center, bw, sr, 1.0)
    e = env(n, attack=0.05, release=0.55)
    return [hn[i] * e[i] * amp for i in range(n)]


def say(group, rng, sr=SR, gap=0.045, lead_consonant=0.055, amp=1.0, f0_scale=1.0):
    """Build one 'spoken group' = (optional onset) + 1..n syllables."""
    voice = VOICE_TYPES[group % len(VOICE_TYPES)]
    dur = 0.17 + 0.11 * (group % 3)
    parts = []
    if group % 2 == 0:
        parts.append(consonant(lead_consonant, rng,
                               center=1800.0 + 500.0 * (group % 4), amp=0.7 * amp, sr=sr))
    parts.append(syllable(dur, voice, sr, amp=amp, f0_scale=f0_scale, rng=rng))
    if group % 3 == 0:
        parts.append(syllable(0.13, voice, sr, amp=0.75 * amp, f0_scale=f0_scale * 1.04, rng=rng))
    out = []
    for p in parts:
        out.extend(p)
        out.extend(buf(int(gap * sr)))
    return out


# --------------------------------------------------------------------------- #
# the broadcast (T2, "ban phat")
# --------------------------------------------------------------------------- #

def make_broadcast(clear, seed=2002):
    """
    clear=True  -> the version recoverable with light filtering (Nghe Loc).
    clear=False -> the broadcast as it is heard normally: buried under noise.
    Both files are the SAME event, only filtered / re-balanced, so switching
    listening state genuinely changes what can be heard (not a fake label).
    """
    rng = random.Random(seed)
    n_total = int(16.0 * SR)
    out = buf(n_total)

    # 1) operator line (the 02:16:34 announcement), 0.6s .. 3.4s
    op = []
    for i, g in enumerate((0, 1, 2, 3, 4, 5)):
        s = say(g, rng, amp=0.95, f0_scale=0.95)
        op.extend(s)
        op.extend(buf(int(0.05 * SR)))
    mix_into(out, lowpass(op, 5200.0), int(0.6 * SR), 1.0)

    # 2) 65 answers ("Con! Con o day!") spread across 3.8s .. 14.4s
    #    two of them are deliberately tiny + quiet (chi Tuyet & be Bong)
    #    one of them is a child voice, and it is CUT OFF mid-sentence.
    n_answers = 65
    start = 3.8
    span = 10.6
    step = span / n_answers
    child_index = 29
    for i in range(n_answers):
        at = int((start + i * step + rng.uniform(-0.018, 0.018)) * SR)
        tiny = i in (11, 12)          # the two voices almost nobody hears
        if i == child_index:
            # Nhi: "Con! Con em o-" and then the tape runs on
            body = say(4, rng, amp=0.95, f0_scale=1.18)
            body = body[:int(0.52 * SR)]
            body = lowpass(body, 5600.0)
            tail = buf(int(0.30 * SR))
            mix_into(out, body + tail, at, 1.05)
            continue
        g = 0 if tiny else (1 + (i % 3))
        s = say(g, rng, amp=1.0)
        s = lowpass(s, 5000.0)
        a = 0.16 if tiny else (0.62 if not clear else 0.72)
        mix_into(out, s, at, a)

    if not clear:
        # The broadcast as broadcast: low band only, buried under the carrier
        # hiss. Nothing above ~380 Hz survives, so no answer is identifiable.
        body = lowpass(out, 380.0)
        hiss = lowpass(noise(n_total, random.Random(91)), 2600.0)
        for i in range(n_total):
            hiss[i] *= 0.55 + 0.12 * math.sin(2.0 * math.pi * 0.7 * i / SR)
        out = [body[i] * 0.85 + hiss[i] * 0.42 for i in range(n_total)]
        out = lowpass(out, 900.0)
    else:
        out = lowpass(out, 11000.0)

    out = fade_edges(norm(out, 0.86), 20)
    return out


def make_rollcall(seed=17):
    """
    Nguoi Cho Diem Danh: a muffled roll call from the classroom speaker,
    then a pause, then one small answer. Heard through a wall on purpose.
    """
    rng = random.Random(seed)
    n_total = int(13.0 * SR)
    out = buf(n_total)

    call = []
    for g in (0, 1, 2, 3, 4):
        call.extend(say(g, rng, amp=0.9, f0_scale=0.8))
        call.extend(buf(int(0.09 * SR)))
    mix_into(out, lowpass(call, 1500.0), int(1.0 * SR), 1.0)

    # 4.2s: a single small answer, far away
    reply = say(2, rng, amp=0.7, f0_scale=1.15)
    reply = lowpass(reply, 1400.0)
    mix_into(out, reply, int(4.2 * SR), 0.85)

    # speaker carrier hum under the whole thing
    hum = buf(n_total)
    for i in range(n_total):
        t = i / SR
        hum[i] = (0.16 * math.sin(2 * math.pi * 50.0 * t)
                  + 0.09 * math.sin(2 * math.pi * 100.0 * t)
                  + 0.05 * math.sin(2 * math.pi * 150.0 * t))
    out = [out[i] + hum[i] for i in range(n_total)]
    out = lowpass(out, 2600.0)
    return fade_edges(norm(out, 0.8), 30)


def make_child_reply(seed=29):
    """The thing in the back corner. Very quiet, very small, cut off."""
    rng = random.Random(seed)
    n_total = int(3.2 * SR)
    out = buf(n_total)
    body = say(4, rng, amp=0.8, f0_scale=1.2)
    body = body[:int(0.9 * SR)]
    body = lowpass(body, 2200.0)
    mix_into(out, body, int(0.25 * SR), 1.0)
    return fade_edges(norm(out, 0.55), 40)


def make_ambience(seed=5):
    """Abandoned rural school at night: air, rain on tin roof, a slow drip."""
    rng = random.Random(seed)
    n_total = int(9.0 * SR)
    out = buf(n_total)
    hiss = highpass(noise(n_total, rng), 1200.0)
    for i in range(n_total):
        t = i / SR
        mod = 0.75 + 0.25 * math.sin(2 * math.pi * 0.11 * t) * math.sin(2 * math.pi * 0.037 * t)
        out[i] = hiss[i] * 0.16 * mod
    rumble = buf(n_total)
    for i in range(n_total):
        t = i / SR
        rumble[i] = (0.5 * math.sin(2 * math.pi * 54.0 * t + 1.2 * math.sin(2 * math.pi * 0.07 * t))
                     + 0.3 * math.sin(2 * math.pi * 81.0 * t))
    out = [out[i] + rumble[i] * 0.13 for i in range(n_total)]
    # three distant drips
    for k, dt in enumerate((2.1, 5.4, 8.0)):
        d = buf(int(0.22 * SR))
        e = env(len(d), 0.01, 0.9)
        for i in range(len(d)):
            d[i] = math.sin(2 * math.pi * (900.0 - 2600.0 * i / len(d)) * i / SR) * e[i]
        mix_into(out, lowpass(d, 2600.0), int(dt * SR), 0.22 - 0.03 * k)
    return loopify(norm(out, 0.7), 300)


def make_noise_mask(seed=13):
    """The 'masking' bed. Loud in normal listening, almost silent when filtering."""
    rng = random.Random(seed)
    n_total = int(4.0 * SR)
    w = noise(n_total, rng)
    p = lowpass(w, 5200.0)
    out = [0.75 * p[i] + 0.25 * w[i] for i in range(n_total)]
    for i in range(n_total):
        t = i / SR
        out[i] *= 0.8 + 0.2 * math.sin(2 * math.pi * 0.9 * t)
    return loopify(norm(out, 0.55), 200)


def make_clarity_tone(seed=23):
    """Quiet focus cue for the enhanced listening state."""
    n_total = int(4.0 * SR)
    out = buf(n_total)
    for i in range(n_total):
        t = i / SR
        trem = 0.7 + 0.3 * math.sin(2 * math.pi * 0.5 * t)
        out[i] = trem * (0.5 * math.sin(2 * math.pi * 196.0 * t)
                         + 0.25 * math.sin(2 * math.pi * 392.0 * t + 0.7)
                         + 0.12 * math.sin(2 * math.pi * 587.0 * t + 1.9))
    return loopify(norm(out, 0.5), 250)


def make_speaker_hum(seed=31):
    """Dying PA transformer in the classroom."""
    rng = random.Random(seed)
    n_total = int(3.0 * SR)
    out = buf(n_total)
    for i in range(n_total):
        t = i / SR
        v = 0.5 * math.sin(2 * math.pi * 50.0 * t) + 0.3 * math.sin(2 * math.pi * 150.0 * t)
        v += 0.1 * math.sin(2 * math.pi * 250.0 * t)
        if rng.random() < 0.00035:
            v += rng.uniform(-0.7, 0.7)
        out[i] = v
    return loopify(norm(out, 0.35), 200)


def make_blip(freqs, dur, seed, decay=6.0, noise_mix=0.0):
    rng = random.Random(seed)
    n = int(dur * SR)
    out = buf(n)
    for i in range(n):
        t = i / SR
        e = math.exp(-decay * t)
        v = 0.0
        for k, f in enumerate(freqs):
            v += (1.0 / (k + 1.0)) * math.sin(2 * math.pi * f * t)
        out[i] = v * e
    if noise_mix > 0.0:
        hn = highpass(noise(n, rng), 2000.0)
        for i in range(n):
            out[i] += hn[i] * noise_mix * math.exp(-decay * 1.4 * (i / SR))
    return fade_edges(norm(out, 0.6), 6)


def make_paper(seed=41):
    rng = random.Random(seed)
    n = int(0.55 * SR)
    out = buf(n)
    hn = highpass(noise(n, rng), 2600.0)
    for i in range(n):
        t = i / SR
        e = math.exp(-7.0 * t) * (0.6 + 0.4 * math.sin(2 * math.pi * 23.0 * t))
        out[i] = hn[i] * e * 0.5
    tone = [math.sin(2 * math.pi * 660.0 * (i / SR)) * math.exp(-9.0 * (i / SR)) * 0.18
            for i in range(n)]
    out = [out[i] + tone[i] for i in range(n)]
    return fade_edges(norm(out, 0.5), 6)


def make_tape_deck(seed=53):
    rng = random.Random(seed)
    n = int(0.9 * SR)
    out = buf(n)
    hiss = highpass(noise(n, rng), 3000.0)
    for i in range(n):
        t = i / SR
        clunk = math.exp(-22.0 * t) * (0.6 * math.sin(2 * math.pi * 90.0 * t)
                                       + 0.4 * math.sin(2 * math.pi * 143.0 * t))
        motor = 0.10 * math.sin(2 * math.pi * 48.0 * t) * min(1.0, t * 3.0)
        out[i] = clunk + motor + hiss[i] * 0.06 * min(1.0, t * 2.0)
    return fade_edges(norm(out, 0.55), 8)


# --------------------------------------------------------------------------- #
# writing
# --------------------------------------------------------------------------- #

def write_wav(name, samples, sr=SR):
    path = os.path.join(OUT_DIR, name + ".wav")
    frames = bytearray()
    for v in samples:
        s = int(max(-1.0, min(1.0, v)) * 32767.0)
        frames += struct.pack("<h", s)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(bytes(frames))
    return path, len(frames) * 2


JOBS = [
    ("S_KL_T2_Clear", lambda: make_broadcast(clear=True)),
    ("S_KL_T2_Masked", lambda: make_broadcast(clear=False)),
    ("S_KL_RollCall", make_rollcall),
    ("S_KL_ChildReply", make_child_reply),
    ("S_KL_Ambience_Hall", make_ambience),
    ("S_KL_NoiseMask", make_noise_mask),
    ("S_KL_ClarityTone", make_clarity_tone),
    ("S_KL_SpeakerHum", make_speaker_hum),
    ("S_KL_UI_Interact", lambda: make_blip((880.0, 1320.0), 0.16, 3, decay=22.0, noise_mix=0.12)),
    ("S_KL_UI_Evidence", lambda: make_paper(9)),
    ("S_KL_UI_ModeShift", lambda: make_blip((520.0, 780.0, 1170.0), 0.34, 11, decay=9.0)),
    ("S_KL_TapeDeck", make_tape_deck),
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for name, fn in JOBS:
        samples = fn()
        path, size = write_wav(name, samples)
        total += size
        print("%-22s %8.1f KB" % (name, size / 1024.0))
    print("TOTAL %.1f MB in %s" % (total / (1024.0 * 1024.0), OUT_DIR))


if __name__ == "__main__":
    main()

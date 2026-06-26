#!/usr/bin/env python3
"""Generate deep, warm brown-noise WAV files for masking sudden sounds.

Each file is true brown (Brownian / "red") noise produced by passing white
noise through a leaky integrator, which yields the characteristic -6 dB/octave
roll-off that sounds deep and warm. A gentle subsonic high-pass removes DC
drift so the loudness headroom is spent on audible content rather than
inaudible rumble. Short fades avoid clicks on start/stop and loop points.
"""

import os
import numpy as np
from scipy import signal
from scipy.io import wavfile

# --- Output settings -------------------------------------------------------
SAMPLE_RATE = 44100          # standard, universally playable
DURATION_S = 6 * 60          # 6 minutes per file
N_FILES = 20
FADE_S = 2.0                 # fade in/out length
PEAK_DBFS = -1.5             # normalization target (leaves a little headroom)

# Leaky-integrator coefficient. Closer to 1.0 => deeper, warmer (lower corner).
# corner freq ~= (1 - R) * SR / (2*pi)  ->  ~20 Hz here.
R = 0.99715

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio", "brown-noise")


def make_brown(rng, n):
    """White noise -> leaky integrator (brown) -> subsonic high-pass."""
    white = rng.standard_normal(n).astype(np.float64)
    # Leaky integrator: y[n] = white[n] + R * y[n-1]  (brown spectrum)
    brown = signal.lfilter([1.0], [1.0, -R], white)
    # Remove subsonic drift/DC (12 Hz, 2nd-order Butterworth high-pass).
    sos = signal.butter(2, 12.0, btype="highpass", fs=SAMPLE_RATE, output="sos")
    brown = signal.sosfilt(sos, brown)
    return brown


def normalize_peak(x, dbfs):
    peak = np.max(np.abs(x))
    if peak == 0:
        return x
    target = 10 ** (dbfs / 20.0)
    return x * (target / peak)


def apply_fades(x, sr, fade_s):
    f = int(sr * fade_s)
    if f * 2 >= len(x):
        return x
    ramp = np.linspace(0.0, 1.0, f, dtype=np.float64) ** 2  # equal-ish power
    x[:f] *= ramp
    x[-f:] *= ramp[::-1]
    return x


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    n = SAMPLE_RATE * DURATION_S
    total_bytes = 0
    for i in range(1, N_FILES + 1):
        rng = np.random.default_rng(20260626 + i)  # distinct, reproducible
        x = make_brown(rng, n)
        x = apply_fades(x, SAMPLE_RATE, FADE_S)
        x = normalize_peak(x, PEAK_DBFS)
        pcm = np.clip(x * 32767.0, -32768, 32767).astype(np.int16)
        path = os.path.join(OUT_DIR, f"brown-noise-{i:02d}.wav")
        wavfile.write(path, SAMPLE_RATE, pcm)
        sz = os.path.getsize(path)
        total_bytes += sz
        print(f"  {os.path.basename(path)}  {sz/1e6:6.1f} MB")
    print(f"Done: {N_FILES} files, {total_bytes/1e6:.0f} MB total -> {OUT_DIR}")


if __name__ == "__main__":
    main()

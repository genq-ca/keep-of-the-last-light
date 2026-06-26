#!/usr/bin/env python3
"""Generate a graded set of deep, warm brown-noise WAV files for masking.

Each file is true brown (Brownian / "red") noise: white noise through a leaky
integrator, giving the characteristic -6 dB/octave roll-off that sounds deep
and warm. A subsonic high-pass removes DC drift so headroom goes to audible
content, and short fades avoid clicks on start/stop and loop points.

Because pure brown noise is statistically stationary, two files with different
random seeds sound identical to the ear. To make the 20 files *audibly*
distinct, we vary the tone across the set:

  - corner frequency of the leaky integrator  -> how DEEP / sub-heavy it is
  - low-pass cutoff (warmth)                   -> how DARK vs OPEN/AIRY it is

File 01 is the deepest & darkest (sub-heavy, muffled rumble); file 20 is the
warmest & fullest (more body and air). The steps in between are a smooth
gradient, so each file is clearly different from its neighbours.
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

# Tone gradient across the set (log-spaced, file 01 -> file 20).
CORNER_HZ_LO, CORNER_HZ_HI = 8.0, 28.0      # leaky-integrator corner: depth
LOWPASS_HZ_LO, LOWPASS_HZ_HI = 700.0, 9000.0  # low-pass cutoff: warmth/openness

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio", "brown-noise")


def logspread(lo, hi, i, n):
    """Log-interpolate between lo..hi for step i of n (i in 0..n-1)."""
    t = 0.0 if n == 1 else i / (n - 1)
    return lo * (hi / lo) ** t


def make_brown(rng, n, corner_hz, lowpass_hz):
    """White noise -> leaky integrator (brown) -> subsonic HPF -> warmth LPF."""
    white = rng.standard_normal(n).astype(np.float64)
    # Leaky integrator: y[n] = white[n] + R*y[n-1]. R set by the corner freq;
    # lower corner => closer to 1.0 => deeper, more sub-bass weight.
    r = 1.0 - 2.0 * np.pi * corner_hz / SAMPLE_RATE
    brown = signal.lfilter([1.0], [1.0, -r], white)
    # Remove subsonic drift/DC (12 Hz high-pass).
    hp = signal.butter(2, 12.0, btype="highpass", fs=SAMPLE_RATE, output="sos")
    brown = signal.sosfilt(hp, brown)
    # Warmth: gentle low-pass shapes how dark vs open the file sounds.
    lp = signal.butter(2, lowpass_hz, btype="lowpass", fs=SAMPLE_RATE, output="sos")
    brown = signal.sosfilt(lp, brown)
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
    for i in range(N_FILES):
        corner = logspread(CORNER_HZ_LO, CORNER_HZ_HI, i, N_FILES)
        lowpass = logspread(LOWPASS_HZ_LO, LOWPASS_HZ_HI, i, N_FILES)
        rng = np.random.default_rng(20260626 + i + 1)  # distinct, reproducible
        x = make_brown(rng, n, corner, lowpass)
        x = apply_fades(x, SAMPLE_RATE, FADE_S)
        x = normalize_peak(x, PEAK_DBFS)
        pcm = np.clip(x * 32767.0, -32768, 32767).astype(np.int16)
        path = os.path.join(OUT_DIR, f"brown-noise-{i + 1:02d}.wav")
        wavfile.write(path, SAMPLE_RATE, pcm)
        sz = os.path.getsize(path)
        total_bytes += sz
        print(f"  brown-noise-{i + 1:02d}.wav  corner={corner:5.1f}Hz  "
              f"lowpass={lowpass:6.0f}Hz  {sz / 1e6:5.1f} MB")
    print(f"Done: {N_FILES} files, {total_bytes / 1e6:.0f} MB total -> {OUT_DIR}")


if __name__ == "__main__":
    main()

"""
make_sounds.py - generates placeholder 8-bit style sound effects into assets/sounds/

Run once:  python make_sounds.py

Uses only the standard library (wave, struct, math, random) - no pip install needed.
Replace any .wav with your own file of the same name and the game picks it up.
"""

import math                                     # Waveform math
import os                                       # Output paths
import random                                   # Noise generation
import struct                                   # Packing samples into bytes
import wave                                     # Writing .wav files

RATE = 22050                                    # Samples per second (retro-friendly and small)
AMP = 12000                                     # Peak amplitude out of 32767 (leaves headroom)
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'sounds')


def square(t, freq):                            # Square wave: the classic chiptune timbre
    return 1.0 if (t * freq) % 1.0 < 0.5 else -1.0


def saw(t, freq):                               # Saw wave: brighter, good for sweeps
    return 2.0 * ((t * freq) % 1.0) - 1.0


def tone(freq_start, freq_end, ms, wave_fn=square, decay=True, noise=0.0):
    """Build one tone as a list of float samples in the range -1..1."""
    n = int(RATE * ms / 1000.0)                 # Total sample count
    out = []                                    # Collected samples
    for i in range(n):                          # Generate sample by sample
        t = i / RATE                            # Time in seconds
        progress = i / max(1, n - 1)            # 0.0 at the start, 1.0 at the end
        freq = freq_start + (freq_end - freq_start) * progress # Linear pitch sweep
        value = wave_fn(t, freq)                # The raw waveform
        if noise:                               # Optionally mix in white noise
            value = value * (1.0 - noise) + random.uniform(-1, 1) * noise
        if decay:                               # Fade out so notes do not click
            value *= (1.0 - progress) ** 1.5    # Exponential-ish decay
        out.append(value)                       # Store the sample
    return out


def silence(ms):                                # A short gap between notes
    return [0.0] * int(RATE * ms / 1000.0)      # Zero samples


def save(samples, name):                        # Write float samples to a 16-bit mono .wav
    path = os.path.join(OUT_DIR, name + '.wav') # Output path
    frames = b''.join(struct.pack('<h', int(max(-1.0, min(1.0, s)) * AMP)) for s in samples)
    with wave.open(path, 'wb') as w:            # Open the wav for writing
        w.setnchannels(1)                       # Mono
        w.setsampwidth(2)                       # 16-bit samples
        w.setframerate(RATE)                    # Sample rate
        w.writeframes(frames)                   # Write the audio data
    print('wrote', name + '.wav', '({} ms)'.format(int(len(samples) / RATE * 1000)))


def build_all():                                # Generate every sound the game asks for
    os.makedirs(OUT_DIR, exist_ok=True)         # Make sure assets/sounds/ exists
    random.seed(7)                              # Deterministic noise, so reruns sound identical

    # eat: two quick rising blips - reads as "collect"
    save(tone(660, 880, 60) + tone(880, 1320, 70), 'eat')

    # hit: harsh descending buzz with noise - reads as "damage"
    save(tone(420, 110, 220, wave_fn=saw, noise=0.45), 'hit')

    # bump: short low thud - reads as "blocked / stunned"
    save(tone(180, 90, 130, noise=0.2), 'bump')

    # skill: fast upward sweep - reads as "power on"
    save(tone(300, 1200, 180, wave_fn=saw), 'skill')

    # win: three-note major arpeggio
    save(tone(523, 523, 110) + silence(20) +    # C5
         tone(659, 659, 110) + silence(20) +    # E5
         tone(784, 784, 260), 'win')            # G5, held longer


if __name__ == '__main__':                      # Allow running this file directly
    build_all()                                 # Generate the whole sound set
    print('\nDone. Sounds are in:', OUT_DIR)    # Tell the user where they landed

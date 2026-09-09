"""
audio.py - non-blocking sound effects. Code only: NO audio files are generated,
and NO third-party package is required.

The game is turtle + stdlib. This module keeps it that way: it looks for audio
files that already exist, and if it finds none it turns into a no-op - every
`sfx.play(...)` returns immediately and the game runs exactly as it does with the
sound code absent. So this is safe to ship before any audio is added.

--------------------------------------------------------------------------------
HOW TO ACTUALLY GET SOUND (no install needed)

Put **.wav** files in `assets/sounds/`, named after the events:

    eat.wav  hit.wav  bump.wav  power.wav  score.wav
    win.wav  lose.wav  select.wav  start.wav

On Windows those play through `winsound`, which is in the standard library - so
nothing to install. The repo already ships `sound_effect/*.mp3`; converting those
to .wav with any converter (Audacity, ffmpeg, an online one) is the shortest path,
because .mp3 CANNOT be played by winsound or by the CLI players. Only pygame reads
.mp3, and pygame is optional - if it is not installed the .mp3 files are ignored
rather than half-played, and the startup line says so.

Lookup order per event, first hit wins:

  1. assets/sounds/<event>.wav        <- put files here
  2. ../../sound_effect/<candidate>   <- the repo's .mp3 pack, only usable via pygame

--------------------------------------------------------------------------------
BACKENDS, first usable one wins

  1. pygame.mixer  OPTIONAL. Overlapping sounds, volume control, reads .mp3
  2. winsound      Windows stdlib, .wav only, one sound at a time  <- the default path
  3. command line  afplay / paplay / aplay / ffplay, .wav, one process per sound
  4. silent        nothing usable was found; every play() is a no-op

Nothing in here is allowed to raise or block. A missing file, a broken file or a
busy audio device must never take the game down with it.
"""

import os
import shutil
import subprocess

from game_config import SOUND_ON, SOUND_DIR, SOUND_VOLUME
from scene_manager import ASSET_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_PATH = os.path.join(ASSET_DIR, SOUND_DIR)             # assets/sounds/
REPO_SOUND_PATH = os.path.abspath(                          # <repo>/sound_effect/
    os.path.join(BASE_DIR, '..', '..', 'sound_effect'))

# Event name -> filenames to try in the shipped .mp3 pack, best match first.
# The event names are what the game calls: sfx.play('eat'), sfx.play('hit'), ...
EVENTS = {
    'eat':    ('eat_fruit.mp3', 'motion_eating.mp3'),
    'hit':    ('bomb.mp3',),
    'bump':   ('impact_wall.mp3',),
    'power':  ('increase_speed.mp3', 'skill_selection.mp3'),
    'score':  ('score.mp3',),
    'win':    ('result_fanfare.mp3',),
    'lose':   ('bomb.mp3',),
    'select': ('setting.mp3', 'skill_selection.mp3'),
    'start':  ('start_1.mp3', 'start_2.mp3', 'start_3.mp3'),
}


class SoundManager:
    """The game only ever calls play(), toggle() and status()."""

    def __init__(self):
        self.enabled = SOUND_ON                 # Runtime mute flag (X toggles it)
        self.backend = 'silent'
        self._files = {}                        # event -> absolute path, existing files only
        self._cache = {}                        # pygame Sound objects
        self._cli = None
        self._winsound = None
        self._find_files()
        self._pick_backend()

    # ---------- setup ----------
    def _find_files(self):
        for event, candidates in EVENTS.items():
            wav = os.path.join(SOUND_PATH, event + '.wav')   # 1. assets/sounds/<event>.wav
            if os.path.isfile(wav):
                self._files[event] = wav
                continue
            for name in candidates:                          # 2. the repo .mp3 pack
                path = os.path.join(REPO_SOUND_PATH, name)
                if os.path.isfile(path):
                    self._files[event] = path
                    break

    def _pick_backend(self):
        if not self._files:                     # Nothing to play: stay silent, skip probing
            return

        needs_mp3 = any(p.lower().endswith('.mp3') for p in self._files.values())

        try:                                    # 1. pygame.mixer
            import pygame
            pygame.mixer.init()
            for event, path in self._files.items():
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(SOUND_VOLUME)
                    self._cache[event] = snd
                except Exception:
                    pass                        # One bad file must not sink the backend
            if self._cache:
                self.backend = 'pygame'
                return
        except Exception:
            self._cache.clear()

        # Without pygame, .mp3 cannot be played by the remaining backends. Keep only
        # the .wav files so we never hand an .mp3 to winsound and get silence plus a
        # stderr splat.
        wavs = {e: p for e, p in self._files.items() if p.lower().endswith('.wav')}
        if not wavs:
            self.backend = 'silent'
            self._missing_mp3_support = needs_mp3
            return
        self._files = wavs

        try:                                    # 2. winsound (Windows stdlib)
            import winsound
            self._winsound = winsound
            self.backend = 'winsound'
            return
        except Exception:
            pass

        for exe in ('afplay', 'paplay', 'aplay', 'ffplay'):  # 3. command line players
            if shutil.which(exe):
                self._cli = exe
                self.backend = 'cli'
                return

        self.backend = 'silent'                 # 4. give up quietly

    # ---------- playback ----------
    def play(self, event):
        """Play one event by name. Never blocks, never raises."""
        if not self.enabled or self.backend == 'silent':
            return
        path = self._files.get(event)
        if not path:
            return
        try:
            if self.backend == 'pygame':
                snd = self._cache.get(event)
                if snd is not None:
                    snd.play()
            elif self.backend == 'winsound':
                self._winsound.PlaySound(
                    path, self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)
            elif self.backend == 'cli':
                args = [self._cli, path]
                if self._cli == 'ffplay':
                    args = [self._cli, '-nodisp', '-autoexit', '-loglevel', 'quiet', path]
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass                                # An audio glitch must never kill the game

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def status(self):
        if self.backend == 'silent':
            return 'SOUND: none'
        return 'SOUND: {}'.format('on' if self.enabled else 'off')

    def report(self):
        """One line for the console, so it is obvious why there is or is not sound."""
        if self.backend == 'silent':
            if getattr(self, '_missing_mp3_support', False):
                return ('SOUND: off - only .mp3 files were found, and .mp3 needs pygame. '
                        'Convert sound_effect/*.mp3 to .wav into assets/sounds/ '
                        '(eat, hit, bump, power, score, win, lose, select, start) - '
                        'then it plays on the standard library alone.')
            return ('SOUND: off - no audio files found. Put .wav files in assets/sounds/ '
                    'named eat.wav, hit.wav, bump.wav, power.wav, score.wav, win.wav, '
                    'lose.wav, select.wav, start.wav - no install needed.')
        return 'SOUND: {} events via {}'.format(len(self._files), self.backend)


sfx = SoundManager()                            # One shared instance for the whole game

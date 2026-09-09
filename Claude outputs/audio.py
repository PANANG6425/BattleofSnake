"""
audio.py - sound effects. Code only: NO audio is generated and NO third-party
package is required.

With no audio files present every play() is a no-op and the game runs unchanged, so
this is safe to ship before any sound exists.

TO SWITCH SOUND ON: put .wav files in assets/sounds/ named after the events below.
On Windows those play through winsound, which is standard library - nothing to
install. The repo's sound_effect/*.mp3 are only usable via the optional pygame
backend, so without pygame they are ignored rather than half-played; report() says
exactly that at startup.

Nothing here may raise or block. A missing file, a broken file or a busy audio
device must never take the game down with it.
"""

import os
import shutil
import subprocess
import wave

from config import SOUND_ON, SOUND_DIR, SOUND_VOLUME, EXTRA_SOUND_DIRS, SOUND_DEBUG
from engine import ASSET_DIR, BASE_DIR

# Code only: NO audio is generated and NO third-party package is required. With no
# audio files present every play() is a no-op and the game runs unchanged.
#
# To get sound: put .wav files in assets/sounds/ named after the events below. On
# Windows those play through winsound, which is standard library. The repo's
# sound_effect/*.mp3 are only usable via the optional pygame backend, so without it
# they are ignored rather than half-played - report() says so.
SOUND_PATH = os.path.join(ASSET_DIR, SOUND_DIR)
# Extra folders to search, resolved relative to this file. config.EXTRA_SOUND_DIRS
# keeps them configurable instead of hardcoding a path that walks out of the project.
EXTRA_PATHS = [os.path.abspath(os.path.join(BASE_DIR, d)) for d in EXTRA_SOUND_DIRS]

SOUND_EVENTS = {                                # event -> .mp3 candidates in the repo pack
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
_WAV_NAMES = 'eat, hit, bump, power, score, win, lose, select, start'


def inspect_wav(path):
    """Is this .wav something winsound / the CLI players can actually play?

    Returns (ok, description). winsound needs plain PCM at 8 or 16 bits. The stdlib
    `wave` module refuses everything winsound refuses, which makes it a free
    pre-flight check:

        IEEE float32 .wav   -> "unknown extended format"   (Audacity's default export)
        MS ADPCM .wav       -> "unknown format: 2"
        an .mp3 renamed .wav-> "does not start with RIFF id"
        24-bit PCM          -> opens fine, but winsound will not play it

    This is why a file could be FOUND and still silent: PlaySound raised, and play()
    swallows exceptions on purpose so audio can never kill the game.
    """
    try:
        with wave.open(path) as w:
            ch, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
            comp = w.getcomptype()
        desc = '{} ch, {}-bit, {} Hz'.format(ch, width * 8, rate)
        if comp != 'NONE':
            return False, desc + ' compressed ({}) - needs plain PCM'.format(comp)
        if width not in (1, 2):
            return False, desc + ' - winsound needs 8 or 16-bit, not {}'.format(width * 8)
        return True, desc
    except wave.Error as e:
        return False, 'not a playable PCM wav: {}'.format(e)
    except Exception as e:
        return False, 'unreadable: {}: {}'.format(type(e).__name__, e)


class SoundManager:
    """The game only calls play(), toggle() and report()."""

    def __init__(self):
        self.enabled = SOUND_ON
        self.backend = 'silent'
        self._files = {}
        self._cache = {}
        self._cli = None
        self._winsound = None
        self._missing_mp3_support = False
        self._bad_wavs = {}                     # event -> why the file is unplayable
        self.last_error = None                  # first play() failure, for diagnose()
        self._find_files()
        self._pick_backend()

    def _find_files(self):
        """First hit wins, cheapest and most explicit name first.

        Every folder is searched for .wav BEFORE any .mp3, because .wav plays on the
        standard library and .mp3 needs the optional pygame backend. A .wav dropped
        into sound_effect/ next to the mp3 pack is therefore picked up and used - you
        do not have to move converted files into assets/sounds/ if you would rather
        convert them where they already are.
        """
        for event, candidates in SOUND_EVENTS.items():
            stems = [event] + [os.path.splitext(n)[0] for n in candidates]
            for path in self._search_order(event, stems, candidates):
                if os.path.isfile(path):
                    self._files[event] = path
                    break

    @staticmethod
    def _search_order(event, stems, candidates):
        """Every path to try for one event, in priority order."""
        yield os.path.join(SOUND_PATH, event + '.wav')       # 1. assets/sounds/eat.wav
        for folder in EXTRA_PATHS:                           # 2. sound_effect/eat.wav
            for stem in stems:                               #    then eat_fruit.wav
                yield os.path.join(folder, stem + '.wav')
        for name in candidates:                              # 3. the .mp3 pack (pygame)
            for folder in EXTRA_PATHS:
                yield os.path.join(folder, name)

    def _pick_backend(self):
        if not self._files:
            return
        needs_mp3 = any(p.lower().endswith('.mp3') for p in self._files.values())

        try:                                    # 1. pygame - optional, reads .mp3
            import pygame
            pygame.mixer.init()
            for event, path in self._files.items():
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(SOUND_VOLUME)
                    self._cache[event] = snd
                except Exception:
                    pass
            if self._cache:
                self.backend = 'pygame'
                return
        except Exception:
            self._cache.clear()

        # No pygame: drop .mp3 so we never hand one to a .wav-only backend.
        wavs = {e: p for e, p in self._files.items() if p.lower().endswith('.wav')}
        if not wavs:
            self._missing_mp3_support = needs_mp3
            return
        self._files = wavs

        # Drop .wav files the backends cannot play, and remember why. Without this a
        # float32 or ADPCM wav counted as "found", winsound raised, play() swallowed
        # it, and the status line claimed sound was working while nothing came out.
        good = {}
        for event, path in self._files.items():
            ok, desc = inspect_wav(path)
            if ok:
                good[event] = path
            else:
                self._bad_wavs[event] = (path, desc)
        self._files = good
        if not self._files:
            return

        try:                                    # 2. winsound - Windows stdlib
            import winsound
            self._winsound = winsound
            self.backend = 'winsound'
            return
        except Exception:
            pass

        for exe in ('afplay', 'paplay', 'aplay', 'ffplay'):   # 3. CLI players
            if shutil.which(exe):
                self._cli = exe
                self.backend = 'cli'
                return

    def play(self, event):
        """Never blocks, never raises. An audio glitch must not kill the game."""
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
        except Exception as e:
            if self.last_error is None:
                self.last_error = '{} on {}: {}: {}'.format(
                    self.backend, os.path.basename(path), type(e).__name__, e)
            if SOUND_DEBUG:
                print('SOUND ERROR:', self.last_error)

    def toggle(self):
        """Mute / unmute. Bound to X in both game modes."""
        self.enabled = not self.enabled
        return self.enabled

    def report(self):
        """One startup line, so silence is never a mystery."""
        if self.backend == 'silent':
            if self._missing_mp3_support:
                return ('SOUND: off - only .mp3 files were found, and .mp3 needs pygame. '
                        'Convert sound_effect/*.mp3 to .wav into assets/sounds/ ({}) - '
                        'then it plays on the standard library alone.'.format(_WAV_NAMES))
            if self._bad_wavs:
                return ('SOUND: off - {} file(s) found but not playable. Run '
                        'sfx.diagnose() or set SOUND_DEBUG=True in config.py for '
                        'details. Most likely they are not plain 16-bit PCM wav.'
                        .format(len(self._bad_wavs)))
            return ('SOUND: off - no audio files found. Put 16-bit PCM .wav files named '
                    '{} into assets/sounds/ (or into sound_effect/ next to the mp3s) '
                    '- no install needed.'.format(_WAV_NAMES))
        line = 'SOUND: {} events via {}'.format(len(self._files), self.backend)
        if self._bad_wavs:
            line += '  ({} file(s) skipped as unplayable - see sfx.diagnose())'.format(
                len(self._bad_wavs))
        return line

    def diagnose(self):
        """Multi-line report: every event, its file, its format, and the verdict.

        Print this when sound is missing. It answers the only question that matters:
        was the file found, and if so why is it not coming out of the speakers.
        """
        out = ['--- SOUND DIAGNOSIS ---',
               'backend        : {}'.format(self.backend),
               'muted          : {}'.format(not self.enabled),
               'wav folder     : {}'.format(SOUND_PATH),
               '  exists       : {}'.format(os.path.isdir(SOUND_PATH)),
               'extra folders  :']
        for f in EXTRA_PATHS:
            out.append('  {}  exists={}'.format(f, os.path.isdir(f)))
        out.append('')
        out.append('{:<8} {:<10} {}'.format('event', 'status', 'file / reason'))
        for event in SOUND_EVENTS:
            if event in self._files:
                ok, desc = inspect_wav(self._files[event])
                if self._files[event].lower().endswith('.mp3'):
                    desc = 'mp3 (pygame backend)'
                out.append('{:<8} {:<10} {}  [{}]'.format(
                    event, 'ready', os.path.basename(self._files[event]), desc))
            elif event in self._bad_wavs:
                path, why = self._bad_wavs[event]
                out.append('{:<8} {:<10} {}  <-- {}'.format(
                    event, 'UNUSABLE', os.path.basename(path), why))
            else:
                out.append('{:<8} {:<10} -'.format(event, 'missing'))
        if self._missing_mp3_support:
            out.append('')
            out.append('Only .mp3 was found. Without pygame nothing can play it.')
            out.append('Convert to 16-bit PCM wav instead:')
            out.append('  ffmpeg -i in.mp3 -c:a pcm_s16le -ac 1 -ar 22050 out.wav')
        if self._bad_wavs:
            out.append('')
            out.append('To fix an UNUSABLE file, re-encode it as plain 16-bit PCM:')
            out.append('  ffmpeg -i broken.wav -c:a pcm_s16le -ac 1 -ar 22050 fixed.wav')
            out.append('In Audacity: File > Export > WAV, choose')
            out.append('  "WAV (Microsoft) signed 16-bit PCM" - NOT 32-bit float.')
        if self.last_error:
            out.append('')
            out.append('first playback error: {}'.format(self.last_error))
        return '\n'.join(out)


sfx = SoundManager()                            # One shared instance for the whole game

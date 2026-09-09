"""
sounds.py - non-blocking sound effects with automatic fallback.

Backends are tried in order and the first available one wins:
  1. pygame.mixer  - best: overlapping sounds, volume control, low latency
  2. winsound      - Windows only, stdlib, one sound at a time
  3. command line  - afplay (macOS) / paplay or aplay (Linux), one process per sound
  4. silent        - nothing installed, every play() is a no-op

Nothing in here is allowed to raise or block: a game that crashes because a .wav is
missing is worse than a silent game. Generate the .wav files with make_sounds.py.
"""

import os                                       # Filesystem checks
import shutil                                   # Used to look for command line players
import subprocess                               # Used by the command line backend

from config import SOUND_ON, SOUND_DIR, SOUND_VOLUME # Sound settings
from screen import ASSET_PATH                   # assets/ folder, sounds live in assets/sounds/

SOUND_PATH = os.path.join(ASSET_PATH, SOUND_DIR) # Absolute path to the .wav folder

# Sound names the game asks for. Each maps to assets/sounds/<name>.wav
SOUND_NAMES = ('eat', 'hit', 'bump', 'skill', 'win')


class SoundManager:                             # Small wrapper so the game only ever calls play()
    def __init__(self):
        self.enabled = SOUND_ON                 # Runtime mute flag (M key toggles it)
        self.backend = 'silent'                 # Chosen backend name
        self._cache = {}                        # pygame Sound objects, keyed by name
        self._cli = None                        # Command line player executable, if that backend wins
        self._files = {}                        # name -> absolute .wav path, only for files that exist
        self._find_files()                      # Discover which .wav files are actually present
        self._pick_backend()                    # Decide how to play them

    # ---------- setup ----------
    def _find_files(self):                      # Record only the sounds that exist on disk
        for name in SOUND_NAMES:                # Check every sound the game may request
            path = os.path.join(SOUND_PATH, name + '.wav') # Expected file path
            if os.path.isfile(path):            # Only register real files
                self._files[name] = path        # Remember where it is

    def _pick_backend(self):                    # Try each backend from best to worst
        if not self._files:                     # No .wav files at all
            self.backend = 'silent'             # Nothing to play
            return

        try:                                    # 1. pygame.mixer
            import pygame                       # Optional dependency
            pygame.mixer.init()                 # Open the audio device
            for name, path in self._files.items():        # Preload every sound once
                snd = pygame.mixer.Sound(path)            # Decode the .wav
                snd.set_volume(SOUND_VOLUME)              # Apply the configured volume
                self._cache[name] = snd                   # Cache it for instant replay
            self.backend = 'pygame'             # This backend works
            return
        except Exception:                       # pygame missing, or no audio device
            self._cache.clear()                 # Drop anything half-loaded

        try:                                    # 2. winsound (Windows stdlib)
            import winsound                     # Raises ImportError off Windows
            self._winsound = winsound           # Keep the module handle
            self.backend = 'winsound'           # This backend works
            return
        except Exception:                       # Not on Windows
            pass

        for exe in ('afplay', 'paplay', 'aplay', 'ffplay'): # 3. command line players
            if shutil.which(exe):               # Is it on PATH?
                self._cli = exe                 # Remember which one to call
                self.backend = 'cli'            # This backend works
                return

        self.backend = 'silent'                 # 4. give up quietly

    # ---------- playback ----------
    def play(self, name):                       # Play one sound by name, never blocking
        if not self.enabled or self.backend == 'silent': # Muted or no backend
            return
        path = self._files.get(name)            # Look up the file
        if not path:                            # This sound was never generated
            return
        try:
            if self.backend == 'pygame':        # Best case: overlapping playback
                self._cache[name].play()        # Fire and forget
            elif self.backend == 'winsound':    # Windows: async flag keeps the game running
                self._winsound.PlaySound(path, self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)
            elif self.backend == 'cli':         # Spawn a detached player process
                args = [self._cli, path]        # Base command
                if self._cli == 'ffplay':       # ffplay needs flags to stay quiet and exit
                    args = [self._cli, '-nodisp', '-autoexit', '-loglevel', 'quiet', path]
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:                       # An audio glitch must never kill the game
            pass

    def toggle(self):                           # Flip mute on/off (bound to the M key)
        self.enabled = not self.enabled         # Invert the flag
        return self.enabled                     # Report the new state

    def status(self):                           # Short string for the HUD / console
        if self.backend == 'silent':            # No usable backend or no files
            return 'SOUND: none'
        return 'SOUND: {}'.format('on' if self.enabled else 'off') # Normal case


sfx = SoundManager()                            # One shared instance imported by the rest of the game

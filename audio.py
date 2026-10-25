import os
import wave

import numpy as np
import pygame

try:
    import pygame.sndarray as _sndarray
except Exception:
    _sndarray = None

SR = 22050
BGM_KEYS = ("bgm_title", "bgm_battle", "bgm_win", "bgm_lose")
SE_KEYS = ("se_place", "se_select", "se_win", "se_lose")
ALL_KEYS = BGM_KEYS + SE_KEYS

REPLACE_HELP = """[audio] 素材の差し替え先: assets/audio/<key>.ogg または .wav (16bit 44.1kHz 推奨)
  BGM: bgm_title / bgm_battle / bgm_win / bgm_lose  SE: se_place / se_select / se_win / se_lose
  無いものは assets/audio/_generated/ に自動生成した仮音を使用します。"""


def _note(freq, dur, amp, decay=0.0, harmonics=((1.0, 1.0),)):
    n = max(1, int(SR * dur))
    t = np.arange(n) / SR
    env = np.exp(-t * decay) if decay > 0 else np.ones(n)
    sig = np.zeros(n)
    for mult, a in harmonics:
        sig += a * np.sin(2 * np.pi * freq * mult * t)
    return sig * env * amp


def _edge_fade(sig, ms=25):
    k = int(SR * ms / 1000)
    if k * 2 < len(sig):
        ramp = np.linspace(0.0, 1.0, k)
        sig[:k] *= ramp
        sig[-k:] *= ramp[::-1]
    return sig


def _chords(chords_each, decay=1.0, bass=None):
    out = []
    for i, chord in enumerate(chords_each):
        seg = np.zeros(int(SR * chord[1]))
        for f in chord[0]:
            seg += _note(f, chord[1], 0.14, decay, ((1.0, 1.0), (2.0, 0.35)))
        if bass is not None:
            seg += _note(bass[i % len(bass)], chord[1], 0.12, 4.0)
        out.append(seg)
    return np.concatenate(out)


AM = (220.0, 261.63, 329.63)
F = (174.61, 220.0, 261.63)
C = (261.63, 329.63, 392.0)
G = (196.0, 246.94, 293.66)
EM = (164.81, 196.0, 246.94)


def _synth(key):
    if key == "se_place":
        n = int(SR * 0.09)
        t = np.arange(n) / SR
        sig = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 55) * 0.7
        click = np.random.randn(int(SR * 0.003)) * 0.35
        sig[: len(click)] += click
        return sig
    if key == "se_select":
        return _note(990, 0.07, 0.4, 40)
    if key == "se_win":
        parts = [_note(f, 0.09, 0.4, 12) for f in (440, 554.37, 659.25)]
        parts.append(_note(880, 0.5, 0.4, 5))
        return np.concatenate(parts)
    if key == "se_lose":
        parts = [_note(f, 0.28, 0.35, 8) for f in (329.63, 261.63, 220.0)]
        parts.append(_note(164.81, 0.6, 0.35, 5))
        return np.concatenate(parts)
    if key == "bgm_title":
        sig = _chords([(AM, 2.0), (F, 2.0), (C, 2.0), (G, 2.0)], decay=0.9)
        return _edge_fade(sig)
    if key == "bgm_battle":
        sig = _chords(
            [(AM, 1.0), (EM, 1.0), (F, 1.0), (G, 1.0)],
            decay=1.6,
            bass=(110.0, 82.41, 87.31, 98.0),
        )
        return _edge_fade(sig)
    if key == "bgm_win":
        parts = [_note(f, 0.16, 0.35, 6) for f in (440, 554.37, 659.25)]
        parts.append(_note(880, 0.9, 0.35, 3))
        return np.concatenate(parts)
    if key == "bgm_lose":
        parts = [_note(f, 0.35, 0.3, 6) for f in (329.63, 261.63, 220.0, 164.81)]
        return np.concatenate(parts)
    return np.zeros(int(SR * 0.1))


def _write_wav(path, sig):
    peak = max(1e-6, float(np.max(np.abs(sig))))
    data = np.clip(sig / peak, -1.0, 1.0) * 32000
    pcm = data.astype("<i2")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


class AudioManager:
    def __init__(self, root, bgm_vol=0.5, se_vol=0.8, se_muted=False, bgm_muted=False):
        self.ok = False
        self.bgm_vol = bgm_vol
        self.se_vol = se_vol
        self.se_muted = se_muted
        self.bgm_muted = bgm_muted
        self.audio_dir = os.path.join(root, "assets", "audio")
        self._raw = {}
        self._sounds = {}
        self._pitch_cache = {}
        self.bgm_name = None
        self.bgm_channel = None
        self.bgm_fade = None  # [t, dur, from_v, to_v]
        self.duck_level = 1.0
        self._duck_timer = 0.0
        try:
            pygame.mixer.pre_init(44100, -16, 1, 512)
            pygame.mixer.init(44100, -16, 1, 512)
            self.ok = True
        except Exception as e:
            print(f"[audio] mixer unavailable, running silent: {e}")
            return
        self._use_array = _sndarray is not None
        self._prepare()
        print(REPLACE_HELP)

    def _prepare(self):
        from assets import pick_audio_file

        missing = []
        for key in ALL_KEYS:
            path = pick_audio_file(self.audio_dir, key)
            if path is None:
                missing.append(key)
                path = os.path.join(self.audio_dir, "_generated", key + ".wav")
                try:
                    _write_wav(path, _synth(key))
                except Exception as e:
                    print(f"[audio] synth failed for {key}: {e}")
                    continue
            try:
                snd = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[audio] load failed {path}: {e}")
                continue
            self._sounds[key] = snd
            if self._use_array:
                try:
                    arr = _sndarray.samples(snd)
                    self._raw[key] = arr[:, 0].astype(np.float32) / 32768.0
                except Exception:
                    self._use_array = False
        if missing:
            print(f"[audio] 自動生成(プレースホルダ): {', '.join(missing)}")

    def play_se(self, key, pitch=1.0, vol=1.0):
        if not self.ok or self.se_muted:
            return
        snd = self._sounds.get(key)
        if snd is None:
            return
        try:
            if abs(pitch - 1.0) < 1e-3 or key not in self._raw or not self._use_array:
                snd.set_volume(self.se_vol * vol)
                snd.play()
            else:
                cache_key = (key, round(pitch, 3))
                sound = self._pitch_cache.get(cache_key)
                if sound is None:
                    raw = self._raw[key]
                    n = max(1, int(len(raw) / pitch))
                    idx = np.linspace(0, len(raw) - 1, n)
                    shifted = np.interp(idx, np.arange(len(raw)), raw)
                    arr = (np.clip(shifted, -1, 1) * 32767).astype(np.int16)
                    sound = _sndarray.make_sound(arr)
                    self._pitch_cache[cache_key] = sound
                sound.set_volume(self.se_vol * vol)
                sound.play()
        except Exception:
            snd.set_volume(self.se_vol * vol)
            snd.play()

    def play_bgm(self, key):
        if not self.ok:
            return
        if self.bgm_name == key and self.bgm_channel and self.bgm_channel.get_busy():
            return
        self.stop_bgm()
        snd = self._sounds.get(key)
        if snd is None:
            return
        self.bgm_name = key
        target = self._bgm_target()
        try:
            self.bgm_channel = snd.play(loops=-1)
        except Exception:
            self.bgm_name = None
            return
        if self.bgm_channel:
            self.bgm_channel.set_volume(0.0)
            self.bgm_fade = [0.0, 0.5, 0.0, target]

    def play_jingle(self, key):
        if not self.ok:
            return
        snd = self._sounds.get(key)
        if snd and not self.bgm_muted:
            snd.set_volume(self.bgm_vol)
            snd.play()

    def stop_bgm(self):
        if self.bgm_channel:
            self.bgm_channel.stop()
        self.bgm_channel = None
        self.bgm_name = None
        self.bgm_fade = None

    def duck(self, level=0.25, dur=2.0):
        self.duck_level = level
        self._duck_timer = dur

    def _bgm_target(self):
        if self.bgm_muted:
            return 0.0
        return self.bgm_vol * self.duck_level

    def set_mute(self, kind, muted):
        if kind == "se":
            self.se_muted = muted
        else:
            self.bgm_muted = muted
            if self.bgm_channel:
                self.bgm_fade = None
                self.bgm_channel.set_volume(0.0 if muted else self._bgm_target())

    def update(self, dt):
        if not self.ok:
            return
        if self._duck_timer > 0:
            self._duck_timer -= dt
            if self._duck_timer <= 0:
                self.duck_level = 1.0
                if self.bgm_channel:
                    tgt = self._bgm_target()
                    cur = self.bgm_channel.get_volume()
                    self.bgm_fade = [0.0, 0.4, cur, tgt]
        if self.bgm_fade and self.bgm_channel:
            t, dur, v0, v1 = self.bgm_fade
            t += dt
            k = min(1.0, t / dur)
            self.bgm_channel.set_volume(v0 + (v1 - v0) * k)
            if k >= 1.0:
                self.bgm_fade = None
            self.bgm_fade = [t, dur, v0, v1] if self.bgm_fade else None

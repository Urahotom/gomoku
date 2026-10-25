import json
import os

import pygame

FONT_CANDIDATES = ["notosansjp", "meiryo", "yu gothic ui", "ms gothic", "msgothic"]


def resolve_font(size, bold=False):
    for name in FONT_CANDIDATES:
        try:
            path = pygame.font.match_font(name, bold=bold)
        except Exception:
            path = None
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


class Character:
    def __init__(self, char_id, name, lines, images):
        self.char_id = char_id
        self.name = name
        self.lines = lines
        self.images = images

    def line(self, key, default=None):
        return self.lines.get(key, default)

    def rand(self, key, default=None):
        vals = self.lines.get(key)
        if not vals:
            return default
        if isinstance(vals, list):
            import random
            return random.choice(vals).rstrip(";")
        return vals.rstrip(";")


def wrap_text(font, text, width, max_lines=4):
    lines = []
    for raw in text.splitlines() or [""]:
        cur = ""
        for ch in raw:
            if font.size(cur + ch)[0] > width and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    return lines


def _fit(surf, w, h):
    ratio = min(w / surf.get_width(), h / surf.get_height())
    size = (max(1, int(surf.get_width() * ratio)), max(1, int(surf.get_height() * ratio)))
    return pygame.transform.smoothscale(surf, size)


def _placeholder(w, h, name, state):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    palette = {
        "normal": ((70, 110, 130), (235, 220, 205)),
        "win": ((170, 130, 40), (245, 230, 200)),
        "lose": ((90, 85, 95), (205, 200, 205)),
    }
    body, skin = palette.get(state, palette["normal"])
    cx = w // 2
    head_r = w // 6
    head_cy = int(h * 0.32)
    pygame.draw.polygon(
        surf, body,
        [(cx - w // 3, h), (cx - head_r, head_cy + head_r), (cx + head_r, head_cy + head_r), (cx + w // 3, h)],
    )
    pygame.draw.circle(surf, skin, (cx, head_cy), head_r)

    font = resolve_font(max(14, w // 12), bold=True)
    label = font.render(f"対戦相手  {name}", True, (250, 248, 242))
    lw, lh = label.get_size()
    pad = 8
    tag = pygame.Rect(0, 0, lw + pad * 2, lh + pad)
    tag.center = (cx, head_cy + head_r + int(h * 0.12))
    backdrop = pygame.Surface(tag.size, pygame.SRCALPHA)
    backdrop.fill((20, 16, 22, 190))
    surf.blit(backdrop, tag.topleft)
    pygame.draw.rect(surf, (238, 200, 120), tag, 2, border_radius=6)
    surf.blit(label, (tag.x + pad, tag.y + pad // 2))
    return surf


def load_character(root, char_id, portrait_size):
    base = os.path.join(root, "assets", "characters", char_id)
    name = char_id
    lines = {
        "start": "よろしくね!",
        "place": ["いい手;", "ここよ;"],
        "danger": "あれ、来てる…?",
        "win": "勝った!;",
        "lose": "うっそ…;",
        "draw": "引き分け!",
    }
    dialog_path = os.path.join(base, "dialog.json")
    try:
        with open(dialog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("name", char_id)
        merged = dict(lines)
        merged.update(data.get("lines", {}))
        lines = merged
    except (OSError, ValueError) as e:
        print(f"[assets] dialog.json not loaded for '{char_id}': {e}")

    w, h = portrait_size
    images = {}
    for state in ("normal", "win", "lose"):
        path = None
        for ext in (".png", ".jpg", ".jpeg", ".bmp"):
            cand = os.path.join(base, state + ext)
            if os.path.exists(cand):
                path = cand
                break
        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                images[state] = _fit(img, w, h)
                continue
            except Exception as e:
                print(f"[assets] failed to load {path}: {e}")
        images[state] = _placeholder(w, h, name, state)
    return Character(char_id, name, lines, images)


def pick_audio_file(audio_dir, key):
    for name in (key + ".ogg", key + ".wav"):
        p = os.path.join(audio_dir, name)
        if os.path.exists(p):
            return p
    p = os.path.join(audio_dir, "_generated", key + ".wav")
    if os.path.exists(p):
        return p
    return None

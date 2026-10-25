import math

import pygame

from assets import wrap_text

PANEL_BG = (36, 32, 40)
PANEL_EDGE = (90, 80, 100)
BUBBLE_BG = (248, 244, 236)
NAME_BG = (214, 168, 90)
TEXT = (45, 38, 35)


class CharPanel:
    def __init__(self, rect, character, fonts):
        self.rect = pygame.Rect(rect)
        self.char = character
        self.fonts = fonts
        self.state = "normal"
        self.cur = character.images["normal"]
        self.prev = None
        self.fade = 1.0
        self.text = ""
        self.shown = 0.0
        self.thinking = False
        self.t = 0.0
        self.portrait_rect = pygame.Rect(
            self.rect.x + 10, self.rect.y + 14, self.rect.w - 20, 372
        )
        self.bubble_rect = pygame.Rect(
            self.rect.x + 8, self.rect.y + 398, self.rect.w - 16, 148
        )

    def set_state(self, state):
        if state == self.state or state not in self.char.images:
            return
        self.prev = self.cur
        self.cur = self.char.images[state]
        self.state = state
        self.fade = 0.0

    def set_thinking(self, value):
        self.thinking = bool(value)

    def say(self, text):
        self.text = text or ""
        self.shown = 0.0

    def update(self, dt):
        self.t += dt
        if self.fade < 1.0:
            self.fade = min(1.0, self.fade + dt / 0.15)
        if self.shown < len(self.text):
            self.shown = min(len(self.text), self.shown + dt * 40)

    def _blit_portrait(self, surf, img, alpha, dy=0):
        x = self.portrait_rect.x + (self.portrait_rect.w - img.get_width()) // 2
        y = self.portrait_rect.bottom - img.get_height() + dy
        if alpha >= 0.999:
            surf.blit(img, (x, y))
        else:
            tmp = img.copy()
            tmp.set_alpha(int(255 * alpha))
            surf.blit(tmp, (x, y))

    def draw(self, surf):
        pygame.draw.rect(surf, PANEL_BG, self.rect)
        pygame.draw.line(
            surf, PANEL_EDGE, (self.rect.x, self.rect.y), (self.rect.x, self.rect.bottom), 2
        )
        dy = int(math.sin(self.t * 6.0) * 4) if self.thinking else 0
        if self.prev is not None:
            self._blit_portrait(surf, self.prev, 1.0 - self.fade, dy)
        self._blit_portrait(surf, self.cur, self.fade, dy)

        b = self.bubble_rect
        pygame.draw.rect(surf, BUBBLE_BG, b, border_radius=10)
        pygame.draw.rect(surf, PANEL_EDGE, b, 2, border_radius=10)
        name_s = self.fonts["small"].render(self.char.name, True, TEXT)
        chip = pygame.Rect(b.x + 10, b.y - 10, name_s.get_width() + 20, 22)
        pygame.draw.rect(surf, NAME_BG, chip, border_radius=8)
        surf.blit(name_s, (chip.x + 10, chip.y + 2))

        shown_text = self.text[: int(self.shown)]
        lines = wrap_text(self.fonts["small"], shown_text, b.w - 28)
        ty = b.y + 18
        for line in lines:
            surf.blit(self.fonts["small"].render(line, True, TEXT), (b.x + 14, ty))
            ty += self.fonts["small"].get_height() + 4
        if self.thinking:
            for i in range(3):
                ph = (self.t * 2.5 + i * 0.35) % 1.0
                glow = max(0.0, math.sin(ph * math.pi))
                dot = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(
                    dot, (90, 80, 95, int(100 + 150 * glow)), (6, 6), int(2 + 3 * glow)
                )
                surf.blit(dot, (b.right - 48 + i * 13, b.y + 10))

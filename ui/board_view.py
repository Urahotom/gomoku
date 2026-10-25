import math
import random

import pygame

LINE_COLOR = (70, 45, 20)
GOLD = (255, 200, 60)


class BoardView:
    def __init__(self, origin, cell, n):
        self.origin = origin
        self.cell = cell
        self.n = n
        self.bg = self._build_bg()

    def _build_bg(self):
        size = self.cell * self.n
        s = pygame.Surface((size, size))
        for y in range(size):
            t = y / size
            col = (int(205 - 45 * t), int(155 - 50 * t), int(90 - 45 * t))
            pygame.draw.line(s, col, (0, y), (size, y))
        ov = pygame.Surface((size, size), pygame.SRCALPHA)
        rng = random.Random(7)
        for _ in range(110):
            y = rng.randrange(size)
            y2 = y + rng.randint(0, 4)
            x0 = rng.randrange(size)
            x1 = min(size, x0 + rng.randint(60, 320))
            pygame.draw.line(
                ov, (120, 80, 40, rng.randint(10, 26)), (x0, y), (x1, y2), rng.randint(1, 2)
            )
        s.blit(ov, (0, 0))
        for i in range(self.n + 1):
            wdt = 2 if i in (0, self.n) else 1
            p = i * self.cell
            pygame.draw.line(s, LINE_COLOR, (p, 0), (p, size), wdt)
            pygame.draw.line(s, LINE_COLOR, (0, p), (size, p), wdt)
        for r in (3, 7, 11):
            for c in (3, 7, 11):
                cx = c * self.cell + self.cell // 2
                cy = r * self.cell + self.cell // 2
                pygame.draw.circle(s, LINE_COLOR, (cx, cy), 4)
        return s

    def cell_at(self, pos):
        mx, my = pos[0] - self.origin[0], pos[1] - self.origin[1]
        if not (0 <= mx < self.cell * self.n and 0 <= my < self.cell * self.n):
            return None
        return (my // self.cell, mx // self.cell)

    def center(self, r, c):
        return (
            self.origin[0] + c * self.cell + self.cell // 2,
            self.origin[1] + r * self.cell + self.cell // 2,
        )

    @staticmethod
    def _stone(surf, cx, cy, rad, color):
        if color == 1:
            base, hi, edge = (28, 28, 32), (95, 95, 105), (0, 0, 0)
        else:
            base, hi, edge = (238, 236, 228), (255, 255, 255), (120, 120, 115)
        pygame.draw.circle(surf, (40, 30, 20), (cx + 1, cy + 2), rad)
        pygame.draw.circle(surf, base, (cx, cy), rad)
        pygame.draw.circle(surf, hi, (cx - rad // 3, cy - rad // 3), max(2, rad // 3))
        pygame.draw.circle(surf, edge, (cx, cy), rad, 1)

    def draw(self, surf, board, now=0.0, pop=None, hover=None, hover_color=None,
             win=None, win_t=0.0):
        x, y = self.origin
        surf.blit(self.bg, (x, y))
        rad = self.cell // 2 - 4
        win_cells = set()
        if win:
            win_cells = {cell for line in win for cell in line}
        for r, c, color in board.history:
            cx, cy = self.center(r, c)
            s = 1.0
            if pop and (r, c) in pop:
                t = now - pop[(r, c)]
                if 0 <= t < 0.15:
                    e = t / 0.15
                    s = 1.0 + 0.25 * (1 - e) ** 2
            self._stone(surf, cx, cy, int(rad * s), color)
            if (r, c) in win_cells:
                pygame.draw.circle(surf, GOLD, (cx, cy), rad + 2, 2)
                pygame.draw.circle(surf, (255, 245, 200), (cx, cy), rad + 3, 1)
        if board.history:
            lr, lc, _ = board.history[-1]
            cx, cy = self.center(lr, lc)
            pygame.draw.circle(surf, (220, 60, 60), (cx, cy), rad - 4, 2)
        if win:
            line = max(win, key=len)
            p0, p1 = self.center(*line[0]), self.center(*line[-1])
            w = 3 + int(2 * abs(math.sin(win_t * 6)))
            pygame.draw.line(surf, (255, 240, 160), p0, p1, w + 4)
            pygame.draw.line(surf, GOLD, p0, p1, w)
            k = (win_t % 1.2) / 0.6
            if k > 1.0:
                k = 2.0 - k
            sx = p0[0] + (p1[0] - p0[0]) * k
            sy = p0[1] + (p1[1] - p0[1]) * k
            glow = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 240, 160, 60), (18, 18), 14)
            pygame.draw.circle(glow, (255, 250, 220, 170), (18, 18), 7)
            pygame.draw.circle(glow, (255, 255, 250, 255), (18, 18), 3)
            surf.blit(glow, (sx - 18, sy - 18), special_flags=pygame.BLEND_RGBA_ADD)
        if hover is not None and hover_color is not None:
            hr, hc = hover
            if board.get(hr, hc) == 0:
                cx, cy = self.center(hr, hc)
                ghost = pygame.Surface((rad * 2 + 2, rad * 2 + 2), pygame.SRCALPHA)
                col = (28, 28, 32, 110) if hover_color == 1 else (238, 236, 228, 140)
                pygame.draw.circle(ghost, col, (rad + 1, rad + 1), rad)
                surf.blit(ghost, (cx - rad - 1, cy - rad - 1))

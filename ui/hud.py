import math

import pygame

DARK = (28, 24, 30)
GOLD = (238, 200, 120)
WHITE = (240, 238, 232)
DIM = (12, 10, 14)
BTN_BG = (62, 54, 70)
BTN_HOVER = (96, 84, 106)
BTN_EDGE = (140, 128, 150)


def draw_title(surf, t, fonts, char, bg):
    surf.fill(DARK)
    bg_img = pygame.transform.smoothscale(bg, surf.get_size())
    bg_img.set_alpha(90)
    surf.blit(bg_img, (0, 0))
    w = surf.get_width()
    title = fonts["title"].render("五目並べ", True, GOLD)
    surf.blit(title, (w // 2 - title.get_width() // 2, 130))
    sub = fonts["mid"].render(f"{char.name} との対局", True, WHITE)
    surf.blit(sub, (w // 2 - sub.get_width() // 2, 230))
    if int(t * 2) % 2 == 0:
        hint = fonts["mid"].render("クリックまたは Enter でスタート", True, (220, 215, 205))
        surf.blit(hint, (w // 2 - hint.get_width() // 2, 330))
    img = char.images["normal"]
    surf.blit(img, (w - img.get_width() - 30, surf.get_height() - img.get_height()))
    ver = fonts["small"].render("M1 prototype", True, (150, 145, 150))
    surf.blit(ver, (10, surf.get_height() - 26))


def draw_hud(surf, bar_rect, label, stone_color, fonts):
    bar = pygame.Rect(bar_rect)
    s = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
    s.fill((20, 16, 22, 150))
    surf.blit(s, (bar.x, bar.y))
    cx, cy = bar.x + 26, bar.y + bar.h // 2
    base = (28, 28, 32) if stone_color == 1 else (238, 236, 228)
    pygame.draw.circle(surf, base, (cx, cy), 11)
    pygame.draw.circle(surf, (0, 0, 0), (cx, cy), 11, 1)
    pygame.draw.circle(surf, (255, 255, 255), (cx - 3, cy - 3), 3)
    surf.blit(fonts["mid"].render(label, True, WHITE), (bar.x + 48, bar.y + 8))


def draw_result(surf, fonts, title_text, alpha):
    w, h = surf.get_size()
    dim = pygame.Surface((w, h), pygame.SRCALPHA)
    dim.fill((*DIM, int(170 * alpha)))
    surf.blit(dim, (0, 0))
    if alpha < 0.6:
        return
    panel = pygame.Rect(w // 2 - 210, 210, 420, 160)
    pygame.draw.rect(surf, (48, 42, 54), panel, border_radius=14)
    pygame.draw.rect(surf, GOLD, panel, 3, border_radius=14)
    t = fonts["big"].render(title_text, True, GOLD)
    surf.blit(t, (panel.centerx - t.get_width() // 2, panel.y + 26))
    l1 = fonts["small"].render("クリック / Enter: タイトルへ    R: 再戦", True, WHITE)
    surf.blit(l1, (panel.centerx - l1.get_width() // 2, panel.y + 100))


def draw_button(surf, rect, text, font, hover):
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, BTN_HOVER if hover else BTN_BG, r, border_radius=8)
    pygame.draw.rect(surf, BTN_EDGE, r, 1, border_radius=8)
    t = font.render(text, True, WHITE)
    surf.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))


def vignette(size):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    w, h = size
    for i in range(6):
        k = 30 + i * 26
        pygame.draw.rect(surf, (0, 0, 0, 8), (i * 4, i * 4, w - i * 8, h - i * 8), k)
    return surf

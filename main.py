import os
import random
import sys
import time

import pygame

import config
from config import W, H, CELL, N, ORIGIN, PANEL, HUD_H
from engine.board import Board, BLACK, WHITE
from engine import ai as ai_mod

import assets as assets_mod
import audio as audio_mod
from ui.board_view import BoardView
from ui.char_view import CharPanel
from ui import hud


def selftest():
    for i in range(10):
        board = Board()
        color = BLACK
        winner = None
        while True:
            mv, _ = ai_mod.choose_move(board, color, 0.1, level=1)
            if mv is None:
                break
            r, c = mv
            assert board.place(r, c, color)
            if board.check_win(r, c, color):
                winner = color
                break
            if board.is_full():
                break
            color = 3 - color
        print(f"game {i:02d}: winner={winner} moves={len(board.history)}")
        assert winner or board.is_full()
    b = Board()
    for c in range(4):
        b.grid[7][c] = BLACK
        b.history.append((7, c, BLACK))
    mv, reason = ai_mod.choose_move(b, WHITE, 0, level=2)
    assert mv == (7, 4) and reason == "block", (mv, reason)
    b2 = Board()
    for c in range(4):
        b2.grid[7][c] = WHITE
        b2.history.append((7, c, WHITE))
    mv2, reason2 = ai_mod.choose_move(b2, WHITE, 0, level=2)
    assert mv2 == (7, 4) and reason2 == "win", (mv2, reason2)
    wins = 0
    for i in range(3):
        strong = BLACK if i % 2 == 0 else WHITE
        board = Board()
        color = BLACK
        winner = None
        while len(board.history) < 100:
            if color == strong:
                mv, _ = ai_mod.choose_move(board, color, 0, level=2, depth=3)
            else:
                mv, _ = ai_mod.choose_move(board, color, 0.5, level=1)
            r, c = mv
            assert board.place(r, c, color)
            if board.check_win(r, c, color):
                winner = color
                break
            color = 3 - color
        print(f"match {i}: strong={'B' if strong == BLACK else 'W'} winner={winner}")
        wins += winner == strong
    assert wins >= 2, f"level2 too weak: {wins}/3"
    print(f"selftest OK (level2 beat level1 {wins}/3)")


class Fade:
    def __init__(self):
        self.phase = "idle"
        self.alpha = 0.0
        self.callback = None

    def go(self, callback):
        self.phase = "out"
        self.callback = callback

    def update(self, dt):
        if self.phase == "idle":
            return
        if self.phase == "out":
            self.alpha = min(1.0, self.alpha + dt / 0.22)
            if self.alpha >= 1.0:
                cb, self.callback = self.callback, None
                if cb:
                    cb()
                self.phase = "in"
        elif self.phase == "in":
            self.alpha = max(0.0, self.alpha - dt / 0.22)
            if self.alpha <= 0.0:
                self.phase = "idle"

    def draw(self, surf):
        if self.alpha > 0:
            ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            ov.fill((8, 6, 10, int(255 * self.alpha)))
            surf.blit(ov, (0, 0))


class Game:
    def __init__(self):
        pygame.init()
        self.cfg = config.load_config()
        self.audio = audio_mod.AudioManager(
            config.ROOT,
            bgm_vol=self.cfg["bgm_volume"],
            se_vol=self.cfg["se_volume"],
            se_muted=self.cfg["se_muted"],
            bgm_muted=self.cfg["bgm_muted"],
        )
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("五目並べ - Gomoku")
        self.clock = pygame.time.Clock()
        self.fonts = {
            "title": assets_mod.resolve_font(72, bold=True),
            "big": assets_mod.resolve_font(44, bold=True),
            "mid": assets_mod.resolve_font(24),
            "small": assets_mod.resolve_font(18),
        }
        self.board_view = BoardView(ORIGIN, CELL, N)
        self.vignette = hud.vignette((W, H))
        self.fade = Fade()
        self.t = 0.0
        self.state = "title"
        self._new_character()
        self._reset_round_state()

    def _new_character(self):
        size = (PANEL[2] - 20, 372)
        self.char = assets_mod.load_character(config.ROOT, self.cfg["character"], size)
        self.panel = CharPanel(PANEL, self.char, self.fonts)

    BUTTON_SE = (PANEL[0] + 16, 556, 122, 30)
    BUTTON_RR = (PANEL[0] + 148, 556, 116, 30)

    def _reset_round_state(self):
        self.board = Board(N)
        self.pop = {}
        self.hover = None
        self.win_lines = None
        self.win_t = 0.0
        self.round_over = False
        self.result = None
        self.result_alpha = 0.0
        self.over_timer = 0.0
        self.think = 0.0
        self.turn = BLACK
        self.ai_color = WHITE if self.cfg["player_is_black"] else BLACK
        self.human_color = 3 - self.ai_color
        self.ai_moves = 0

    def start_round(self):
        self._reset_round_state()
        self.panel.set_state("normal")
        self.panel.say(self.char.line("start"))
        self.audio.play_bgm("bgm_battle")
        self.state = "play"
        if self.turn == self.ai_color:
            self.think = random.uniform(0.4, 0.8)

    def goto_title(self):
        self.state = "title"
        self.audio.play_bgm("bgm_title")

    def _place(self, r, c, color):
        self.board.place(r, c, color)
        self.pop[(r, c)] = self.t
        pitch = 1.0 if color == self.human_color else 0.88
        self.audio.play_se("se_place", pitch=pitch)
        win = self.board.check_win(r, c, color)
        if win:
            self._end_round("win" if color == self.human_color else "lose", win)
            return
        if self.board.is_full():
            self._end_round("draw", None)
            return
        self.turn = 3 - color

    def _end_round(self, result, win):
        self.round_over = True
        self.result = result
        self.win_lines = win
        self.over_timer = 0.0
        if result == "win":
            self.audio.play_se("se_win")
            self.audio.duck(0.25, 2.5)
            self.audio.play_jingle("bgm_win")
        elif result == "lose":
            self.audio.play_se("se_lose")
            self.audio.duck(0.25, 2.5)
            self.audio.play_jingle("bgm_lose")

    def _ai_turn(self):
        mv, reason = ai_mod.choose_move(
            self.board,
            self.ai_color,
            self.cfg["ai_noise"],
            level=self.cfg.get("ai_level", 2),
            depth=self.cfg.get("ai_depth", 5),
        )
        if mv is None:
            return
        r, c = mv
        self._place(r, c, self.ai_color)
        if self.round_over:
            return
        self.ai_moves += 1
        line = self.char.line(f"turn_{self.ai_moves}")
        if reason == "block" and random.random() < 0.6:
            self.panel.say(self.char.rand("danger"))
        elif line:
            self.panel.say(line)
        elif random.random() < 0.3:
            self.panel.say(self.char.rand("place"))

    def _human_click(self, pos):
        cell = self.board_view.cell_at(pos)
        if cell is None:
            return
        r, c = cell
        if self.board.get(r, c) != 0:
            return
        self._place(r, c, self.human_color)
        if not self.round_over and self.turn == self.ai_color:
            self.think = random.uniform(0.4, 0.8)

    def update(self, dt):
        self.t += dt
        self.fade.update(dt)
        self.audio.update(dt)
        self.panel.update(dt)
        if self.state != "play":
            return
        if self.round_over:
            self.win_t += dt
            self.over_timer += dt
            if self.over_timer >= 1.0 and self.result_alpha < 1.0:
                self.result_alpha = min(1.0, self.result_alpha + dt / 0.4)
                if self.result == "win":
                    self.panel.set_state("lose")
                    self.panel.say(self.char.rand("lose"))
                elif self.result == "lose":
                    self.panel.set_state("win")
                    self.panel.say(self.char.rand("win"))
                else:
                    self.panel.say(self.char.rand("draw"))
            return
        if self.turn == self.ai_color:
            self.think -= dt
            if self.think <= 0:
                self._ai_turn()

    def draw(self):
        if self.state == "title":
            hud.draw_title(self.screen, self.t, self.fonts, self.char, self.board_view.bg)
        else:
            self.screen.fill((24, 20, 26))
            mouse = pygame.mouse.get_pos()
            self.board_view.draw(
                self.screen,
                self.board,
                now=self.t,
                pop=self.pop,
                hover=None if self.round_over else self.hover,
                hover_color=None if self.round_over else self.human_color,
                win=self.win_lines,
                win_t=self.win_t,
            )
            self.panel.set_thinking(self.turn == self.ai_color and not self.round_over)
            self.panel.draw(self.screen)
            thinking = self.turn == self.ai_color and not self.round_over
            label = f"{self.char.name} が考え中…" if thinking else "あなたの番です"
            stone = self.ai_color if thinking else self.human_color
            hud.draw_hud(
                self.screen, (ORIGIN[0], ORIGIN[1], W - PANEL[2] - ORIGIN[0] * 2, HUD_H),
                label, stone, self.fonts,
            )
            se_txt = "♪ SE: OFF" if self.audio.se_muted else "♪ SE: ON"
            hud.draw_button(self.screen, self.BUTTON_SE, se_txt, self.fonts["small"],
                            pygame.Rect(self.BUTTON_SE).collidepoint(mouse))
            hud.draw_button(self.screen, self.BUTTON_RR, "再戦 (R)", self.fonts["small"],
                            pygame.Rect(self.BUTTON_RR).collidepoint(mouse))
            if self.round_over and self.result_alpha > 0:
                title = {"win": "あなたの勝ち!", "lose": f"{self.char.name} の勝ち…",
                         "draw": "引き分け"}[self.result]
                hud.draw_result(self.screen, self.fonts, title, self.result_alpha)
            self.screen.blit(self.vignette, (0, 0))
        self.fade.draw(self.screen)
        pygame.display.flip()

    def _quit(self):
        self.cfg["se_muted"] = self.audio.se_muted if self.audio.ok else self.cfg["se_muted"]
        self.cfg["bgm_muted"] = self.audio.bgm_muted if self.audio.ok else self.cfg["bgm_muted"]
        config.save_config(self.cfg)
        pygame.quit()
        sys.exit(0)

    def events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self._quit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.state in ("play",):
                        self.fade.go(self.goto_title)
                elif e.key == pygame.K_r:
                    if self.state == "play":
                        self.fade.go(self.start_round)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.state == "title":
                        self.fade.go(self.start_round)
                    elif self.state == "play" and self.round_over and self.result_alpha >= 1:
                        self.fade.go(self.goto_title)
                elif e.key == pygame.K_m:
                    self.audio.set_mute("se", not self.audio.se_muted)
                elif e.key == pygame.K_v:
                    self.audio.set_mute("bgm", not self.audio.bgm_muted)
            elif e.type == pygame.MOUSEMOTION:
                if self.state == "play" and not self.round_over:
                    self.hover = self.board_view.cell_at(e.pos)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._click(e.pos)

    def _click(self, pos):
        if self.state == "title":
            self.fade.go(self.start_round)
            return
        if self.state == "play":
            if pygame.Rect(self.BUTTON_SE).collidepoint(pos):
                self.audio.set_mute("se", not self.audio.se_muted)
                return
            if pygame.Rect(self.BUTTON_RR).collidepoint(pos):
                self.fade.go(self.start_round)
                return
            if self.round_over:
                if self.result_alpha >= 1.0:
                    self.fade.go(self.goto_title)
                return
            if self.turn == self.human_color and self.fade.phase == "idle":
                self._human_click(pos)

    def run(self):
        self.audio.play_bgm("bgm_title")
        while True:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self.events()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    Game().run()

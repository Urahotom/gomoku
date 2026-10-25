import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT, "config.json")

W, H = 960, 600
N = 15
CELL = 40
PANEL_W = 280
BOARD_PX = N * CELL
ORIGIN = ((W - PANEL_W - BOARD_PX) // 2, (H - BOARD_PX) // 2)
PANEL = (W - PANEL_W, 0, PANEL_W, H)

HUD_H = 44

DEFAULTS = {
    "character": "aoi",
    "bgm_volume": 0.5,
    "se_volume": 0.8,
    "player_is_black": True,
    "ai_noise": 0.15,
    "ai_level": 2,
    "ai_depth": 5,
    "se_muted": False,
    "bgm_muted": False,
}


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in DEFAULTS:
            if k in data:
                cfg[k] = data[k]
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

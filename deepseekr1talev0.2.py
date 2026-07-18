"""
deepseekr1 tale 0.1
An Undertale-inspired game built with pygame-ce.
"""

import pygame
import sys
import math
import random
import json
import os
from enum import Enum, auto

# ── Constants ────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 640, 480
FPS = 60

BLUE     = (60, 120, 255)
DARK_BLUE= (20, 40, 120)
BLACK    = (0, 0, 0)
WHITE    = (255, 255, 255)
RED      = (255, 50, 50)
YELLOW   = (255, 255, 100)
GREEN    = (80, 220, 80)
PURPLE   = (180, 80, 255)
CREAM    = (255, 244, 204)
LIGHT_BLUE = (100, 160, 255)

TILE_SIZE = 32

BLUE_HUE_SURF = None  # overlay for blue hue effect

# ── Helper ────────────────────────────────────────────────────────────────────
def load_img(path, scale=None):
    if not os.path.exists(path):
        surf = pygame.Surface((32, 32))
        surf.fill((255, 0, 255))
        return surf
    img = pygame.image.load(path).convert_alpha()
    if scale:
        img = pygame.transform.scale(img, scale)
    return img

def make_border_rect(surf, color=BLUE, width=4):
    pygame.draw.rect(surf, color, surf.get_rect(), width)

def blit_text(surf, text, pos, color=BLUE, size=24, align="topleft"):
    font = pygame.font.Font(None, size)
    img = font.render(text, True, color)
    rect = img.get_rect()
    setattr(rect, align, pos)
    surf.blit(img, rect)

def draws_box(surf, rect, color=BLUE, bg=BLACK, border=3):
    pygame.draw.rect(surf, bg, rect)
    pygame.draw.rect(surf, color, rect, border)

def text_wrap(text, font, max_width):
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        test = cur + " " + w if cur else w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ── Enums ──────────────────────────────────────────────────────────────────────
class GameState(Enum):
    MENU    = auto()
    OVERWORLD = auto()
    DIALOGUE  = auto()
    BATTLE    = auto()
    BATTLE_MENU = auto()
    BATTLE_ACT  = auto()
    BATTLE_ITEM = auto()
    BATTLE_MERCY = auto()
    BATTLE_FIGHT = auto()
    BATTLE_DIALOGUE = auto()
    PAUSE    = auto()
    GAME_OVER = auto()

# ── Keys ──────────────────────────────────────────────────────────────────────
CONFIRM_KEYS = (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE)
CANCEL_KEYS  = (pygame.K_x, pygame.K_ESCAPE)

# ── Room data ─────────────────────────────────────────────────────────────────
ROOMS = {}

# ── RUINS ──
ROOMS["flower_room"] = {
    "name": "Golden Flower Room",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14] + [(9, 7), (10, 7), (9, 8), (10, 8)],
    "exits": {"right": "hall2"},
    "npc": [{"type": "flowey", "pos": (10, 11), "name": "Flowey"}],
    "save_points": [],
    "player_start": (3, 7),
}

ROOMS["start"] = {
    "name": "The Ruins - Entrance",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"down": "hall1"},
    "npc": [],
    "save_points": [(10, 10)],
    "player_start": (10, 2),
}

ROOMS["hall1"] = {
    "name": "Long Hall",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "start", "down": "hall2"},
    "npc": [],
    "save_points": [],
    "player_start": (10, 2),
}

ROOMS["hall2"] = {
    "name": "Crossroads",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "hall1", "down": "ruins_main", "left": "flower_room", "right": "dark_hall"},
    "npc": [],
    "save_points": [(10, 7)],
    "player_start": (10, 2),
}

ROOMS["dark_hall"] = {
    "name": "Dark Hallway",
    "w": 15, "h": 15,
    "walls": [(x, y) for x in range(15) for y in range(15) if x == 0 or x == 14 or y == 0 or y == 14],
    "exits": {"left": "hall2"},
    "npc": [{"type": "whimsun", "pos": (7, 7), "name": "Whimsun"}],
    "save_points": [],
    "player_start": (12, 7),
}

ROOMS["ruins_main"] = {
    "name": "Ruins Main Hall",
    "w": 30, "h": 20,
    "walls": [(x, y) for x in range(30) for y in range(20) if x == 0 or x == 29 or y == 0 or y == 19],
    "exits": {"up": "hall2", "down": "toriel_house", "left": "puzzle_room"},
    "npc": [{"type": "froggit", "pos": (15, 15), "name": "Froggit"}],
    "save_points": [(10, 5)],
    "player_start": (15, 3),
}

ROOMS["puzzle_room"] = {
    "name": "Puzzle Room",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14] + [(5, y) for y in range(3, 12)] + [(14, y) for y in range(3, 12)],
    "exits": {"right": "ruins_main"},
    "npc": [],
    "save_points": [],
    "player_start": (3, 7),
}

ROOMS["toriel_house"] = {
    "name": "Toriel's Home",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14] +
             [(x, 7) for x in range(6, 14)] + [(6, 7), (13, 7)],
    "exits": {"up": "ruins_main", "down": "toriel_basement"},
    "npc": [{"type": "toriel", "pos": (10, 11), "name": "Toriel"}],
    "save_points": [(10, 3)],
    "player_start": (10, 4),
}

ROOMS["toriel_basement"] = {
    "name": "Toriel's Basement",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "toriel_house", "down": "ruins_exit"},
    "npc": [{"type": "toriel_boss", "pos": (10, 10), "name": "Toriel"}],
    "save_points": [(10, 13)],
    "player_start": (10, 3),
}

ROOMS["ruins_exit"] = {
    "name": "Ruins Exit",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "toriel_basement", "down": "snowdin_forest1"},
    "npc": [],
    "save_points": [(10, 3)],
    "player_start": (10, 12),
}

# ── SNOWDIN ──
ROOMS["snowdin_forest1"] = {
    "name": "Snowdin Forest - Entry",
    "w": 25, "h": 18,
    "walls": [(x, y) for x in range(25) for y in range(18) if x == 0 or x == 24 or y == 0 or y == 17],
    "exits": {"up": "ruins_exit", "down": "snowdin_forest2"},
    "npc": [],
    "save_points": [(12, 3)],
    "player_start": (12, 2),
}

ROOMS["snowdin_forest2"] = {
    "name": "Snowdin Forest - Doggo",
    "w": 25, "h": 18,
    "walls": [(x, y) for x in range(25) for y in range(18) if x == 0 or x == 24 or y == 0 or y == 17],
    "exits": {"up": "snowdin_forest1", "down": "snowdin_forest3"},
    "npc": [{"type": "doggo", "pos": (12, 9), "name": "Doggo"}],
    "save_points": [],
    "player_start": (12, 2),
}

ROOMS["snowdin_forest3"] = {
    "name": "Snowdin Forest - Crossing",
    "w": 25, "h": 18,
    "walls": [(x, y) for x in range(25) for y in range(18) if x == 0 or x == 24 or y == 0 or y == 17] +
             [(x, 9) for x in range(8, 18)],
    "exits": {"up": "snowdin_forest2", "down": "snowdin_forest4"},
    "npc": [{"type": "lesser_dog", "pos": (18, 13), "name": "Lesser Dog"}],
    "save_points": [],
    "player_start": (12, 2),
}

ROOMS["snowdin_forest4"] = {
    "name": "Snowdin Forest - Deep",
    "w": 25, "h": 18,
    "walls": [(x, y) for x in range(25) for y in range(18) if x == 0 or x == 24 or y == 0 or y == 17],
    "exits": {"up": "snowdin_forest3", "down": "snowdin_forest5"},
    "npc": [{"type": "greater_dog", "pos": (12, 9), "name": "Greater Dog"}],
    "save_points": [(12, 15)],
    "player_start": (12, 2),
}

ROOMS["snowdin_forest5"] = {
    "name": "Snowdin Forest - Edge",
    "w": 25, "h": 18,
    "walls": [(x, y) for x in range(25) for y in range(18) if x == 0 or x == 24 or y == 0 or y == 17],
    "exits": {"up": "snowdin_forest4", "down": "snowdin_town"},
    "npc": [],
    "save_points": [],
    "player_start": (12, 2),
}

ROOMS["snowdin_town"] = {
    "name": "Snowdin Town",
    "w": 30, "h": 22,
    "walls": [(x, y) for x in range(30) for y in range(22) if x == 0 or x == 29 or y == 0 or y == 21] +
             [(10, y) for y in range(7, 16)] + [(20, y) for y in range(7, 16)] +
             [(x, 7) for x in range(10, 21)] + [(x, 15) for x in range(10, 21)],
    "exits": {"up": "snowdin_forest5", "down": "snowdin_exit",
              "left": "snowdin_shop", "right": "sans_house"},
    "npc": [{"type": "sans", "pos": (15, 11), "name": "Sans"}],
    "save_points": [(15, 18)],
    "player_start": (15, 3),
}

ROOMS["snowdin_shop"] = {
    "name": "Snowdin Shop",
    "w": 12, "h": 10,
    "walls": [(x, y) for x in range(12) for y in range(10) if x == 0 or x == 11 or y == 0 or y == 9],
    "exits": {"right": "snowdin_town", "down": "grillbys"},
    "npc": [{"type": "shopkeep", "pos": (3, 5), "name": "Shopkeeper"}],
    "save_points": [],
    "player_start": (9, 5),
}

ROOMS["grillbys"] = {
    "name": "Grillby's",
    "w": 16, "h": 12,
    "walls": [(x, y) for x in range(16) for y in range(12) if x == 0 or x == 15 or y == 0 or y == 11] +
             [(x, 6) for x in range(4, 12)],
    "exits": {"up": "snowdin_shop"},
    "npc": [{"type": "grillby", "pos": (8, 4), "name": "Grillby"}],
    "save_points": [],
    "player_start": (8, 2),
}

ROOMS["librarby"] = {
    "name": "Librarby",
    "w": 14, "h": 12,
    "walls": [(x, y) for x in range(14) for y in range(12) if x == 0 or x == 13 or y == 0 or y == 11],
    "exits": {"right": "sans_house"},
    "npc": [{"type": "bratty", "pos": (7, 6), "name": "Bratty"}],
    "save_points": [],
    "player_start": (2, 6),
}

ROOMS["sans_house"] = {
    "name": "Sans & Papyrus's House",
    "w": 14, "h": 12,
    "walls": [(x, y) for x in range(14) for y in range(12) if x == 0 or x == 13 or y == 0 or y == 11] +
             [(x, 6) for x in range(4, 10)],
    "exits": {"left": "snowdin_town", "right": "librarby"},
    "npc": [{"type": "papyrus", "pos": (10, 8), "name": "Papyrus"}],
    "save_points": [],
    "player_start": (7, 9),
}

ROOMS["snowdin_exit"] = {
    "name": "Snowdin Town Gate",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "snowdin_town", "down": "waterfall_entrance"},
    "npc": [],
    "save_points": [(10, 3)],
    "player_start": (10, 12),
}

# ── WATERFALL ──
ROOMS["waterfall_entrance"] = {
    "name": "Waterfall Entrance",
    "w": 22, "h": 16,
    "walls": [(x, y) for x in range(22) for y in range(16) if x == 0 or x == 21 or y == 0 or y == 15],
    "exits": {"up": "snowdin_exit", "down": "waterfall_main"},
    "npc": [],
    "save_points": [(11, 3)],
    "player_start": (11, 2),
}

ROOMS["waterfall_main"] = {
    "name": "Waterfall - Main Path",
    "w": 30, "h": 22,
    "walls": [(x, y) for x in range(30) for y in range(22) if x == 0 or x == 29 or y == 0 or y == 21],
    "exits": {"up": "waterfall_entrance", "down": "waterfall_exit",
              "left": "temmie_village", "right": "napstablook_house"},
    "npc": [{"type": "onionsan", "pos": (15, 11), "name": "Onion-san"}],
    "save_points": [(15, 5)],
    "player_start": (15, 3),
}

ROOMS["temmie_village"] = {
    "name": "Temmie Village",
    "w": 16, "h": 12,
    "walls": [(x, y) for x in range(16) for y in range(12) if x == 0 or x == 15 or y == 0 or y == 11],
    "exits": {"right": "waterfall_main"},
    "npc": [{"type": "temmie", "pos": (8, 6), "name": "Temmie"}],
    "save_points": [],
    "player_start": (13, 6),
}

ROOMS["napstablook_house"] = {
    "name": "Napstablook's House",
    "w": 14, "h": 10,
    "walls": [(x, y) for x in range(14) for y in range(10) if x == 0 or x == 13 or y == 0 or y == 9],
    "exits": {"left": "waterfall_main"},
    "npc": [{"type": "napstablook_npc", "pos": (7, 5), "name": "Napstablook"}],
    "save_points": [],
    "player_start": (2, 5),
}

ROOMS["gerson_shop"] = {
    "name": "Gerson's Shop",
    "w": 12, "h": 10,
    "walls": [(x, y) for x in range(12) for y in range(10) if x == 0 or x == 11 or y == 0 or y == 9],
    "exits": {"up": "waterfall_main"},
    "npc": [{"type": "gerson", "pos": (3, 5), "name": "Gerson"}],
    "save_points": [],
    "player_start": (9, 5),
}

ROOMS["shyren_room"] = {
    "name": "Shyren's Room",
    "w": 14, "h": 10,
    "walls": [(x, y) for x in range(14) for y in range(10) if x == 0 or x == 13 or y == 0 or y == 9],
    "exits": {"up": "waterfall_main"},
    "npc": [{"type": "shyren", "pos": (7, 5), "name": "Shyren"}],
    "save_points": [],
    "player_start": (2, 5),
}

ROOMS["mad_dummy_room"] = {
    "name": "Mad Dummy Arena",
    "w": 18, "h": 14,
    "walls": [(x, y) for x in range(18) for y in range(14) if x == 0 or x == 17 or y == 0 or y == 13],
    "exits": {"down": "waterfall_main"},
    "npc": [{"type": "mad_dummy", "pos": (9, 7), "name": "Mad Dummy"}],
    "save_points": [],
    "player_start": (9, 11),
}

ROOMS["waterfall_exit"] = {
    "name": "Waterfall - End",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "waterfall_main", "down": "hotland_entrance"},
    "npc": [],
    "save_points": [(10, 3)],
    "player_start": (10, 12),
}

# ── HOTLAND ──
ROOMS["hotland_entrance"] = {
    "name": "Hotland Entrance",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "waterfall_exit", "down": "hotland_main"},
    "npc": [],
    "save_points": [(10, 3)],
    "player_start": (10, 2),
}

ROOMS["hotland_main"] = {
    "name": "Hotland - Main Area",
    "w": 28, "h": 20,
    "walls": [(x, y) for x in range(28) for y in range(20) if x == 0 or x == 27 or y == 0 or y == 19],
    "exits": {"up": "hotland_entrance", "down": "hotland_exit",
              "left": "cooking_show", "right": "lab_entrance"},
    "npc": [{"type": "mettaton", "pos": (14, 10), "name": "Mettaton"},
            {"type": "mettaton_quiz", "pos": (8, 16), "name": "Quiz Show"}],
    "save_points": [(14, 5)],
    "player_start": (14, 3),
}


ROOMS["lab_entrance"] = {
    "name": "Lab Entrance",
    "w": 16, "h": 12,
    "walls": [(x, y) for x in range(16) for y in range(12) if x == 0 or x == 15 or y == 0 or y == 11],
    "exits": {"left": "hotland_main", "down": "alphys_lab"},
    "npc": [],
    "save_points": [],
    "player_start": (3, 6),
}

ROOMS["alphys_lab"] = {
    "name": "Alphys's Lab",
    "w": 18, "h": 14,
    "walls": [(x, y) for x in range(18) for y in range(14) if x == 0 or x == 17 or y == 0 or y == 13] +
             [(x, 7) for x in range(4, 14)],
    "exits": {"up": "lab_entrance"},
    "npc": [{"type": "alphys", "pos": (9, 10), "name": "Alphys"}],
    "save_points": [],
    "player_start": (9, 5),
}

ROOMS["cooking_show"] = {
    "name": "Cooking Show",
    "w": 16, "h": 12,
    "walls": [(x, y) for x in range(16) for y in range(12) if x == 0 or x == 15 or y == 0 or y == 11],
    "exits": {"right": "hotland_main"},
    "npc": [{"type": "mettaton_cook", "pos": (8, 6), "name": "Mettaton"}],
    "save_points": [],
    "player_start": (2, 6),
}

ROOMS["hotland_exit"] = {
    "name": "Hotland - Core Entrance",
    "w": 20, "h": 15,
    "walls": [(x, y) for x in range(20) for y in range(15) if x == 0 or x == 19 or y == 0 or y == 14],
    "exits": {"up": "hotland_main", "down": "core_entrance"},
    "npc": [],
    "save_points": [(10, 3)],
    "player_start": (10, 12),
}

# ── CORE ──
ROOMS["core_entrance"] = {
    "name": "CORE - Entrance",
    "w": 22, "h": 16,
    "walls": [(x, y) for x in range(22) for y in range(16) if x == 0 or x == 21 or y == 0 or y == 15],
    "exits": {"up": "hotland_exit", "down": "core_main"},
    "npc": [],
    "save_points": [(11, 3)],
    "player_start": (11, 2),
}

ROOMS["core_main"] = {
    "name": "CORE - Main",
    "w": 24, "h": 18,
    "walls": [(x, y) for x in range(24) for y in range(18) if x == 0 or x == 23 or y == 0 or y == 17],
    "exits": {"up": "core_entrance", "down": "core_final"},
    "npc": [],
    "save_points": [(12, 5)],
    "player_start": (12, 3),
}

ROOMS["core_final"] = {
    "name": "CORE - Final",
    "w": 22, "h": 16,
    "walls": [(x, y) for x in range(22) for y in range(16) if x == 0 or x == 21 or y == 0 or y == 15],
    "exits": {"up": "core_main", "down": "new_home_entrance"},
    "npc": [{"type": "mettaton_ex", "pos": (11, 8), "name": "Mettaton EX"}],
    "save_points": [(11, 12)],
    "player_start": (11, 3),
}

# ── NEW HOME ──
ROOMS["new_home_entrance"] = {
    "name": "New Home - Entrance",
    "w": 22, "h": 16,
    "walls": [(x, y) for x in range(22) for y in range(16) if x == 0 or x == 21 or y == 0 or y == 15],
    "exits": {"up": "core_final", "down": "new_home_main"},
    "npc": [],
    "save_points": [(11, 3)],
    "player_start": (11, 2),
}

ROOMS["new_home_main"] = {
    "name": "New Home - Main Hall",
    "w": 26, "h": 18,
    "walls": [(x, y) for x in range(26) for y in range(18) if x == 0 or x == 25 or y == 0 or y == 17],
    "exits": {"up": "new_home_entrance", "down": "asgore_throne"},
    "npc": [],
    "save_points": [(13, 5)],
    "player_start": (13, 3),
}

ROOMS["asgore_throne"] = {
    "name": "Throne Room",
    "w": 22, "h": 16,
    "walls": [(x, y) for x in range(22) for y in range(16) if x == 0 or x == 21 or y == 0 or y == 15],
    "exits": {"up": "new_home_main", "down": "barrier"},
    "npc": [{"type": "asgore", "pos": (11, 5), "name": "Asgore"}],
    "save_points": [],
    "player_start": (11, 12),
}

ROOMS["barrier"] = {
    "name": "The Barrier",
    "w": 22, "h": 16,
    "walls": [(x, y) for x in range(22) for y in range(16) if x == 0 or x == 21 or y == 0 or y == 15],
    "exits": {"up": "asgore_throne"},
    "npc": [],
    "save_points": [],
    "player_start": (11, 12),
}

# ── Enemy Data ────────────────────────────────────────────────────────────────
ENEMIES = {
    "froggit": {
        "name": "Froggit",
        "hp": 20, "max_hp": 20, "atk": 4, "def": 1,
        "exp": 10, "gold": 5,
        "acts": ["Check", "Compliment", "Threaten"],
        "act_results": {
            "Check": "* Froggit, ATK 4 DEF 1\n* A peaceful monster.",
            "Compliment": "* Froggit blushes. Its ATK lowered!",
            "Threaten": "* Froggit trembles. Its DEF lowered!",
        },
        "talk_lines": ["ribbit...", "..."],
        "spareable_after": "Compliment",
        "bullets": ["simple", "simple", "simple"],
    },
    "whimsun": {
        "name": "Whimsun",
        "hp": 15, "max_hp": 15, "atk": 5, "def": 0,
        "exp": 12, "gold": 3,
        "acts": ["Check", "Terrorize", "Console"],
        "act_results": {
            "Check": "* Whimsun, ATK 5 DEF 0\n* A nervous monster.",
            "Terrorize": "* Whimsun cries! ATK lowered.",
            "Console": "* Whimsun feels better. It spares you!",
        },
        "talk_lines": ["...please don't hurt me...", "I'm scared..."],
        "spareable_after": "Console",
        "bullets": ["spiral", "spiral", "simple"],
    },
    "moldsmal": {
        "name": "Moldsmal",
        "hp": 18, "max_hp": 18, "atk": 6, "def": 2,
        "exp": 8, "gold": 2,
        "acts": ["Check", "Imitate", "Flirt"],
        "act_results": {
            "Check": "* Moldsmal, ATK 6 DEF 2\n* It's just sort of... sitting there.",
            "Imitate": "* You imitate Moldsmal. It feels understood!",
            "Flirt": "* Moldsmal wiggles. It seems pleased.",
        },
        "talk_lines": ["...", "......", ".........."],
        "spareable_after": "Imitate",
        "bullets": ["aimed", "aimed", "simple"],
    },
    "napstablook": {
        "name": "Napstablook",
        "hp": 30, "max_hp": 30, "atk": 8, "def": 0,
        "exp": 25, "gold": 10,
        "acts": ["Check", "Cheer", "Joke"],
        "act_results": {
            "Check": "* Napstablook, ATK 8 DEF 0\n* Very peculiar monster.",
            "Cheer": "* You tried to cheer up Napstablook.\n* It's not very effective...",
            "Joke": "* Napstablook smirks. It's too good to fight!",
        },
        "talk_lines": ["...oh... hi...", "i'm... blooky...", "...don't mind me..."],
        "spareable_after": "Joke",
        "bullets": ["tear", "tear", "spiral", "simple"],
    },
    "toriel_boss": {
        "name": "Toriel",
        "hp": 80, "max_hp": 80, "atk": 6, "def": 2,
        "exp": 150, "gold": 0,
        "acts": ["Check", "Talk", "Spare"],
        "act_results": {
            "Check": "* Toriel, ATK 6 DEF 2\n* Knows best for you.",
            "Talk": "* You try to talk to Toriel.\n* She listens intently.",
            "Spare": "* You plead with Toriel.\n* Her grip loosens...",
        },
        "talk_lines": ["My child...", "This is for your own good.", "Please, stay here."],
        "spareable_after": "Spare",
        "bullets": ["toriel_fire", "toriel_fire", "toriel_fire", "simple"],
    },
    "doggo": {
        "name": "Doggo",
        "hp": 25, "max_hp": 25, "atk": 5, "def": 1,
        "exp": 15, "gold": 8,
        "acts": ["Check", "Pet", "Threaten"],
        "act_results": {
            "Check": "* Doggo, ATK 5 DEF 1\n* Can't see you if you don't move.",
            "Pet": "* Doggo wags its tail! It's distracted!",
            "Threaten": "* Doggo growls. It's ready to fight!",
        },
        "talk_lines": ["...did something move?", "i can't see you if you don't move...", "..."],
        "spareable_after": "Pet",
        "bullets": ["simple", "simple", "aimed"],
    },
    "lesser_dog": {
        "name": "Lesser Dog",
        "hp": 30, "max_hp": 30, "atk": 6, "def": 2,
        "exp": 18, "gold": 10,
        "acts": ["Check", "Pet", "Play"],
        "act_results": {
            "Check": "* Lesser Dog, ATK 6 DEF 2\n* Likes to be petted.",
            "Pet": "* You pet Lesser Dog.\n* Its neck gets longer!",
            "Play": "* Lesser Dog barks happily!",
        },
        "talk_lines": ["woof!", "...", "bark!"],
        "spareable_after": "Pet",
        "bullets": ["simple", "aimed", "simple"],
    },
    "greater_dog": {
        "name": "Greater Dog",
        "hp": 40, "max_hp": 40, "atk": 8, "def": 3,
        "exp": 25, "gold": 15,
        "acts": ["Check", "Pet", "Annoy"],
        "act_results": {
            "Check": "* Greater Dog, ATK 8 DEF 2\n* A good dog.",
            "Pet": "* Greater Dog rolls over for belly rubs!",
            "Annoy": "* Greater Dog barks loudly! ATK up!",
        },
        "talk_lines": ["BOW WOW!", "WOOF!", "...wag wag..."],
        "spareable_after": "Pet",
        "bullets": ["aimed", "aimed", "spiral", "simple"],
    },
    "mad_dummy": {
        "name": "Mad Dummy",
        "hp": 50, "max_hp": 50, "atk": 10, "def": 1,
        "exp": 40, "gold": 0,
        "acts": ["Check", "Talk", "Joke"],
        "act_results": {
            "Check": "* Mad Dummy, ATK 10 DEF 1\n* Hates being called a dummy.",
            "Talk": "* You try to reason with the dummy.\n* It's not listening.",
            "Joke": "* You tell a knock-knock joke.\n* Mad Dummy is furious!",
        },
        "talk_lines": ["HOW DARE YOU!", "I'LL SHOW YOU!", "DON'T CALL ME A DUMMY!"],
        "spareable_after": "Talk",
        "bullets": ["aimed", "spiral", "aimed", "spiral"],
    },
    "mettaton_ex": {
        "name": "Mettaton EX",
        "hp": 100, "max_hp": 100, "atk": 14, "def": 4,
        "exp": 200, "gold": 100,
        "acts": ["Check", "Pose", "Compliment"],
        "act_results": {
            "Check": "* Mettaton EX, ATK 14 DEF 4\n* A beautiful star.",
            "Pose": "* You strike a pose!\n* Mettaton is impressed!",
            "Compliment": "* You compliment Mettaton's style.",
        },
        "talk_lines": ["OH YES!", "DARLING!", "THE SHOW MUST GO ON!"],
        "spareable_after": "Pose",
        "bullets": ["spiral", "toriel_fire", "spiral", "aimed"],
    },
    "asgore": {
        "name": "Asgore Dreemurr",
        "hp": 120, "max_hp": 120, "atk": 16, "def": 5,
        "exp": 0, "gold": 0,
        "acts": ["Check", "Talk", "Hope"],
        "act_results": {
            "Check": "* Asgore Dreemurr, ATK 16 DEF 5\n* King of the Underground.",
            "Talk": "* You try to talk to Asgore.\n* He listens...",
            "Hope": "* You tell Asgore about your hope.\n* Something stirs in his heart.",
        },
        "talk_lines": ["Human...", "I do not wish to fight you.", "Please, understand."],
        "spareable_after": "Hope",
        "bullets": ["toriel_fire", "spiral", "aimed", "toriel_fire"],
    },
}

# ── Bullet Patterns ───────────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, vx, vy, size=6, color=WHITE, pattern="simple"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.pattern = pattern
        self.alive = True
        self.timer = 0

    def update(self):
        self.timer += 1
        if self.pattern == "simple":
            self.x += self.vx
            self.y += self.vy
        elif self.pattern == "sin":
            self.x += self.vx
            self.y += self.vy + math.sin(self.timer * 0.1) * 2
        elif self.pattern == "aimed":
            self.x += self.vx
            self.y += self.vy
        elif self.pattern == "spiral":
            angle = self.timer * 0.1
            self.x += self.vx + math.cos(angle) * 1.5
            self.y += self.vy + math.sin(angle) * 1.5
        elif self.pattern == "tear":
            self.x += self.vx
            self.y += self.vy
            self.size = max(2, self.size - 0.05)
        elif self.pattern == "toriel_fire":
            # Drift outward with a slight wobble (was missing: fire never moved)
            self.x += self.vx + math.sin(self.timer * 0.15) * 0.5
            self.y += self.vy + math.cos(self.timer * 0.12) * 0.5
        else:
            self.x += self.vx
            self.y += self.vy

        margin = 80
        if (self.x < -margin or self.x > SCREEN_W + margin or
            self.y < -margin or self.y > SCREEN_H + margin):
            self.alive = False

    def draw(self, surf, offset_x=0, offset_y=0):
        if not self.alive:
            return
        cx = int(self.x) + offset_x
        cy = int(self.y) + offset_y
        if self.pattern == "tear":
            pygame.draw.ellipse(surf, self.color, (cx - self.size, cy - self.size * 1.5, self.size * 2, self.size * 3))
        elif self.pattern == "toriel_fire":
            flicker = random.randint(-2, 2)
            sz = self.size + flicker
            pygame.draw.circle(surf, (255, 150, 50), (cx, cy), int(sz))
            pygame.draw.circle(surf, (255, 200, 100), (cx, cy), int(sz * 0.6))
        else:
            pygame.draw.circle(surf, self.color, (cx, cy), int(self.size))

    def rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)


# ── Player Data ────────────────────────────────────────────────────────────────
class PlayerData:
    def __init__(self):
        self.name = "FRISK"
        self.lv = 1
        self.hp = 20
        self.max_hp = 20
        self.atk = 10
        self.def_ = 10
        self.exp = 0
        self.next_exp = 20
        self.gold = 0
        self.weapon = "Stick"
        self.armor = "Bandage"
        self.items = ["Butterscotch Pie", "Monster Candy"]
        self.item_counts = {"Butterscotch Pie": 1, "Monster Candy": 2}
        self.heal_items = {"Butterscotch Pie": 30, "Monster Candy": 10}
        self.save_points = []
        self.encountered_enemies = []
        self.spared_enemies = []
        self.killed_enemies = []
        self.flowey_met = False
        self.toriel_met = False
        self.toriel_spared = False
        self.pacifist = True

    def add_exp(self, amt):
        self.exp += amt
        while self.exp >= self.next_exp:
            self.lv += 1
            self.exp -= self.next_exp
            self.next_exp = int(self.next_exp * 1.5)
            self.max_hp += 4
            self.hp = self.max_hp
            self.atk += 2
            self.def_ += 1

    def add_gold(self, amt):
        self.gold += amt

    def heal(self, amt):
        self.hp = min(self.max_hp, self.hp + amt)

    def use_item(self, item_name):
        if item_name in self.items and self.item_counts.get(item_name, 0) > 0:
            heal_amt = self.heal_items.get(item_name, 10)
            old_hp = self.hp
            self.heal(heal_amt)
            actual = self.hp - old_hp
            self.item_counts[item_name] -= 1
            if self.item_counts[item_name] <= 0:
                self.items.remove(item_name)
            return actual
        return -1


# ── Game ───────────────────────────────────────────────────────────────────────
class DeepSeekTale:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("deepseekr1 tale 0.1")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True

        global BLUE_HUE_SURF
        BLUE_HUE_SURF = pygame.Surface((SCREEN_W, SCREEN_H))
        BLUE_HUE_SURF.fill(BLUE)
        BLUE_HUE_SURF.set_alpha(15)

        self.state = GameState.MENU
        self.player = PlayerData()

        # Menu
        self.menu_selection = 0
        self.menu_options = ["START", "CONTINUE", "RESET"]
        self.menu_timer = 0
        self.menu_title_y = -50

        # Overworld
        self.room_name = "start"
        self.px = 10 * TILE_SIZE
        self.py = 2 * TILE_SIZE
        self.p_speed = 3
        self.p_dir = "down"
        self.p_moving = False
        self.facing_enemy = False
        self.enemy_encounter_timer = 0
        self.overworld_timer = 0
        self.near_save = False

        # Pause
        self.pause_message = ""
        self.pause_msg_timer = 0

        # Dialogue
        self.dialogue_queue = []
        self.dialogue_index = 0
        self.dialogue_char_index = 0
        self.dialogue_speed = 2
        self.dialogue_timer = 0
        self.dialogue_finished = False
        self.dialogue_show_arrow = False
        self.dialogue_box_rect = pygame.Rect(20, SCREEN_H - 150, SCREEN_W - 40, 130)
        self.dialogue_is_battle = False

        # Battle
        self.battle_enemy = None
        self.enemy_data = None
        self.soul_x = SCREEN_W // 2
        self.soul_y = SCREEN_H // 2 + 40
        self.soul_vx = 0
        self.soul_vy = 0
        self.soul_size = 8
        self.battle_box = pygame.Rect(0, 0, 0, 0)
        self.bullets = []
        self.battle_timer = 0
        self.battle_phase = "intro"
        self.battle_phase_timer = 0
        self.battle_menu_selection = 0
        self.battle_menu_options = ["FIGHT", "ACT", "ITEM", "MERCY"]
        self.battle_act_selection = 0
        self.battle_act_options = []
        self.battle_item_selection = 0
        self.battle_mercy_selection = 0
        self.battle_mercy_options = ["Spare", "Flee"]
        self.battle_text = ""
        self.battle_text_timer = 0
        self.battle_text_queue = []
        self.fight_power = 0
        self.fight_charge_dir = 1
        self.fight_zone = None
        self.fight_bonus = 0
        self.enemy_hp = 0
        self.enemy_max_hp = 0
        self.spare_progress = 0
        self.spare_threshold = 3
        self.battle_act_count = 0
        self.battle_defeated = False
        self.battle_spared = False
        self.turn_count = 0
        self.bullet_spawn_timer = 0
        self.battle_attack_phase = False
        self.battle_player_turn = True
        self.battle_flee_attempts = 0
        self.battle_message_active = False
        self.battle_message_lines = []
        self.battle_message_index = 0
        self.battle_action_taken = False
        self.battle_fled = False
        self.pending_battle = None
        self.soul_flash_timer = 0
        self.fight_timer = 0
        self.game_over_timer = 0

        # Sound (simple beeps)
        self._init_sound()

        # Font
        self.font_small = pygame.font.Font(None, 20)
        self.font_med = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 48)
        self.font_title = pygame.font.Font(None, 72)

        # Start game
        self._load_game()
        self._enter_room(self.room_name, self.px, self.py)

    def _init_sound(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.sounds = {}
            for name, freq, dur in [
                ("confirm", 440, 0.1),
                ("cursor", 220, 0.05),
                ("hurt", 100, 0.15),
                ("heal", 523, 0.3),
                ("levelup", 660, 0.4),
                ("battle", 330, 0.2),
                ("enemy_damage", 550, 0.1),
                ("spare", 880, 0.3),
            ]:
                self.sounds[name] = self._make_beep(freq, dur)
        except Exception:
            self.sounds = {}

    def _make_beep(self, freq, duration):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        try:
            import numpy as np
            # Mono buffer as (n, 1) int16 — required by pygame-ce sndarray
            t = np.arange(n_samples, dtype=np.float32) / sample_rate
            wave = (0.3 * 32767 * np.sin(2 * np.pi * freq * t)).astype(np.int16)
            arr = wave.reshape(-1, 1)
            return pygame.sndarray.make_sound(arr)
        except Exception:
            class DummySound:
                def play(self, *a, **kw): pass
            return DummySound()

    def _play_sound(self, name):
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

    def _save_game(self):
        data = {
            "name": self.player.name,
            "lv": self.player.lv,
            "hp": self.player.hp,
            "max_hp": self.player.max_hp,
            "atk": self.player.atk,
            "def_": self.player.def_,
            "exp": self.player.exp,
            "next_exp": self.player.next_exp,
            "gold": self.player.gold,
            "weapon": self.player.weapon,
            "armor": self.player.armor,
            "items": self.player.items,
            "item_counts": self.player.item_counts,
            "room": self.room_name,
            "px": self.px,
            "py": self.py,
            "flowey_met": self.player.flowey_met,
            "toriel_met": self.player.toriel_met,
            "toriel_spared": self.player.toriel_spared,
            "pacifist": self.player.pacifist,
            "encountered_enemies": self.player.encountered_enemies,
            "spared_enemies": self.player.spared_enemies,
            "killed_enemies": self.player.killed_enemies,
        }
        try:
            with open("deeptale_save.json", "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_game(self):
        player_keys = {
            "name", "lv", "hp", "max_hp", "atk", "def_", "exp", "next_exp",
            "gold", "weapon", "armor", "items", "item_counts",
            "flowey_met", "toriel_met", "toriel_spared", "pacifist",
            "encountered_enemies", "spared_enemies", "killed_enemies",
        }
        try:
            with open("deeptale_save.json") as f:
                data = json.load(f)
            for k, v in data.items():
                if k in player_keys:
                    setattr(self.player, k, v)
            self.room_name = data.get("room", "start")
            self.px = data.get("px", 10 * TILE_SIZE)
            self.py = data.get("py", 2 * TILE_SIZE)
            # Never load into a dead state
            if self.player.hp <= 0:
                self.player.hp = self.player.max_hp
            return True
        except Exception:
            return False

    def _enter_room(self, room_name, px=None, py=None):
        if room_name not in ROOMS:
            room_name = "start"
        self.room_name = room_name
        room = ROOMS[room_name]
        if px is not None and py is not None:
            self.px = px
            self.py = py
        else:
            self.px = room["player_start"][0] * TILE_SIZE
            self.py = room["player_start"][1] * TILE_SIZE
        self.facing_enemy = False
        self.enemy_encounter_timer = 0

    def _clamp_room_position(self, room_name, px, py):
        room = ROOMS.get(room_name, ROOMS["start"])
        px = max(TILE_SIZE, min(px, (room["w"] - 2) * TILE_SIZE))
        py = max(TILE_SIZE, min(py, (room["h"] - 2) * TILE_SIZE))
        return px, py

    def _try_room_exit(self, room, new_x, new_y, dx, dy):
        if dx == 0 and dy == 0:
            return False

        exits = room["exits"]
        if dy < 0 and "up" in exits and new_y < TILE_SIZE:
            target = exits["up"]
            if target not in ROOMS: return False
            px, py = self._clamp_room_position(target, new_x, (ROOMS[target]["h"] - 2) * TILE_SIZE)
            self._enter_room(target, px, py)
            return True
        if dy > 0 and "down" in exits and new_y + TILE_SIZE > (room["h"] - 1) * TILE_SIZE:
            target = exits["down"]
            if target not in ROOMS: return False
            px, py = self._clamp_room_position(target, new_x, TILE_SIZE)
            self._enter_room(target, px, py)
            return True
        if dx < 0 and "left" in exits and new_x < TILE_SIZE:
            target = exits["left"]
            if target not in ROOMS: return False
            px, py = self._clamp_room_position(target, (ROOMS[target]["w"] - 2) * TILE_SIZE, new_y)
            self._enter_room(target, px, py)
            return True
        if dx > 0 and "right" in exits and new_x + TILE_SIZE > (room["w"] - 1) * TILE_SIZE:
            target = exits["right"]
            if target not in ROOMS: return False
            px, py = self._clamp_room_position(target, TILE_SIZE, new_y)
            self._enter_room(target, px, py)
            return True

        return False

    def _set_state(self, state):
        self.state = state

    # ── MENU ──────────────────────────────────────────────────────────────────
    def _update_menu(self):
        self.menu_timer += 1
        if self.menu_title_y < SCREEN_H // 3:
            self.menu_title_y += 2

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                    self._play_sound("cursor")
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                    self._play_sound("cursor")
                elif e.key in CONFIRM_KEYS:
                    self._play_sound("confirm")
                    sel = self.menu_options[self.menu_selection]
                    if sel == "START":
                        self.player = PlayerData()
                        self.room_name = "flower_room"
                        self._enter_room("flower_room")
                        self._set_state(GameState.OVERWORLD)
                        self.dialogue_queue = [
                            "* ...Where... am I?",
                            "* You're in the Underground.",
                            "* A land of monsters.",
                            "* Use the arrow keys to move.",
                            "* Press Z or Enter to confirm.",
                        ]
                        self._start_dialogue()
                    elif sel == "CONTINUE":
                        if self._load_game():
                            self._enter_room(self.room_name, self.px, self.py)
                            self._set_state(GameState.OVERWORLD)
                        else:
                            # No save file — start a fresh run instead of hanging
                            self.player = PlayerData()
                            self._enter_room("flower_room")
                            self._set_state(GameState.OVERWORLD)
                    elif sel == "RESET":
                        self.player = PlayerData()
                        self.room_name = "start"
                        self._enter_room("start")
                        try:
                            os.remove("deeptale_save.json")
                        except Exception:
                            pass

    def _draw_menu(self):
        self.screen.fill(BLACK)

        title_y = int(self.menu_title_y)
        title_surf = self.font_title.render("deepseekr1 tale", True, BLUE)
        title_rect = title_surf.get_rect(center=(SCREEN_W // 2, title_y))
        self.screen.blit(title_surf, title_rect)

        sub_surf = self.font_large.render("0.1", True, LIGHT_BLUE)
        sub_rect = sub_surf.get_rect(center=(SCREEN_W // 2, title_y + 60))
        self.screen.blit(sub_surf, sub_rect)

        heart_y = title_y + 100 + math.sin(self.menu_timer * 0.05) * 5
        self._draw_heart(SCREEN_W // 2, int(heart_y), BLUE)

        for i, opt in enumerate(self.menu_options):
            y = SCREEN_H // 2 + i * 50
            color = LIGHT_BLUE if i != self.menu_selection else BLUE
            if i == self.menu_selection:
                self._draw_heart(SCREEN_W // 2 - 80, y, BLUE)
            opt_surf = self.font_large.render(opt, True, color)
            opt_rect = opt_surf.get_rect(center=(SCREEN_W // 2, y))
            self.screen.blit(opt_surf, opt_rect)

        blink = (self.menu_timer // 30) % 2 == 0
        if blink:
            blit_text(self.screen, "[Press Z or Enter]", (SCREEN_W // 2, SCREEN_H - 40),
                      LIGHT_BLUE, 20, "center")

    # ── OVERWORLD ─────────────────────────────────────────────────────────────
    def _get_room(self):
        return ROOMS.get(self.room_name, ROOMS["start"])

    def _update_overworld(self):
        self.overworld_timer += 1
        room = self._get_room()
        keys = pygame.key.get_pressed()

        # Process events once
        z_pressed = False
        esc_pressed = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in CONFIRM_KEYS:
                    z_pressed = True
                if e.key in CANCEL_KEYS:
                    esc_pressed = True

        # ESC -> pause
        if esc_pressed:
            self._set_state(GameState.PAUSE)
            return

        dx = dy = 0
        self.p_moving = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.p_speed; self.p_dir = "left"; self.p_moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.p_speed; self.p_dir = "right"; self.p_moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.p_speed; self.p_dir = "up"; self.p_moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.p_speed; self.p_dir = "down"; self.p_moving = True

        new_x = self.px + dx
        new_y = self.py + dy

        if self._try_room_exit(room, new_x, new_y, dx, dy):
            return

        # Axis-separated collision so you can slide along walls
        walls = room["walls"]

        def collides(x, y):
            tx1 = x // TILE_SIZE
            ty1 = y // TILE_SIZE
            tx2 = (x + TILE_SIZE - 1) // TILE_SIZE
            ty2 = (y + TILE_SIZE - 1) // TILE_SIZE
            for tx in range(tx1, tx2 + 1):
                for ty in range(ty1, ty2 + 1):
                    if (tx, ty) in walls:
                        return True
            return False

        if not collides(new_x, self.py):
            self.px = new_x
        if not collides(self.px, new_y):
            self.py = new_y

        # Boundaries (keep within walkable area, 1 tile from walls)
        self.px = max(TILE_SIZE, min(self.px, (room["w"] - 2) * TILE_SIZE))
        self.py = max(TILE_SIZE, min(self.py, (room["h"] - 2) * TILE_SIZE))

        # NPC interactions (don't clear facing when checking later NPCs)
        self.facing_enemy = False
        nearest_npc = None
        nearest_dist = 999
        for npc in room["npc"]:
            nx, ny = npc["pos"]
            dist = abs(self.px // TILE_SIZE - nx) + abs(self.py // TILE_SIZE - ny)
            if dist <= 2 and dist < nearest_dist:
                self.facing_enemy = True
                nearest_npc = npc
                nearest_dist = dist
        if nearest_npc is not None and z_pressed:
            self._interact_npc(nearest_npc)
            return

        # Save point interaction
        self.near_save = False
        for sp in room.get("save_points", []):
            sx, sy = sp
            dist = abs(self.px // TILE_SIZE - sx) + abs(self.py // TILE_SIZE - sy)
            if dist <= 1:
                self.near_save = True
                if z_pressed:
                    self._save_game()
                    self.dialogue_queue = ["* Game saved!", f"* {self.player.name} - LV {self.player.lv}", f"* HP: {self.player.hp}/{self.player.max_hp}"]
                    self._start_dialogue()
                    return
                break

        # Random encounters
        encounter_rooms_no = ("start", "flower_room", "toriel_house", "toriel_basement",
                              "snowdin_town", "snowdin_shop", "grillbys", "librarby", "sans_house",
                              "temmie_village", "napstablook_house", "gerson_shop", "shyren_room",
                              "mad_dummy_room", "mettaton_quiz", "lab_entrance", "alphys_lab",
                              "cooking_show", "asgore_throne", "barrier")
        area_enemies = {
            "dark_hall": ["whimsun"],
            "ruins_main": ["froggit", "moldsmal"],
            "puzzle_room": ["moldsmal", "froggit"],
            "snowdin_forest1": ["doggo"],
            "snowdin_forest2": ["doggo"],
            "snowdin_forest3": ["lesser_dog"],
            "snowdin_forest4": ["greater_dog"],
            "snowdin_forest5": ["greater_dog", "doggo"],
            "waterfall_main": ["whimsun", "moldsmal"],
            "waterfall_entrance": ["whimsun"],
            "waterfall_exit": ["whimsun", "moldsmal"],
            "hotland_main": ["moldsmal", "froggit"],
            "hotland_entrance": ["froggit"],
            "core_main": ["moldsmal"],
            "core_final": ["moldsmal", "whimsun"],
            "new_home_main": ["whimsun"],
            "new_home_entrance": ["whimsun", "moldsmal"],
        }
        if self.p_moving and self.room_name not in encounter_rooms_no:
            self.enemy_encounter_timer += 1
            enems = area_enemies.get(self.room_name, ["froggit", "whimsun", "moldsmal"])
            if self.enemy_encounter_timer > random.randint(60, 180):
                self._start_battle(random.choice(enems))
                return
        else:
            self.enemy_encounter_timer = max(0, self.enemy_encounter_timer - 1)

    def _interact_npc(self, npc):
        npc_type = npc.get("type", "")
        if npc_type == "flowey" and not self.player.flowey_met:
            self.player.flowey_met = True
            self.dialogue_queue = [
                "* Howdy! I'm FLOWEY!",
                "* FLOWEY the FLOWER!",
                "* Welcome to the UNDERGROUND!",
                "* You must be new here.",
                "* Let me show you how things work!",
                "* ...",
                "* Actually, I'll let you explore.",
                "* Be careful down here!",
                "* Hee hee hee...",
            ]
            self._start_dialogue()
        elif npc_type == "toriel":
            if not self.player.toriel_met:
                self.player.toriel_met = True
                self.dialogue_queue = [
                    "* Hello, my child.",
                    "* I am TORIEL, caretaker of the RUINS.",
                    "* Are you lost?",
                    "* ...",
                    "* You must be tired.",
                    "* Come with me, I'll take care of you.",
                ]
                self._start_dialogue()
            else:
                self.dialogue_queue = [
                    "* Hello again, my child.",
                    "* Would you like some butterscotch pie?",
                    "* I'll save a slice for you.",
                ]
                self._start_dialogue()
        elif npc_type == "toriel_boss":
            self.dialogue_queue = [
                "* Toriel stands before you.",
                "* She doesn't want to hurt you.",
                "* But she won't let you leave the Ruins.",
            ]
            self._start_dialogue_then_battle("toriel_boss")
        elif npc_type == "froggit":
            self.dialogue_queue = [
                "* Froggit: Ribbit...",
                "* Froggit hops around you curiously.",
                "* It seems friendly.",
            ]
            self._start_dialogue_then_battle("froggit")
        elif npc_type == "whimsun":
            self.dialogue_queue = [
                "* Whimsun: ...oh! A human!",
                "* Whimsun looks nervous.",
            ]
            self._start_dialogue_then_battle("whimsun")
        elif npc_type == "doggo":
            self.dialogue_queue = [
                "* Doggo: ...did something move?",
                "* Doggo sniffs the air.",
            ]
            self._start_dialogue_then_battle("doggo")
        elif npc_type == "lesser_dog":
            self.dialogue_queue = [
                "* Lesser Dog wags its tail.",
                "* It looks like it wants to play!",
            ]
            self._start_dialogue_then_battle("lesser_dog")
        elif npc_type == "greater_dog":
            self.dialogue_queue = [
                "* A massive dog blocks your path!",
                "* Greater Dog: WOOF!",
            ]
            self._start_dialogue_then_battle("greater_dog")
        elif npc_type == "mad_dummy":
            self.dialogue_queue = [
                "* Mad Dummy: HOW DARE YOU!",
                "* The dummy attacks!",
            ]
            self._start_dialogue_then_battle("mad_dummy")
        elif npc_type == "napstablook_npc":
            self.dialogue_queue = [
                "* Napstablook: ...oh... hi...",
                "* Napstablook: ...do you need something?",
                "* ...",
                "* Napstablook stares at the floor.",
            ]
            self._start_dialogue()
        elif npc_type == "shyren":
            self.dialogue_queue = [
                "* Shyren: ...",
                "* Shyren hides behind her hair.",
                "* She seems too shy to fight.",
            ]
            self._start_dialogue_then_battle("moldsmal")
        elif npc_type == "sans":
            self.dialogue_queue = [
                "* Sans: hey there, kid.",
                "* Sans: i'm sans. sans the skeleton.",
                "* Sans: you're a human, right?",
                "* Sans: ...",
                "* Sans: heh. just don't cause any trouble.",
                "* Sans: my brother papyrus is the local skeleton.",
                "* Sans: maybe you'll run into him!",
            ]
            self._start_dialogue()
        elif npc_type == "papyrus":
            self.dialogue_queue = [
                "* Papyrus: HUMAN!",
                "* Papyrus: YOU HAVE ENTERED THE GREAT PAPYRUS'S HOME!",
                "* Papyrus: I WOULD CHALLENGE YOU...",
                "* Papyrus: BUT SANS SAYS I NEED TO CLEAN MY ROOM FIRST.",
                "* Papyrus: NYEH HEH HEH!",
            ]
            self._start_dialogue()
        elif npc_type == "shopkeep":
            self.dialogue_queue = [
                "* Welcome to Snowdin Shop!",
                "* Feel free to browse.",
                "* Unfortunately, the shop is closed for display purposes.",
            ]
            self._start_dialogue()
        elif npc_type == "grillby":
            self.dialogue_queue = [
                "* Grillby stands behind the counter.",
                "* The fire elemental nods at you silently.",
                "* The bar is warm and inviting.",
            ]
            self._start_dialogue()
        elif npc_type == "bratty":
            self.dialogue_queue = [
                "* Bratty: ...what are you looking at?",
                "* Bratty: never seen a monster before?",
            ]
            self._start_dialogue()
        elif npc_type == "onionsan":
            self.dialogue_queue = [
                "* Onion-san: ...h ...hello!",
                "* Onion-san: Do you like... water?",
                "* Onion-san: I love water!",
                "* Onion-san: ...bye!",
            ]
            self._start_dialogue()
        elif npc_type == "temmie":
            self.dialogue_queue = [
                "* temmie: hOI!!",
                "* temmie: im temmie!",
                "* temmie: welcome to temmie village!",
                "* temmie: ...tem flake?",
            ]
            self._start_dialogue()
        elif npc_type == "gerson":
            self.dialogue_queue = [
                "* Gerson: WELL, WELL! A CUSTOMER!",
                "* Gerson: THE NAME'S GERSON!",
                "* Gerson: I'VE SEEN A LOT IN MY DAYS!",
                "* Gerson: HAHAHA!",
            ]
            self._start_dialogue()
        elif npc_type == "mettaton":
            self.dialogue_queue = [
                "* Mettaton: OHHH YES!",
                "* Mettaton: WELCOME TO HOTLAND!",
                "* Mettaton: I'M METTATON, THE MOST GLAMOROUS ROBOT!",
                "* Mettaton: ENJOY YOUR STAY, DARLING!",
            ]
            self._start_dialogue()
        elif npc_type == "mettaton_quiz":
            self.dialogue_queue = [
                "* Mettaton: WELCOME TO MY QUIZ SHOW!",
                "* Mettaton: PREPARE FOR FABULOUS CHALLENGES!",
                "* Mettaton: ...but first, the set isn't ready.",
                "* Mettaton: COME BACK LATER, DARLING!",
            ]
            self._start_dialogue()
        elif npc_type == "mettaton_cook":
            self.dialogue_queue = [
                "* Mettaton: WELCOME TO COOKING WITH METTATON!",
                "* Mettaton: TODAY WE'LL BE MAKING...",
                "* Mettaton: A FABULOUS DISH!",
                "* Mettaton: ...IF I HAD ANY INGREDIENTS!",
                "* Mettaton: HOW EMBARRASSING!",
            ]
            self._start_dialogue()
        elif npc_type == "mettaton_ex":
            self.dialogue_queue = [
                "* Mettaton: SO, WE MEET AGAIN!",
                "* Mettaton: THIS IS MY FINAL FORM!",
                "* Mettaton: METTATON EX!",
                "* Mettaton: PREPARE FOR THE FINALE!",
            ]
            self._start_dialogue_then_battle("mettaton_ex")
        elif npc_type == "alphys":
            self.dialogue_queue = [
                "* Alphys: Oh! H-h-hi!",
                "* Alphys: I'm Dr. Alphys!",
                "* Alphys: The Royal Scientist!",
                "* Alphys: ...if you need anything, just ask!",
            ]
            self._start_dialogue()
        elif npc_type == "asgore":
            self.dialogue_queue = [
                "* Asgore Dreemurr stands before you.",
                "* The King of the Underground.",
                "* He holds his trident.",
                "* ...there is sadness in his eyes.",
            ]
            self._start_dialogue_then_battle("asgore")

    def _draw_overworld(self):
        self.screen.fill(BLACK)

        room = self._get_room()
        room_pw = room["w"] * TILE_SIZE
        room_ph = room["h"] * TILE_SIZE
        if room_pw <= SCREEN_W:
            cam_x = -(SCREEN_W - room_pw) // 2
        else:
            cam_x = max(0, min(self.px - SCREEN_W // 2, room_pw - SCREEN_W))
        if room_ph <= SCREEN_H:
            cam_y = -(SCREEN_H - room_ph) // 2
        else:
            cam_y = max(0, min(self.py - SCREEN_H // 2, room_ph - SCREEN_H))

        for x in range(room["w"]):
            for y in range(room["h"]):
                rx = x * TILE_SIZE - cam_x
                ry = y * TILE_SIZE - cam_y
                if -TILE_SIZE < rx < SCREEN_W + TILE_SIZE and -TILE_SIZE < ry < SCREEN_H + TILE_SIZE:
                    if (x, y) in room["walls"]:
                        pygame.draw.rect(self.screen, (10, 10, 15), (rx, ry, TILE_SIZE, TILE_SIZE))
                        pygame.draw.rect(self.screen, (20, 20, 30), (rx, ry, TILE_SIZE, TILE_SIZE), 1)
                    else:
                        pygame.draw.rect(self.screen, (5, 5, 10), (rx, ry, TILE_SIZE, TILE_SIZE))

        for x in range(room["w"]):
            for y in range(room["h"]):
                rx = x * TILE_SIZE - cam_x
                ry = y * TILE_SIZE - cam_y
                if -TILE_SIZE < rx < SCREEN_W + TILE_SIZE and -TILE_SIZE < ry < SCREEN_H + TILE_SIZE:
                    pygame.draw.rect(self.screen, (10, 10, 18), (rx, ry, TILE_SIZE, TILE_SIZE), 1)

        # Exits indicators
        for direction in room["exits"]:
            ex, ey = SCREEN_W // 2, SCREEN_H // 2
            if direction == "up": ey = 5
            elif direction == "down": ey = SCREEN_H - 5
            elif direction == "left": ex = 5
            elif direction == "right": ex = SCREEN_W - 5
            pygame.draw.circle(self.screen, DARK_BLUE, (ex, ey), 8)

        # NPCs
        for npc in room["npc"]:
            nx = npc["pos"][0] * TILE_SIZE - cam_x + TILE_SIZE // 2
            ny = npc["pos"][1] * TILE_SIZE - cam_y + TILE_SIZE // 2
            if -TILE_SIZE < nx < SCREEN_W + TILE_SIZE and -TILE_SIZE < ny < SCREEN_H + TILE_SIZE:
                self._draw_npc(npc, nx, ny)

        # Save points
        for sp in room.get("save_points", []):
            sx = sp[0] * TILE_SIZE - cam_x + TILE_SIZE // 2
            sy = sp[1] * TILE_SIZE - cam_y + TILE_SIZE // 2
            if -TILE_SIZE < sx < SCREEN_W + TILE_SIZE and -TILE_SIZE < sy < SCREEN_H + TILE_SIZE:
                self._draw_save_point(sx, sy)

        # Player
        sx = self.px - cam_x + TILE_SIZE // 2
        sy = self.py - cam_y + TILE_SIZE // 2
        self._draw_player(sx, sy)

        # NPC interaction prompt
        if self.facing_enemy:
            blit_text(self.screen, "[Press Z to interact]",
                      (SCREEN_W // 2, SCREEN_H - 20), LIGHT_BLUE, 14, "center")

        # Save point prompt (Undertale style - bottom center)
        if self.near_save:
            blink = (self.overworld_timer // 30) % 2 == 0
            if blink:
                blit_text(self.screen, "[SAVE - Press Z]",
                          (SCREEN_W // 2, SCREEN_H - 20), GREEN, 14, "center")

    def _draw_player(self, x, y):
        body_color = BLUE if random.random() > 0.03 else WHITE  # subtle flicker
        # Body
        pygame.draw.rect(self.screen, body_color, (x - 8, y - 6, 16, 16), 2)
        # Head
        pygame.draw.circle(self.screen, body_color, (x, y - 10), 6, 2)
        # Eyes
        eye_off = 2
        pygame.draw.circle(self.screen, WHITE, (x - eye_off, y - 12), 2)
        pygame.draw.circle(self.screen, WHITE, (x + eye_off, y - 12), 2)
        # Strip (Frisk's striped shirt)
        pygame.draw.line(self.screen, body_color, (x, y - 2), (x, y + 6), 2)

    def _draw_heart(self, x, y, color=BLUE, size=8):
        # Simple heart shape
        points = []
        for a in range(0, 360, 10):
            rad = math.radians(a)
            hx = size * 16 * (math.sin(rad) ** 3)
            hy = size * (-13 * math.cos(rad) + 5 * math.cos(2 * rad) + 2 * math.cos(3 * rad) + math.cos(4 * rad))
            points.append((x + hx * 0.1, y + hy * 0.1))
        if len(points) > 2:
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, WHITE, points, 1)

    def _draw_npc(self, npc, x, y):
        ntype = npc.get("type", "")
        if ntype == "flowey":
            pygame.draw.circle(self.screen, (255, 200, 0), (x, y - 8), 10)
            pygame.draw.circle(self.screen, (200, 150, 0), (x, y - 8), 10, 2)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                px = x + math.cos(rad) * 12
                py = y - 8 + math.sin(rad) * 12
                pygame.draw.circle(self.screen, (255, 100, 100), (int(px), int(py)), 5)
            pygame.draw.circle(self.screen, BLACK, (x - 3, y - 10), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 3, y - 10), 2)
            pygame.draw.circle(self.screen, WHITE, (x - 3, y - 10), 1)
            pygame.draw.circle(self.screen, WHITE, (x + 3, y - 10), 1)
            pygame.draw.arc(self.screen, BLACK, (x - 4, y - 6, 8, 6), 0, math.pi, 2)

        elif ntype in ("toriel", "toriel_boss"):
            pygame.draw.circle(self.screen, (200, 150, 200), (x, y - 12), 12)
            pygame.draw.rect(self.screen, (150, 100, 150), (x - 10, y, 20, 20))
            pygame.draw.circle(self.screen, (200, 150, 200), (x - 10, y - 16), 5)
            pygame.draw.circle(self.screen, (200, 150, 200), (x + 10, y - 16), 5)
            pygame.draw.circle(self.screen, BLACK, (x - 4, y - 14), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 4, y - 14), 2)

        elif ntype in ("froggit", "whimsun"):
            color_map = {"froggit": (80, 200, 80), "whimsun": (200, 180, 255)}
            c = color_map.get(ntype, (100, 100, 100))
            pygame.draw.circle(self.screen, c, (x, y - 4), 12)
            pygame.draw.circle(self.screen, c, (x, y + 6), 10)
            pygame.draw.circle(self.screen, WHITE, (x - 4, y - 6), 4)
            pygame.draw.circle(self.screen, WHITE, (x + 4, y - 6), 4)
            pygame.draw.circle(self.screen, BLACK, (x - 4, y - 6), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 4, y - 6), 2)

        elif ntype in ("doggo", "lesser_dog", "greater_dog"):
            color_map = {"doggo": (180, 140, 100), "lesser_dog": (160, 120, 80), "greater_dog": (200, 160, 120)}
            c = color_map.get(ntype, (150, 120, 90))
            pygame.draw.ellipse(self.screen, c, (x - 12, y - 8, 24, 16))
            pygame.draw.circle(self.screen, c, (x - 10, y - 12), 8)
            pygame.draw.circle(self.screen, c, (x + 10, y - 12), 8)
            pygame.draw.circle(self.screen, BLACK, (x - 12, y - 13), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 8, y - 13), 2)
            pygame.draw.ellipse(self.screen, BLACK, (x - 3, y - 3, 6, 4))

        elif ntype == "sans":
            pygame.draw.circle(self.screen, (255, 255, 200), (x, y - 6), 10)
            pygame.draw.circle(self.screen, BLACK, (x - 4, y - 8), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 4, y - 8), 2)
            pygame.draw.circle(self.screen, WHITE, (x - 4, y - 8), 1)
            pygame.draw.circle(self.screen, WHITE, (x + 4, y - 8), 1)
            pygame.draw.arc(self.screen, BLACK, (x - 4, y - 4, 8, 5), 0, math.pi, 2)
            pygame.draw.rect(self.screen, (100, 100, 200), (x - 8, y + 4, 16, 14))
            pygame.draw.rect(self.screen, (50, 50, 100), (x - 8, y + 4, 16, 14), 2)

        elif ntype == "papyrus":
            pygame.draw.rect(self.screen, (255, 255, 200), (x - 8, y - 14, 16, 28))
            pygame.draw.circle(self.screen, (255, 255, 200), (x, y - 14), 10)
            pygame.draw.circle(self.screen, WHITE, (x - 4, y - 16), 3)
            pygame.draw.circle(self.screen, WHITE, (x + 4, y - 16), 3)
            pygame.draw.circle(self.screen, BLACK, (x - 4, y - 16), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 4, y - 16), 2)
            pygame.draw.rect(self.screen, (200, 100, 100), (x - 3, y + 8, 6, 6))
            pygame.draw.rect(self.screen, (50, 50, 100), (x - 8, y - 14, 16, 28), 2)

        elif ntype == "shopkeep":
            pygame.draw.rect(self.screen, (150, 100, 80), (x - 10, y - 8, 20, 20))
            pygame.draw.circle(self.screen, (200, 180, 150), (x, y - 12), 8)
            pygame.draw.circle(self.screen, BLACK, (x - 3, y - 13), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 3, y - 13), 2)

        elif ntype == "grillby":
            pygame.draw.circle(self.screen, (255, 200, 50), (x, y - 4), 12)
            for i in range(5):
                off = random.randint(-4, 4)
                pygame.draw.circle(self.screen, (255, 150, 50), (x + off - 6, y - 14 + i * 3), 4)
            pygame.draw.circle(self.screen, (255, 255, 200), (x - 3, y - 6), 2)
            pygame.draw.circle(self.screen, (255, 255, 200), (x + 3, y - 6), 2)

        elif ntype == "bratty":
            pygame.draw.circle(self.screen, (200, 100, 150), (x, y - 8), 8)
            pygame.draw.rect(self.screen, (180, 80, 130), (x - 8, y, 16, 16))
            pygame.draw.circle(self.screen, BLACK, (x - 3, y - 10), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 3, y - 10), 2)

        elif ntype == "napstablook_npc":
            pygame.draw.ellipse(self.screen, (150, 150, 180), (x - 12, y - 4, 24, 16))
            pygame.draw.circle(self.screen, (180, 180, 200), (x, y - 6), 12)
            pygame.draw.circle(self.screen, BLACK, (x - 4, y - 8), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 4, y - 8), 2)

        elif ntype == "shyren":
            pygame.draw.circle(self.screen, (180, 160, 200), (x, y - 6), 10)
            pygame.draw.rect(self.screen, (160, 140, 180), (x - 10, y + 2, 20, 16))
            pygame.draw.rect(self.screen, (120, 100, 140), (x - 12, y - 2, 8, 14))
            pygame.draw.rect(self.screen, (120, 100, 140), (x + 4, y - 2, 8, 14))
            pygame.draw.circle(self.screen, BLACK, (x - 3, y - 8), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 3, y - 8), 2)

        elif ntype == "temmie":
            pygame.draw.ellipse(self.screen, (180, 120, 80), (x - 10, y - 6, 20, 16))
            pygame.draw.circle(self.screen, (200, 150, 100), (x, y - 10), 8)
            pygame.draw.circle(self.screen, BLACK, (x - 3, y - 12), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 3, y - 12), 2)
            pygame.draw.arc(self.screen, BLACK, (x - 4, y - 8, 8, 6), 0, math.pi, 2)

        elif ntype == "onionsan":
            pygame.draw.circle(self.screen, (100, 150, 255), (x, y - 4), 14)
            pygame.draw.circle(self.screen, (50, 100, 200), (x, y - 4), 14, 2)
            pygame.draw.circle(self.screen, BLACK, (x - 4, y - 6), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 4, y - 6), 2)
            pygame.draw.arc(self.screen, BLACK, (x - 4, y - 2, 8, 5), 0, math.pi, 2)

        elif ntype == "gerson":
            pygame.draw.circle(self.screen, (100, 180, 100), (x, y - 10), 12)
            pygame.draw.rect(self.screen, (80, 150, 80), (x - 10, y, 20, 18))
            pygame.draw.circle(self.screen, BLACK, (x - 4, y - 12), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 4, y - 12), 2)
            pygame.draw.rect(self.screen, (60, 120, 60), (x - 12, y + 4, 24, 6))

        elif ntype in ("mettaton", "mettaton_quiz", "mettaton_cook", "mettaton_ex"):
            pygame.draw.rect(self.screen, (200, 200, 220), (x - 10, y - 14, 20, 28))
            pygame.draw.circle(self.screen, (220, 220, 240), (x, y - 16), 10)
            pygame.draw.circle(self.screen, RED, (x - 4, y - 18), 3)
            pygame.draw.circle(self.screen, RED, (x + 4, y - 18), 3)
            pygame.draw.rect(self.screen, (100, 100, 120), (x - 12, y + 14, 6, 10))
            pygame.draw.rect(self.screen, (100, 100, 120), (x + 6, y + 14, 6, 10))

        elif ntype == "alphys":
            pygame.draw.circle(self.screen, (180, 120, 80), (x, y - 10), 10)
            pygame.draw.rect(self.screen, (200, 100, 150), (x - 8, y, 16, 18))
            pygame.draw.circle(self.screen, (100, 80, 60), (x - 5, y - 12), 3)
            pygame.draw.circle(self.screen, (100, 80, 60), (x + 5, y - 12), 3)
            pygame.draw.circle(self.screen, BLACK, (x - 5, y - 12), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 5, y - 12), 2)

        elif ntype == "asgore":
            pygame.draw.circle(self.screen, (200, 150, 200), (x, y - 14), 14)
            pygame.draw.rect(self.screen, (150, 50, 50), (x - 12, y, 24, 22))
            pygame.draw.circle(self.screen, BLACK, (x - 5, y - 16), 2)
            pygame.draw.circle(self.screen, BLACK, (x + 5, y - 16), 2)
            pygame.draw.circle(self.screen, WHITE, (x - 5, y - 16), 1)
            pygame.draw.circle(self.screen, WHITE, (x + 5, y - 16), 1)
            # Crown
            pygame.draw.polygon(self.screen, (255, 215, 0), [(x - 8, y - 22), (x, y - 28), (x + 8, y - 22)])
            pygame.draw.rect(self.screen, (255, 215, 0), (x - 10, y - 22, 20, 4))

        else:
            pygame.draw.circle(self.screen, (100, 100, 150), (x, y), 10)
            pygame.draw.circle(self.screen, BLUE, (x, y), 10, 2)

    def _draw_save_point(self, x, y):
        glow = abs(math.sin(self.overworld_timer * 0.05)) * 20 + 5
        pygame.draw.circle(self.screen, (255, 255, 100), (x, y + 8), int(glow + 4))
        # Star shape
        pts = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = 10 if i % 2 == 0 else 5
            pts.append((x + r * math.cos(angle), y + 8 + r * math.sin(angle)))
        pygame.draw.polygon(self.screen, (255, 255, 200), pts)
        pygame.draw.polygon(self.screen, (255, 255, 255), pts, 1)

    # ── DIALOGUE ──────────────────────────────────────────────────────────────
    def _start_dialogue(self, queue=None):
        if queue:
            self.dialogue_queue = queue
        self.dialogue_index = 0
        self.dialogue_char_index = 0
        self.dialogue_timer = 0
        self.dialogue_finished = False
        self.dialogue_show_arrow = False
        self.dialogue_is_battle = (self.state in (
            GameState.BATTLE, GameState.BATTLE_DIALOGUE, GameState.BATTLE_MENU,
            GameState.BATTLE_FIGHT, GameState.BATTLE_ACT, GameState.BATTLE_ITEM,
            GameState.BATTLE_MERCY,
        ))
        self._set_state(GameState.DIALOGUE)

    def _start_dialogue_then_battle(self, enemy_id):
        """Show pre-fight dialogue, then enter battle when the queue finishes."""
        self.pending_battle = enemy_id
        self._start_dialogue()

    def _update_dialogue(self):
        if self.dialogue_index >= len(self.dialogue_queue):
            self._end_dialogue()
            return

        full_line = self.dialogue_queue[self.dialogue_index]
        self.dialogue_timer += 1
        if self.dialogue_timer % self.dialogue_speed == 0:
            if self.dialogue_char_index < len(full_line):
                self.dialogue_char_index += 1

        if self.dialogue_char_index >= len(full_line):
            self.dialogue_finished = True
            self.dialogue_show_arrow = (self.dialogue_timer // 30) % 2 == 0

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in CONFIRM_KEYS:
                    if self.dialogue_finished:
                        self.dialogue_index += 1
                        self.dialogue_char_index = 0
                        self.dialogue_timer = 0
                        self.dialogue_finished = False
                        self._play_sound("cursor")
                    else:
                        self.dialogue_char_index = len(full_line)

    def _end_dialogue(self):
        # Pre-battle intro dialogue → start the fight
        if self.pending_battle:
            enemy_id = self.pending_battle
            self.pending_battle = None
            self._start_battle(enemy_id)
            return

        if self.dialogue_is_battle or self.battle_defeated or self.battle_spared:
            if self.battle_defeated or self.battle_spared:
                self._end_battle()
            else:
                self.state = GameState.BATTLE
                self.battle_player_turn = True
        else:
            self._set_state(GameState.OVERWORLD)

    def _draw_dialogue(self):
        self.screen.fill(BLACK)

        if self.dialogue_is_battle:
            self._draw_battle_background()
        else:
            self._draw_overworld_raw()

        draws_box(self.screen, self.dialogue_box_rect, BLUE, BLACK, 3)

        inner = self.dialogue_box_rect.inflate(-6, -6)
        pygame.draw.rect(self.screen, (10, 10, 30), inner)
        pygame.draw.rect(self.screen, (20, 20, 50), inner, 1)

        if self.dialogue_index < len(self.dialogue_queue):
            full_line = self.dialogue_queue[self.dialogue_index]
            display_text = full_line[:self.dialogue_char_index]
            lines = text_wrap(display_text, self.font_med, self.dialogue_box_rect.w - 30)
            for i, line in enumerate(lines):
                y = self.dialogue_box_rect.y + 15 + i * 30
                blit_text(self.screen, line, (self.dialogue_box_rect.x + 15, y), BLUE, 24)

        name_rect = pygame.Rect(self.dialogue_box_rect.x + 10, self.dialogue_box_rect.y - 12, 70, 22)
        draws_box(self.screen, name_rect, BLUE, BLACK, 2)
        blit_text(self.screen, "*", (name_rect.x + 6, name_rect.y + 3), BLUE, 16)

        if self.dialogue_show_arrow:
            ax = self.dialogue_box_rect.right - 24
            ay = self.dialogue_box_rect.bottom - 24
            self._draw_heart(ax, ay, WHITE, 4)

    def _draw_overworld_raw(self):
        room = self._get_room()
        room_pw = room["w"] * TILE_SIZE
        room_ph = room["h"] * TILE_SIZE
        if room_pw <= SCREEN_W:
            cam_x = -(SCREEN_W - room_pw) // 2
        else:
            cam_x = max(0, min(self.px - SCREEN_W // 2, room_pw - SCREEN_W))
        if room_ph <= SCREEN_H:
            cam_y = -(SCREEN_H - room_ph) // 2
        else:
            cam_y = max(0, min(self.py - SCREEN_H // 2, room_ph - SCREEN_H))
        for x in range(room["w"]):
            for y in range(room["h"]):
                rx = x * TILE_SIZE - cam_x
                ry = y * TILE_SIZE - cam_y
                if -TILE_SIZE < rx < SCREEN_W + TILE_SIZE and -TILE_SIZE < ry < SCREEN_H + TILE_SIZE:
                    if (x, y) in room["walls"]:
                        pygame.draw.rect(self.screen, (10, 10, 15), (rx, ry, TILE_SIZE, TILE_SIZE))
                        pygame.draw.rect(self.screen, (20, 20, 30), (rx, ry, TILE_SIZE, TILE_SIZE), 1)
                    else:
                        pygame.draw.rect(self.screen, (5, 5, 10), (rx, ry, TILE_SIZE, TILE_SIZE))
        for x in range(room["w"]):
            for y in range(room["h"]):
                rx = x * TILE_SIZE - cam_x
                ry = y * TILE_SIZE - cam_y
                if -TILE_SIZE < rx < SCREEN_W + TILE_SIZE and -TILE_SIZE < ry < SCREEN_H + TILE_SIZE:
                    pygame.draw.rect(self.screen, (10, 10, 18), (rx, ry, TILE_SIZE, TILE_SIZE), 1)
        for npc in room["npc"]:
            nx = npc["pos"][0] * TILE_SIZE - cam_x + TILE_SIZE // 2
            ny = npc["pos"][1] * TILE_SIZE - cam_y + TILE_SIZE // 2
            if -TILE_SIZE < nx < SCREEN_W + TILE_SIZE and -TILE_SIZE < ny < SCREEN_H + TILE_SIZE:
                self._draw_npc(npc, nx, ny)
        for sp in room.get("save_points", []):
            sx = sp[0] * TILE_SIZE - cam_x + TILE_SIZE // 2
            sy = sp[1] * TILE_SIZE - cam_y + TILE_SIZE // 2
            if -TILE_SIZE < sx < SCREEN_W + TILE_SIZE and -TILE_SIZE < sy < SCREEN_H + TILE_SIZE:
                self._draw_save_point(sx, sy)
        sx = self.px - cam_x + TILE_SIZE // 2
        sy = self.py - cam_y + TILE_SIZE // 2
        self._draw_player(sx, sy)

    # ── BATTLE ────────────────────────────────────────────────────────────────
    def _start_battle(self, enemy_id):
        if enemy_id not in ENEMIES:
            return
        self.state = GameState.BATTLE
        self.battle_enemy = enemy_id
        self.enemy_data = ENEMIES[enemy_id]
        self.enemy_hp = self.enemy_data["hp"]
        self.enemy_max_hp = self.enemy_data["max_hp"]
        self.battle_timer = 0
        self.battle_phase = "intro"
        self.battle_phase_timer = 0
        self.bullets = []
        self.battle_text = ""
        self.battle_text_timer = 0
        self.battle_text_queue = []
        self.battle_menu_selection = 0
        self.battle_act_options = self.enemy_data.get("acts", ["Check"])
        self.battle_act_selection = 0
        self.battle_item_selection = 0
        self.battle_mercy_selection = 0
        self.spare_progress = 0
        self.spare_threshold = 3
        self.battle_act_count = 0
        self.battle_defeated = False
        self.battle_spared = False
        self.turn_count = 0
        self.bullet_spawn_timer = 0
        self.battle_attack_phase = False
        self.battle_player_turn = True
        self.battle_flee_attempts = 0
        self.battle_message_active = False
        self.battle_message_lines = []
        self.battle_message_index = 0
        self.battle_action_taken = False
        self.battle_fled = False
        self.soul_flash_timer = 0
        self.soul_x = SCREEN_W // 2
        self.soul_y = SCREEN_H // 2 + 40
        # Keep soul inside the box from the start
        self.battle_box = pygame.Rect(SCREEN_W // 2 - 80, SCREEN_H // 2 - 60, 160, 120)
        self.soul_x = self.battle_box.centerx
        self.soul_y = self.battle_box.centery

        self._play_sound("battle")

    def _update_battle(self):
        self.battle_timer += 1
        if self.soul_flash_timer > 0:
            self.soul_flash_timer -= 1

        # Always pump events so quit works during intro / transitions
        if self.battle_phase == "intro":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
            self.battle_phase_timer += 1
            if self.battle_phase_timer > 60:
                self.battle_phase = "menu"
                self.battle_player_turn = True
            return

        # Handle battle message display (wait for Z to continue)
        if self.battle_message_active:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key in CONFIRM_KEYS:
                    self.battle_message_active = False
                    self._play_sound("cursor")
                    if self.battle_defeated or self.battle_spared or self.battle_fled:
                        self._end_battle()
                    elif self.battle_action_taken:
                        # Real action completed → enemy turn
                        self.battle_action_taken = False
                        self.battle_player_turn = False
                        self.battle_attack_phase = False
                    else:
                        # Info-only message (e.g. empty inventory) — stay on player turn
                        self.battle_player_turn = True
                        self.battle_phase = "menu"
            return

        # Enemy action phase (attack)
        if not self.battle_player_turn and not self.battle_attack_phase and self.battle_phase != "intro":
            self._start_enemy_turn()

        if self.battle_attack_phase:
            self._update_attack_phase()
            self._update_soul()

        # Check for menu input
        if self.battle_player_turn and self.battle_phase not in ("intro", "attack", "fight"):
            self._update_battle_menu()

    def _update_soul(self):
        keys = pygame.key.get_pressed()
        speed = 3.5
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = speed
        self.soul_x += dx
        self.soul_y += dy
        self.soul_x = max(self.battle_box.left + self.soul_size,
                          min(self.battle_box.right - self.soul_size, self.soul_x))
        self.soul_y = max(self.battle_box.top + self.soul_size,
                          min(self.battle_box.bottom - self.soul_size, self.soul_y))

    def _end_attack_phase(self):
        self.battle_attack_phase = False
        self.battle_player_turn = True
        self.battle_phase = "menu"
        self.bullets = []
        self.turn_count += 1

    def _spawn_attack(self, patterns):
        pattern = random.choice(patterns) if patterns else "simple"
        cx, cy = self.battle_box.center
        if pattern == "simple":
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                self.bullets.append(Bullet(cx, cy, math.cos(rad) * 3, math.sin(rad) * 3,
                                           5, WHITE, "simple"))
        elif pattern == "spiral":
            for i in range(12):
                angle = math.radians(i * 30 + self.turn_count * 15)
                self.bullets.append(Bullet(cx, cy, math.cos(angle) * 2.5, math.sin(angle) * 2.5,
                                           5, (200, 100, 255), "spiral"))
        elif pattern == "aimed":
            angle = math.atan2(self.soul_y - cy, self.soul_x - cx)
            for spread in (-0.2, 0, 0.2):
                a = angle + spread
                self.bullets.append(Bullet(cx, cy, math.cos(a) * 4, math.sin(a) * 4,
                                           6, (255, 200, 100), "simple"))
        elif pattern == "tear":
            for i in range(5):
                self.bullets.append(Bullet(
                    cx + random.randint(-60, 60), cy + random.randint(-40, 40),
                    random.uniform(-2, 2), random.uniform(-2, 2),
                    8, (150, 150, 255), "tear"))
        elif pattern == "toriel_fire":
            for i in range(8):
                angle = math.radians(i * 45 + self.turn_count * 10)
                self.bullets.append(Bullet(cx, cy, math.cos(angle) * 2, math.sin(angle) * 2,
                                           10, (255, 150, 50), "toriel_fire"))
        else:
            # Unknown pattern — fall back to simple ring
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                self.bullets.append(Bullet(cx, cy, math.cos(rad) * 3, math.sin(rad) * 3,
                                           5, WHITE, "simple"))

    def _update_attack_phase(self):
        # Pump quit / cancel events (menu input is disabled during attack)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False

        # Advance timer every frame (was stuck at 1 → attack never ended)
        self.bullet_spawn_timer += 1

        # Continuous bullet spawning for the first ~2 seconds
        if (len(self.bullets) < 30 and self.bullet_spawn_timer % 10 == 0
                and self.bullet_spawn_timer < 120 and self.bullet_spawn_timer > 1):
            patterns = self.enemy_data.get("bullets", ["simple"]) if self.enemy_data else ["simple"]
            pattern = random.choice(patterns)
            cx, cy = self.battle_box.center
            if pattern == "simple":
                angle = random.uniform(0, 2 * math.pi)
                self.bullets.append(Bullet(cx, cy, math.cos(angle) * 3, math.sin(angle) * 3,
                                           4, WHITE, "simple"))
            elif pattern == "aimed":
                angle = math.atan2(self.soul_y - cy, self.soul_x - cx)
                self.bullets.append(Bullet(cx, cy, math.cos(angle) * 4, math.sin(angle) * 4,
                                           5, (255, 200, 100), "simple"))
            elif pattern == "spiral":
                angle = math.radians(self.bullet_spawn_timer * 12)
                self.bullets.append(Bullet(cx, cy, math.cos(angle) * 2.5, math.sin(angle) * 2.5,
                                           5, (200, 100, 255), "spiral"))
            elif pattern == "tear":
                self.bullets.append(Bullet(
                    cx + random.randint(-50, 50), cy + random.randint(-30, 30),
                    random.uniform(-2, 2), random.uniform(-2, 2),
                    7, (150, 150, 255), "tear"))
            elif pattern == "toriel_fire":
                angle = random.uniform(0, 2 * math.pi)
                self.bullets.append(Bullet(cx, cy, math.cos(angle) * 2.2, math.sin(angle) * 2.2,
                                           9, (255, 150, 50), "toriel_fire"))

        for b in self.bullets[:]:
            b.update()
            if not b.alive:
                self.bullets.remove(b)

        # Hit detection
        for b in self.bullets[:]:
            dist = math.hypot(self.soul_x - b.x, self.soul_y - b.y)
            if dist < self.soul_size + b.size:
                self._player_hit()
                if b in self.bullets:
                    self.bullets.remove(b)

        # End attack when spawn window is over and bullets are gone, or hard timeout
        if (self.bullet_spawn_timer > 120 and len(self.bullets) == 0) or self.bullet_spawn_timer > 240:
            self._end_attack_phase()

    def _player_hit(self):
        if not self.battle_attack_phase:
            return
        # Brief i-frames so one bullet cloud does not instantly kill
        if self.soul_flash_timer > 0:
            return
        atk = self.enemy_data.get("atk", 5) if self.enemy_data else 5
        damage = max(1, atk - self.player.def_ // 2)
        damage = max(1, random.randint(damage - 1, damage + 2))
        self.player.hp -= damage
        self._play_sound("hurt")
        self.soul_flash_timer = 30
        if self.player.hp <= 0:
            self.player.hp = 0
            self._game_over()

    def _game_over(self):
        self._set_state(GameState.GAME_OVER)
        self.game_over_timer = 0

    def _update_battle_menu(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in CANCEL_KEYS:
                    if self.battle_phase == "act":
                        self.battle_phase = "menu"
                    elif self.battle_phase == "item":
                        self.battle_phase = "menu"
                    elif self.battle_phase == "mercy":
                        self.battle_phase = "menu"
                    else:
                        pass
                    return

                if self.battle_phase == "menu":
                    cols = 2
                    row = self.battle_menu_selection // cols
                    col = self.battle_menu_selection % cols
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        col = max(0, col - 1)
                        self._play_sound("cursor")
                    elif e.key in (pygame.K_RIGHT, pygame.K_d):
                        col = min(cols - 1, col + 1)
                        self._play_sound("cursor")
                    elif e.key in (pygame.K_UP, pygame.K_w):
                        row = max(0, row - 1)
                        self._play_sound("cursor")
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        row = min(1, row + 1)
                        self._play_sound("cursor")
                    elif e.key in CONFIRM_KEYS:
                        self._play_sound("confirm")
                        sel = self.battle_menu_options[self.battle_menu_selection]
                        if sel == "FIGHT":
                            self._do_fight()
                            return
                        elif sel == "ACT":
                            self.battle_phase = "act"
                            self.battle_act_selection = 0
                        elif sel == "ITEM":
                            self.battle_phase = "item"
                            self.battle_item_selection = 0
                        elif sel == "MERCY":
                            self.battle_phase = "mercy"
                            self.battle_mercy_selection = 0
                    self.battle_menu_selection = row * cols + col

                elif self.battle_phase == "act":
                    acts = self.battle_act_options or ["Check"]
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.battle_act_selection = (self.battle_act_selection - 1) % len(acts)
                        self._play_sound("cursor")
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.battle_act_selection = (self.battle_act_selection + 1) % len(acts)
                        self._play_sound("cursor")
                    elif e.key in CONFIRM_KEYS:
                        self._play_sound("confirm")
                        self._do_act(acts[self.battle_act_selection])
                        return

                elif self.battle_phase == "item":
                    items = self.player.items
                    if not items:
                        self.battle_message_active = True
                        self.battle_message_lines = ["* No items!"]
                        self.battle_message_index = 0
                        self.battle_action_taken = False
                        self.battle_phase = "menu"
                        return
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.battle_item_selection = (self.battle_item_selection - 1) % len(items)
                        self._play_sound("cursor")
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.battle_item_selection = (self.battle_item_selection + 1) % len(items)
                        self._play_sound("cursor")
                    elif e.key in CONFIRM_KEYS:
                        self._play_sound("confirm")
                        self._do_item(items[self.battle_item_selection])
                        return

                elif self.battle_phase == "mercy":
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.battle_mercy_selection = (self.battle_mercy_selection - 1) % 2
                        self._play_sound("cursor")
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.battle_mercy_selection = (self.battle_mercy_selection + 1) % 2
                        self._play_sound("cursor")
                    elif e.key in CONFIRM_KEYS:
                        self._play_sound("confirm")
                        sel = self.battle_mercy_options[self.battle_mercy_selection]
                        if sel == "Spare":
                            self._do_spare()
                        else:
                            self._do_flee()
                        return

    def _do_fight(self):
        # Enter fight minigame
        self.battle_phase = "fight"
        self.state = GameState.BATTLE_FIGHT
        self.fight_power = 0
        self.fight_charge_dir = 1
        self.fight_zone = pygame.Rect(SCREEN_W // 2 - 100, SCREEN_H // 2 - 10, 200, 20)
        self.fight_bonus = 0
        self.fight_timer = 0

    def _update_fight(self):
        self.fight_timer += 1
        self.fight_power += self.fight_charge_dir * 2
        if self.fight_power >= 100:
            self.fight_power = 100
            self.fight_charge_dir = -1
        elif self.fight_power <= 0:
            self.fight_power = 0
            self.fight_charge_dir = 1

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in CONFIRM_KEYS:
                    # Match bar position to drawing formula
                    bar_x = self.fight_zone.x + int(self.fight_power * (self.fight_zone.w - 10) / 100)
                    zone_center = self.fight_zone.centerx
                    dist = abs(bar_x - zone_center)
                    if dist < 10:
                        bonus = 1.5
                    elif dist < 25:
                        bonus = 1.2
                    elif dist < 50:
                        bonus = 1.0
                    else:
                        bonus = 0.5
                    enemy_def = self.enemy_data.get("def", 0) if self.enemy_data else 0
                    base_damage = max(1, self.player.atk - enemy_def // 2)
                    damage = max(1, int(base_damage * bonus))
                    self._damage_enemy(damage)
                    self._play_sound("enemy_damage")
                    if self.battle_defeated:
                        return
                    self.battle_message_active = True
                    self.battle_message_lines = [f"* {damage} damage!"]
                    self.battle_message_index = 0
                    self.battle_action_taken = True
                    self.state = GameState.BATTLE
                    self.battle_phase = "menu"

    def _damage_enemy(self, damage):
        self.enemy_hp -= damage
        if self.enemy_hp <= 0:
            self.enemy_hp = 0
            self._defeat_enemy()

    def _defeat_enemy(self):
        self.battle_defeated = True
        exp_gain = self.enemy_data.get("exp", 10) if self.enemy_data else 10
        gold_gain = self.enemy_data.get("gold", 5) if self.enemy_data else 5
        old_lv = self.player.lv
        self.player.add_exp(exp_gain)
        self.player.add_gold(gold_gain)
        if self.battle_enemy:
            if self.battle_enemy in self.player.spared_enemies:
                self.player.spared_enemies.remove(self.battle_enemy)
            if self.battle_enemy not in self.player.killed_enemies:
                self.player.killed_enemies.append(self.battle_enemy)
        self.player.pacifist = False
        name = self.enemy_data["name"] if self.enemy_data else "Monster"
        kill_msg = f"* You gained {exp_gain} EXP and {gold_gain} GOLD."
        self.dialogue_queue = [f"* {name} was defeated.", kill_msg]
        if self.player.lv > old_lv:
            self.dialogue_queue.append(f"* You're now LV {self.player.lv}.")
            self._play_sound("levelup")
        self._start_dialogue()

    def _do_act(self, act_name):
        results = self.enemy_data.get("act_results", {})
        msg = results.get(act_name, f"* You used {act_name}.")
        self.battle_act_count += 1

        if act_name == self.enemy_data.get("spareable_after", ""):
            self.spare_threshold = 1
            self.spare_progress += 2
        elif act_name in ("Compliment", "Console", "Imitate", "Cheer", "Pet", "Play",
                          "Talk", "Joke", "Pose", "Hope", "Flirt"):
            self.spare_progress += 1

        if self.enemy_data.get("spareable_after") == act_name and self.spare_progress >= 2:
            self._spare_enemy()
            return

        self.battle_message_active = True
        self.battle_message_lines = [msg]
        self.battle_message_index = 0
        self.battle_action_taken = True
        self.battle_phase = "menu"

    def _do_item(self, item_name):
        heal = self.player.use_item(item_name)
        if heal > 0:
            msg = f"* You used {item_name}.\n* You recovered {heal} HP!"
            self._play_sound("heal")
            self.battle_action_taken = True
        elif heal == 0:
            msg = f"* You used {item_name}.\n* But your HP is already full!"
            self._play_sound("heal")
            self.battle_action_taken = True
        else:
            msg = f"* You don't have {item_name}!"
            self.battle_action_taken = False
        self.battle_message_active = True
        self.battle_message_lines = [msg]
        self.battle_message_index = 0
        self.battle_phase = "menu"

    def _do_spare(self):
        self.spare_progress += 1
        if self.spare_progress >= self.spare_threshold:
            self._spare_enemy()
        else:
            msg = f"* You spared {self.enemy_data['name']}.\n* But it keeps fighting..."
            self.battle_message_active = True
            self.battle_message_lines = [msg]
            self.battle_message_index = 0
            self.battle_action_taken = True
            self.battle_phase = "menu"

    def _spare_enemy(self):
        self.battle_spared = True
        if self.battle_enemy:
            if self.battle_enemy in self.player.killed_enemies:
                self.player.killed_enemies.remove(self.battle_enemy)
            if self.battle_enemy not in self.player.spared_enemies:
                self.player.spared_enemies.append(self.battle_enemy)
        name = self.enemy_data["name"] if self.enemy_data else "Monster"
        self.dialogue_queue = [
            f"* {name} was spared.",
            f"* You gained 0 EXP and 0 GOLD.",
            "* You feel compassion for the monster.",
        ]
        self._start_dialogue()

    def _do_flee(self):
        self.battle_flee_attempts += 1
        chance = min(60, 20 + self.battle_flee_attempts * 15)
        if random.randint(1, 100) <= chance:
            msg = "* You fled successfully!"
            self.battle_message_active = True
            self.battle_message_lines = [msg]
            self.battle_message_index = 0
            self.battle_fled = True
            self.battle_action_taken = False
        else:
            msg = "* Can't escape!"
            self.battle_message_active = True
            self.battle_message_lines = [msg]
            self.battle_message_index = 0
            self.battle_action_taken = True  # failed flee still spends the turn
            self.battle_phase = "menu"

    def _start_enemy_turn(self):
        self.battle_player_turn = False
        self.battle_attack_phase = True
        self.battle_phase = "attack"
        self.bullet_spawn_timer = 0
        self.bullets = []
        self.soul_x = self.battle_box.centerx
        self.soul_y = self.battle_box.centery
        self.soul_flash_timer = 20  # brief i-frames so center-spawned bullets don't instant-hit
        if self.enemy_data:
            self._spawn_attack(self.enemy_data.get("bullets", ["simple"]))

    def _end_battle(self):
        # Don't auto-save a 0 HP death state
        if self.player.hp > 0:
            self._save_game()
        self.state = GameState.OVERWORLD
        self.battle_enemy = None
        self.enemy_data = None
        self.bullets = []
        self.battle_defeated = False
        self.battle_spared = False
        self.battle_fled = False
        self.battle_message_active = False
        self.battle_action_taken = False
        self.battle_attack_phase = False
        self.battle_player_turn = True
        self.enemy_encounter_timer = 0

    def _draw_battle(self):
        self.screen.fill(BLACK)
        self._draw_battle_background()

        # ── TOP AREA: Enemy info ──
        if self.enemy_data:
            blit_text(self.screen, self.enemy_data["name"], (30, 20), BLUE, 28)
            blit_text(self.screen, f"LV {self.player.lv}", (SCREEN_W - 30, 20), GREEN, 20, "topright")

            bar_rect = pygame.Rect(30, 55, 200, 16)
            draws_box(self.screen, bar_rect, BLUE, (10, 10, 30), 2)
            if self.enemy_max_hp > 0:
                fill_w = int(200 * self.enemy_hp / self.enemy_max_hp)
                hp_rect = pygame.Rect(31, 56, fill_w, 14)
                pygame.draw.rect(self.screen, YELLOW, hp_rect)
            hp_text = f"{self.enemy_hp}/{self.enemy_max_hp}"
            blit_text(self.screen, hp_text, (240, 53), BLUE, 14)

        # ── CENTER: Battle box (soul area) ──
        draws_box(self.screen, self.battle_box, BLUE, (5, 5, 25), 3)

        if self.battle_attack_phase and self.soul_flash_timer > 0 and (self.soul_flash_timer // 4) % 2 == 0:
            soul_color = WHITE
        else:
            soul_color = RED
        self._draw_heart(int(self.soul_x), int(self.soul_y), soul_color, self.soul_size)

        for b in self.bullets:
            b.draw(self.screen)

        # ── BOTTOM-LEFT: Player stats ──
        pbox = pygame.Rect(10, SCREEN_H - 120, 270, 105)
        draws_box(self.screen, pbox, BLUE, BLACK, 3)
        blit_text(self.screen, f"* {self.player.name}  LV {self.player.lv}",
                  (pbox.x + 10, pbox.y + 8), BLUE, 18)
        blit_text(self.screen, f"HP {self.player.hp}/{self.player.max_hp}",
                  (pbox.x + 10, pbox.y + 33), GREEN, 18)

        bar_x, bar_y = pbox.x + 10, pbox.y + 60
        hp_bar_rect = pygame.Rect(bar_x, bar_y, 230, 14)
        draws_box(self.screen, hp_bar_rect, BLUE, (10, 10, 30), 1)
        if self.player.max_hp > 0:
            fill_w = int(230 * self.player.hp / self.player.max_hp)
            hp_fill = pygame.Rect(bar_x + 1, bar_y + 1, fill_w, 12)
            color = YELLOW if self.player.hp > self.player.max_hp // 4 else RED
            pygame.draw.rect(self.screen, color, hp_fill)

        # ── BOTTOM-RIGHT: Battle menu ──
        if self.battle_player_turn and self.battle_phase != "intro" and not self.battle_attack_phase:
            self._draw_battle_menu()

        if self.battle_message_active:
            self._draw_battle_message()

        if self.battle_text_timer > 0 and self.battle_text:
            blit_text(self.screen, self.battle_text, (SCREEN_W // 2, SCREEN_H - 30), BLUE, 22, "center")

        make_border_rect(self.screen, BLUE, 4)

    def _draw_battle_message(self):
        msg_rect = pygame.Rect(60, SCREEN_H // 2 - 60, SCREEN_W - 120, 120)
        draws_box(self.screen, msg_rect, BLUE, BLACK, 3)
        inner = msg_rect.inflate(-6, -6)
        pygame.draw.rect(self.screen, (10, 10, 30), inner)
        lines = []
        for line in self.battle_message_lines:
            wrapped = text_wrap(line, self.font_med, msg_rect.w - 30)
            lines.extend(wrapped)
        for i, line in enumerate(lines):
            y = msg_rect.y + 15 + i * 28
            blit_text(self.screen, line, (msg_rect.x + 15, y), BLUE, 22)
        if self.battle_timer // 30 % 2 == 0:
            blit_text(self.screen, "[Press Z to continue]", (msg_rect.centerx, msg_rect.bottom - 10),
                      BLUE, 16, "center")

    def _draw_battle_background(self):
        for i in range(SCREEN_H):
            c = max(0, min(25, 5 + int(math.sin(i * 0.015) * 6)))
            pygame.draw.line(self.screen, (c, c, c), (0, i), (SCREEN_W, i))
        for x in range(0, SCREEN_W, 32):
            pygame.draw.line(self.screen, (20, 20, 25), (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 32):
            pygame.draw.line(self.screen, (20, 20, 25), (0, y), (SCREEN_W, y))

    def _draw_battle_menu(self):
        menu_x = SCREEN_W - 300
        menu_y = SCREEN_H - 120
        menu_w = 290
        menu_h = 105
        draws_box(self.screen, pygame.Rect(menu_x, menu_y, menu_w, menu_h), BLUE, BLACK, 3)

        if self.battle_phase == "menu":
            cols = 2
            for i, opt in enumerate(self.battle_menu_options):
                x = menu_x + 20 + (i % cols) * 130
                y = menu_y + 15 + (i // cols) * 38
                color = LIGHT_BLUE if i == self.battle_menu_selection else BLUE
                if i == self.battle_menu_selection:
                    self._draw_heart(x - 14, y + 8, RED, 4)
                blit_text(self.screen, opt, (x, y), color, 24)

        elif self.battle_phase == "act":
            acts = self.battle_act_options or ["Check"]
            for i, act in enumerate(acts):
                x = menu_x + 15
                y = menu_y + 12 + i * 26
                color = LIGHT_BLUE if i == self.battle_act_selection else BLUE
                if i == self.battle_act_selection:
                    self._draw_heart(x - 12, y + 6, RED, 4)
                blit_text(self.screen, act, (x + 2, y), color, 20)

        elif self.battle_phase == "item":
            items = self.player.items
            if items:
                for i, item in enumerate(items):
                    x = menu_x + 15
                    y = menu_y + 12 + i * 26
                    color = LIGHT_BLUE if i == self.battle_item_selection else BLUE
                    if i == self.battle_item_selection:
                        self._draw_heart(x - 12, y + 6, RED, 4)
                    count = self.player.item_counts.get(item, 0)
                    blit_text(self.screen, f"{item} x{count}", (x + 2, y), color, 20)
            else:
                blit_text(self.screen, "(No items)", (menu_x + 15, menu_y + 15), BLUE, 20)

        elif self.battle_phase == "mercy":
            for i, opt in enumerate(self.battle_mercy_options):
                x = menu_x + 20 + i * 130
                y = menu_y + 20
                color = LIGHT_BLUE if i == self.battle_mercy_selection else BLUE
                if i == self.battle_mercy_selection:
                    self._draw_heart(x - 14, y + 8, RED, 4)
                blit_text(self.screen, opt, (x, y), color, 24)
            prog_text = f"Spare: {self.spare_progress}/{self.spare_threshold}"
            blit_text(self.screen, prog_text, (menu_x + 15, menu_y + 60), BLUE, 16)

    def _draw_fight(self):
        self.screen.fill(BLACK)
        self._draw_battle_background()

        blit_text(self.screen, "FIGHT", (SCREEN_W // 2, 30), RED, 36, "center")

        draws_box(self.screen, self.fight_zone, BLUE, (10, 10, 30), 2)

        bar_x = self.fight_zone.x + int(self.fight_power * (self.fight_zone.w - 10) / 100)
        bar_y = self.fight_zone.y + 2
        pygame.draw.rect(self.screen, (255, 255, 100), (bar_x, bar_y, 8, self.fight_zone.h - 4))

        tz_w = 30
        tz_x = self.fight_zone.centerx - tz_w // 2
        pygame.draw.rect(self.screen, RED, (tz_x, self.fight_zone.y + 1, tz_w, self.fight_zone.h - 2), 2)

        blit_text(self.screen, "Press Z to attack!",
                  (SCREEN_W // 2, SCREEN_H - 30), BLUE, 22, "center")

        if self.enemy_data:
            blit_text(self.screen, self.enemy_data["name"], (30, 20), BLUE, 28)
            blit_text(self.screen, f"LV {self.player.lv}", (SCREEN_W - 30, 20), GREEN, 20, "topright")
            hp_text = f"HP: {self.enemy_hp}/{self.enemy_max_hp}"
            blit_text(self.screen, hp_text, (30, 55), YELLOW, 22)

        pbox = pygame.Rect(10, SCREEN_H - 120, 270, 105)
        draws_box(self.screen, pbox, BLUE, BLACK, 3)
        blit_text(self.screen, f"* {self.player.name}  LV {self.player.lv}",
                  (pbox.x + 10, pbox.y + 8), BLUE, 18)
        blit_text(self.screen, f"HP {self.player.hp}/{self.player.max_hp}",
                  (pbox.x + 10, pbox.y + 33), GREEN, 18)
        bar_x, bar_y = pbox.x + 10, pbox.y + 60
        hp_bar_rect = pygame.Rect(bar_x, bar_y, 230, 14)
        draws_box(self.screen, hp_bar_rect, BLUE, (10, 10, 30), 1)
        if self.player.max_hp > 0:
            fill_w = int(230 * self.player.hp / self.player.max_hp)
            hp_fill = pygame.Rect(bar_x + 1, bar_y + 1, fill_w, 12)
            color = YELLOW if self.player.hp > self.player.max_hp // 4 else RED
            pygame.draw.rect(self.screen, color, hp_fill)

        make_border_rect(self.screen, BLUE, 4)

    # ── PAUSE ──────────────────────────────────────────────────────────────────
    def _update_pause(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in CANCEL_KEYS or e.key in CONFIRM_KEYS:
                    self._set_state(GameState.OVERWORLD)
                elif e.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self._save_game()
                    self.pause_message = "Game saved!"
                    self.pause_msg_timer = 60

        if self.pause_msg_timer > 0:
            self.pause_msg_timer -= 1

    def _draw_pause(self):
        self.screen.fill(BLACK)

        blit_text(self.screen, "PAUSED", (SCREEN_W // 2, 80), BLUE, 48, "center")
        blit_text(self.screen, "deepseekr1 tale 0.1", (SCREEN_W // 2, 130), LIGHT_BLUE, 24, "center")

        info_lines = [
            f"Name: {self.player.name}",
            f"LV: {self.player.lv}",
            f"HP: {self.player.hp}/{self.player.max_hp}",
            f"ATK: {self.player.atk}  DEF: {self.player.def_}",
            f"EXP: {self.player.exp}/{self.player.next_exp}",
            f"GOLD: {self.player.gold}",
            f"Weapon: {self.player.weapon}",
            f"Armor: {self.player.armor}",
        ]
        for i, line in enumerate(info_lines):
            blit_text(self.screen, line, (SCREEN_W // 2 - 100, 180 + i * 28), BLUE, 20)

        blit_text(self.screen, "Z/X: Resume   Ctrl+S: Save",
                  (SCREEN_W // 2, SCREEN_H - 40), LIGHT_BLUE, 16, "center")

        if self.pause_msg_timer > 0:
            blit_text(self.screen, self.pause_message,
                      (SCREEN_W // 2, SCREEN_H - 80), GREEN, 24, "center")

    # ── GAME OVER ──────────────────────────────────────────────────────────────
    def _update_game_over(self):
        self.game_over_timer += 1
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in CONFIRM_KEYS:
                    # Retry — reload last save (or soft-reset), restore HP and position
                    self.battle_enemy = None
                    self.enemy_data = None
                    self.bullets = []
                    self.battle_defeated = False
                    self.battle_spared = False
                    self.battle_fled = False
                    self.battle_message_active = False
                    self.battle_attack_phase = False
                    if not self._load_game():
                        self.player = PlayerData()
                        self.room_name = "start"
                        self.px = 10 * TILE_SIZE
                        self.py = 2 * TILE_SIZE
                    self.player.hp = max(1, self.player.max_hp)
                    self._enter_room(self.room_name, self.px, self.py)
                    self._set_state(GameState.OVERWORLD)

    def _draw_game_over(self):
        self.screen.fill(BLACK)

        if self.game_over_timer < 30:
            flash = pygame.Surface((SCREEN_W, SCREEN_H))
            flash.fill((255, 0, 0))
            flash.set_alpha(max(0, 200 - self.game_over_timer * 6))
            self.screen.blit(flash, (0, 0))

        if self.game_over_timer > 60:
            blit_text(self.screen, "GAME OVER", (SCREEN_W // 2, SCREEN_H // 2 - 40), RED, 56, "center")
            blink = (self.game_over_timer // 30) % 2 == 0
            if blink:
                blit_text(self.screen, "Press Z to continue", (SCREEN_W // 2, SCREEN_H // 2 + 30), BLUE, 24, "center")

    # ── Main Loop ──────────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            self.screen.fill(BLACK)

            prev_state = self.state

            if self.state == GameState.MENU:
                self._update_menu()
            elif self.state == GameState.OVERWORLD:
                self._update_overworld()
            elif self.state == GameState.DIALOGUE:
                self._update_dialogue()
            elif self.state in (GameState.BATTLE, GameState.BATTLE_MENU,
                                GameState.BATTLE_ACT, GameState.BATTLE_ITEM,
                                GameState.BATTLE_MERCY):
                self._update_battle()
            elif self.state == GameState.BATTLE_FIGHT:
                self._update_fight()
            elif self.state == GameState.PAUSE:
                self._update_pause()
            elif self.state == GameState.GAME_OVER:
                self._update_game_over()

            # Re-check state after update (it may have changed mid-update)
            state = self.state

            if state == GameState.MENU:
                self._draw_menu()
            elif state == GameState.OVERWORLD:
                self._draw_overworld()
            elif state == GameState.DIALOGUE:
                self._draw_dialogue()
            elif state in (GameState.BATTLE, GameState.BATTLE_MENU, GameState.BATTLE_ACT,
                           GameState.BATTLE_ITEM, GameState.BATTLE_MERCY,
                           GameState.BATTLE_DIALOGUE):
                self._draw_battle()
            elif state == GameState.BATTLE_FIGHT:
                self._draw_fight()
            elif state == GameState.PAUSE:
                self._draw_pause()
            elif state == GameState.GAME_OVER:
                self._draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = DeepSeekTale()
    game.run()

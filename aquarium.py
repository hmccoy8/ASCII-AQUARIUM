"""
ASCII Aquarium — resizable tkinter desktop aquarium.
Drag the window (or maximise) and the tank scales to fill the space.

Controls:
  +      add a fish
  -      remove a fish
  Space  release a burst of bubbles
  Q      quit
"""

import tkinter as tk
from tkinter import font as tkfont
import random
import math

# ── Aquarium dimensions — updated dynamically on window resize ───
COLS = 92
ROWS = 28
FPS  = 20

# ── Fish sprites: (right-facing, left-facing, colour-tag) ────────
FISH_SPRITES = [
    ("><>",           "<><",           "fish_cyan"),
    ("~><>",          "<>< ~",         "fish_cyan"),
    ("><{*>",         "<*}><",         "fish_green"),
    ("><{{(*>",       "<*)}}><",       "fish_green"),
    ("~><{{((*>",     "<*))}}><~",     "fish_yellow"),
    ("=><{{{(*>",     "<*)}}}><=",     "fish_red"),
    ("><(((*>",       "<*)))><",       "fish_magenta"),
    ("=><(((((*>",    "<*)))))><=",    "fish_orange"),
]

SAND_PATTERN  = "._.-`-._."
SURFACE_CHARS = "~~--~~--"

# ── Floor decoration sprites (bottom row sits on SAND) ───────────
DECORATION_DEFS = [
    {
        "lines": [
            "^ ^ ^ ^ ^",
            "|       |",
            "|  ___  |",
            "| |   | |",
            "|_|___|_|",
        ],
        "color": "decor_castle",
    },
    {
        "lines": [
            "    |    ",
            "    |\\   ",
            "____|_\\__",
            "|_______|",
        ],
        "color": "decor_ship",
    },
    {
        "lines": [
            ".-----.",
            "|o o o|",
            "|_____|",
        ],
        "color": "decor_treasure",
    },
]


# ── Entity classes ───────────────────────────────────────────────

class Decoration:
    def __init__(self, x: int, lines: list, color: str):
        self.x      = x
        self.lines  = lines
        self.color  = color
        self.width  = max(len(line) for line in lines)
        self.height = len(lines)


class Bubble:
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.speed = random.uniform(0.10, 0.25)
        self.char  = random.choice(["o", ".", "O", "°"])

    def update(self):
        self.y -= self.speed

    @property
    def alive(self) -> bool:
        return self.y >= 1.5


class Fish:
    def __init__(self):
        idx = random.randint(0, len(FISH_SPRITES) - 1)
        self.sprite_r, self.sprite_l, self.color = FISH_SPRITES[idx]
        self.direction = random.choice([-1, 1])
        slen = len(self.sprite_r)
        self.x = float(-slen) if self.direction == 1 else float(COLS)
        self._row_f       = float(random.randint(3, max(3, ROWS - 5)))
        self._target_row  = self._row_f
        self._v_speed     = 0.0
        self._drift_timer = random.randint(60, 180)
        self.speed        = random.uniform(0.10, 0.38)
        self._bubble_timer = random.randint(12, 45)

    @property
    def row(self) -> int:
        return int(self._row_f)

    @property
    def sprite(self) -> str:
        return self.sprite_r if self.direction == 1 else self.sprite_l

    def clamp_rows(self):
        """Snap fish into the valid row range after a resize."""
        lo, hi = 3.0, float(max(3, ROWS - 5))
        self._row_f      = max(lo, min(hi, self._row_f))
        self._target_row = max(lo, min(hi, self._target_row))

    def update(self):
        self.x += self.direction * self.speed
        self._bubble_timer -= 1

        # Vertical drift — smoothly slide toward _target_row
        if self._row_f != self._target_row:
            diff = self._target_row - self._row_f
            step = math.copysign(min(abs(diff), self._v_speed), diff)
            self._row_f += step
            if abs(self._target_row - self._row_f) < 0.05:
                self._row_f = self._target_row
                self._v_speed = 0.0

        # Occasionally pick a new target row
        self._drift_timer -= 1
        if self._drift_timer <= 0:
            self._drift_timer = random.randint(80, 220)
            if random.random() < 0.35:
                lo   = 3.0
                hi   = float(max(3, ROWS - 5))
                span = hi - lo
                shift = (span / 5 + random.random() * span * 0.3) * random.choice([-1, 1])
                self._target_row = max(lo, min(hi, self._row_f + shift))
                self._v_speed    = random.uniform(0.018, 0.040)

    def mouth_pos(self) -> tuple:
        sx = int(self.x)
        if self.direction == 1:
            return sx + len(self.sprite) - 1, self.row
        else:
            return sx, self.row

    def want_bubble(self) -> bool:
        if self._bubble_timer <= 0:
            self._bubble_timer = random.randint(12, 45)
            return True
        return False

    @property
    def alive(self) -> bool:
        slen = len(self.sprite)
        if self.direction == 1:
            return self.x < COLS + slen
        return self.x > -slen - 1


class Seaweed:
    def __init__(self, x: int, height: int):
        self.x      = x
        self.height = height
        self.phase  = random.uniform(0, math.tau)
        self.speed  = random.uniform(0.03, 0.08)

    def update(self):
        self.phase += self.speed

    def char_at(self, depth: int) -> str:
        sway = math.sin(self.phase + depth * 0.6)
        if sway > 0.25:  return "/"
        if sway < -0.25: return "\\"
        return "|"


# ── Main application ─────────────────────────────────────────────

class AsciiAquarium:

    PALETTE = {
        "bg":           "#000d1a",
        "water":        "#002244",
        "surface":      "#0066cc",
        "fish_cyan":    "#00ffee",
        "fish_green":   "#44ff88",
        "fish_yellow":  "#ffee00",
        "fish_red":     "#ff6644",
        "fish_magenta": "#ff44cc",
        "fish_orange":  "#ffaa00",
        "bubble":       "#88ccff",
        "seaweed":      "#00cc55",
        "sand":         "#cc9944",
        "rock":           "#556677",
        "status":         "#335577",
        "decor":          "#bbaa66",
        "decor_castle":   "#ccaa55",
        "decor_ship":     "#998877",
        "decor_treasure": "#ffdd44",
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ASCII Aquarium")
        self.root.configure(bg=self.PALETTE["bg"])
        self.root.resizable(True, True)

        # Measure a single character cell for this font
        self._font_obj = tkfont.Font(
            family="Courier New", size=13, weight="bold"
        )
        self._char_w = self._font_obj.measure("M")       # monospace: all same
        self._char_h = self._font_obj.metrics("linespace")

        # Text widget expands with the window
        self.text = tk.Text(
            self.root,
            width=COLS, height=ROWS,
            bg=self.PALETTE["bg"], fg=self.PALETTE["water"],
            font=self._font_obj,
            state="disabled", cursor="none",
            insertwidth=0, selectbackground=self.PALETTE["bg"],
            relief="flat", borderwidth=0,
            padx=0, pady=0,
        )
        self.text.pack(fill="both", expand=True)
        self._configure_tags()

        # Status bar — fixed height strip at the bottom
        self._status = tk.StringVar()
        tk.Label(
            self.root,
            textvariable=self._status,
            bg=self.PALETTE["bg"], fg=self.PALETTE["status"],
            font=("Courier New", 10),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 4))

        # Key bindings
        self.root.bind("<q>",      lambda _: self.root.destroy())
        self.root.bind("<Q>",      lambda _: self.root.destroy())
        self.root.bind("<plus>",   lambda _: self._spawn_fish())
        self.root.bind("<equal>",  lambda _: self._spawn_fish())
        self.root.bind("<minus>",  lambda _: self._remove_fish())
        self.root.bind("<space>",  lambda _: self._bubble_burst())

        # Resize — debounced so we don't thrash while dragging
        self._resize_job = None
        self.root.bind("<Configure>", self._on_configure)

        # State
        self.fishes:  list = []
        self.bubbles: list = []
        self.frame = 0

        self._seaweeds    = self._make_seaweeds()
        self._floor_decor = self._make_floor_decor()
        self._decorations = self._make_decorations()

        for _ in range(7):
            self._spawn_fish()

        self._animate()
        self.root.mainloop()

    # ── Setup helpers ────────────────────────────────────────────

    def _configure_tags(self):
        for name, colour in self.PALETTE.items():
            self.text.tag_configure(
                name, foreground=colour, font=self._font_obj
            )

    def _make_seaweeds(self) -> list:
        count = max(1, COLS // 10)
        pool  = range(3, max(4, COLS - 3))
        xs    = random.sample(list(pool), min(count, len(pool)))
        max_h = max(2, min(7, ROWS // 4))
        return [Seaweed(x, random.randint(2, max_h)) for x in xs]

    def _make_floor_decor(self) -> dict:
        decor: dict = {}
        icons = ["*", "ö", "o", "°", "©", "ø"]
        for _ in range(max(1, COLS // 5)):
            x = random.randint(1, max(1, COLS - 2))
            decor[x] = random.choice(icons)
        return decor

    def _make_decorations(self) -> list:
        decorations = []
        occupied: set = set()
        candidates = DECORATION_DEFS.copy()
        random.shuffle(candidates)
        for defn in candidates:
            lines  = defn["lines"]
            width  = max(len(line) for line in lines)
            height = len(lines)
            if ROWS - 4 < height + 1 or COLS < width + 4:
                continue
            max_x = COLS - width - 2
            for _ in range(30):
                x = random.randint(2, max_x)
                if not any(c in occupied for c in range(x - 1, x + width + 1)):
                    decorations.append(Decoration(x, lines, defn["color"]))
                    for c in range(x - 2, x + width + 2):
                        occupied.add(c)
                    break
        return decorations

    # ── Resize handling ──────────────────────────────────────────

    def _on_configure(self, event):
        """Ignore child-widget events; debounce root resize."""
        if event.widget is not self.root:
            return
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(120, self._apply_resize)

    def _apply_resize(self):
        global COLS, ROWS
        self._resize_job = None

        self.text.update_idletasks()
        pw = self.text.winfo_width()
        ph = self.text.winfo_height()
        if pw < 10 or ph < 10:
            return

        new_cols = max(20, pw // self._char_w)
        new_rows = max(8,  ph // self._char_h)
        if new_cols == COLS and new_rows == ROWS:
            return

        COLS, ROWS = new_cols, new_rows

        # Keep fish inside the new bounds
        for fish in self.fishes:
            fish.clamp_rows()

        # Drop bubbles that are now off-screen
        self.bubbles = [
            b for b in self.bubbles
            if 0 <= int(b.x) < COLS and 1 < int(b.y) < ROWS - 2
        ]

        # Rebuild seaweed, floor decor, and decorations for the new width / depth
        self._seaweeds    = self._make_seaweeds()
        self._floor_decor = self._make_floor_decor()
        self._decorations = self._make_decorations()

    # ── Controls ─────────────────────────────────────────────────

    def _spawn_fish(self):
        if len(self.fishes) < 30:
            self.fishes.append(Fish())

    def _remove_fish(self):
        if self.fishes:
            self.fishes.pop()

    def _bubble_burst(self):
        for _ in range(random.randint(4, 10)):
            x = random.randint(1, max(1, COLS - 2))
            y = random.randint(max(2, ROWS - 6), max(2, ROWS - 3))
            self.bubbles.append(Bubble(x, y))

    # ── Animation loop ───────────────────────────────────────────

    def _animate(self):
        self._update()
        self._render()
        self.root.after(1000 // FPS, self._animate)

    def _update(self):
        self.frame += 1

        live: list = []
        for fish in self.fishes:
            fish.update()
            if fish.alive:
                live.append(fish)
                if fish.want_bubble():
                    bx, by = fish.mouth_pos()
                    if 0 <= bx < COLS:
                        self.bubbles.append(Bubble(bx, by))
        self.fishes = live

        if len(self.fishes) < 5 and random.random() < 0.04:
            self._spawn_fish()

        for b in self.bubbles:
            b.update()
        self.bubbles = [b for b in self.bubbles if b.alive]

        for sw in self._seaweeds:
            sw.update()

    def _render(self):
        SURF = 1
        SAND = ROWS - 2
        ROCK = ROWS - 1

        grid = [[(" ", "water")] * COLS for _ in range(ROWS)]

        # Surface waves
        for c in range(COLS):
            idx = (c + self.frame // 3) % len(SURFACE_CHARS)
            grid[SURF][c] = (SURFACE_CHARS[idx], "surface")

        # Sandy floor
        for c in range(COLS):
            ch  = self._floor_decor.get(c, SAND_PATTERN[c % len(SAND_PATTERN)])
            tag = "decor" if c in self._floor_decor else "sand"
            grid[SAND][c] = (ch, tag)

        # Rocky bottom
        for c in range(COLS):
            grid[ROCK][c] = ("#", "rock")

        # Floor decorations (castle, shipwreck, treasure chest)
        for decor in self._decorations:
            for di, line in enumerate(decor.lines):
                r = SAND - decor.height + 1 + di
                if not (SURF < r <= SAND):
                    continue
                for j, ch in enumerate(line):
                    cx = decor.x + j
                    if 0 <= cx < COLS and ch != " ":
                        grid[r][cx] = (ch, decor.color)

        # Seaweed
        for sw in self._seaweeds:
            if not (0 <= sw.x < COLS):
                continue
            for d in range(sw.height):
                r = SAND - 1 - d
                if SURF < r < SAND:
                    grid[r][sw.x] = (sw.char_at(d), "seaweed")

        # Bubbles
        for b in self.bubbles:
            bx, by = int(b.x), int(b.y)
            if 0 <= bx < COLS and SURF < by < SAND:
                grid[by][bx] = (b.char, "bubble")

        # Fish (drawn on top)
        for fish in self.fishes:
            sprite = fish.sprite
            fx, fy = int(fish.x), fish.row
            if not (SURF <= fy < SAND):
                continue
            for i, ch in enumerate(sprite):
                cx = fx + i
                if 0 <= cx < COLS:
                    grid[fy][cx] = (ch, fish.color)

        # Flush to Text widget (run-length encoded per colour tag)
        self.text.config(state="normal")
        self.text.delete("1.0", "end")

        for r, row in enumerate(grid):
            c = 0
            while c < COLS:
                ch, tag = row[c]
                run = ch
                j = c + 1
                while j < COLS and row[j][1] == tag:
                    run += row[j][0]
                    j += 1
                self.text.insert("end", run, tag)
                c = j
            if r < ROWS - 1:
                self.text.insert("end", "\n")

        self.text.config(state="disabled")

        self._status.set(
            f"  Fish: {len(self.fishes):>2}  Bubbles: {len(self.bubbles):>3}"
            "    |    [+] add fish   [-] remove   [Space] bubbles   [Q] quit"
        )


# ── Entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    AsciiAquarium()

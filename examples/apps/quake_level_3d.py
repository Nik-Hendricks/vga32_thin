
from vga32.game import GameApp
import math

class QuakeLevel3D(GameApp):
    app_id = "games.quakelevel"
    title = "Quake Level 3D"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 12

    def start(self):
        self.m = [
            "############################",
            "#............#.............#",
            "#.##########.#.##########..#",
            "#.#........#.#.#........#..#",
            "#.#.######.#.#.#.######.#..#",
            "#.#.#....#.#.#.#.#....#.#..#",
            "#.#.#.##.#.#.#.#.#.##.#.#..#",
            "#.#.#..#.#.#.#.#.#..#.#.#..#",
            "#.#.####.#.#.#.#.####.#.#..#",
            "#.#......#.#.#.#......#.#..#",
            "#.########.#.#.########.#..#",
            "#..........#...#........#..#",
            "############...#############",
            "#......#...........#.......#",
            "#.####.#.#########.#.#####.#",
            "#.#..#.#.#.......#.#.#...#.#",
            "#.#..#.G.#.#####.#.#.#.#.#.#",
            "#.#..#.#.#.#...#.#.#.#.#.#.#",
            "#.####.#.#.#####.#.#.#.#.#.#",
            "#......#.#.......#.#...#...#",
            "############...#############",
        ]
        self.mh = len(self.m)
        self.mw = max(len(r) for r in self.m)
        self.m = [r.ljust(self.mw, "#") for r in self.m]
        self.px, self.py = 1.5, 1.5
        self.ang = 0.0
        self.health = 100
        self.ammo = 50
        self.score = 0
        self.won = False
        self.over = False
        self.time = 0.0

    def cell(self, x, y):
        if x < 0 or y < 0 or x >= self.mw or y >= self.mh:
            return "#"
        return self.m[int(y)][int(x)]

    def is_wall(self, ch):
        return ch not in (".", " ", "G", "A", "H")

    def update(self, dt):
        if self.pressed("r"):
            self.start()
            return
        if self.over or self.won:
            return
        self.time += dt
        rot = 1.8 * dt
        if self.held("left") or self.held("a"):
            self.ang -= rot
        if self.held("right") or self.held("d"):
            self.ang += rot
        sp = 2.4 * dt
        nx, ny = self.px, self.py
        if self.held("up") or self.held("w"):
            nx += math.cos(self.ang) * sp
            ny += math.sin(self.ang) * sp
        if self.held("down") or self.held("s"):
            nx -= math.cos(self.ang) * sp
            ny -= math.sin(self.ang) * sp
        if not self.is_wall(self.cell(nx, self.py)):
            self.px = nx
        if not self.is_wall(self.cell(self.px, ny)):
            self.py = ny
        ch = self.cell(self.px, self.py)
        if ch == "G":
            self.won = True
            self.score += 1000
        if ch == "A":
            self.ammo = min(99, self.ammo + 10)
            # mark collected
            r = list(self.m[int(self.py)])
            r[int(self.px)] = "."
            self.m[int(self.py)] = "".join(r)
        if ch == "H":
            self.health = min(100, self.health + 25)
            r = list(self.m[int(self.py)])
            r[int(self.px)] = "."
            self.m[int(self.py)] = "".join(r)

    def render(self, g):
        g.clear("black")
        W, H = self.width, self.height
        # ceiling and floor bands
        g.rect(0, 0, W, H//2, (20,20,40))
        g.rect(0, H//2, W, H//2, (35,35,35))
        for x in range(0, W, 2):
            cam = 2.0 * x / W - 1.0
            # camera plane factor
            rdx = math.cos(self.ang) - math.sin(self.ang) * cam * 0.66
            rdy = math.sin(self.ang) + math.cos(self.ang) * cam * 0.66
            mx, my = int(self.px), int(self.py)
            dx = 1 if rdx > 0 else -1 if rdx < 0 else 0
            dy = 1 if rdy > 0 else -1 if rdy < 0 else 0
            side_dist_x = ((mx + (1 if dx > 0 else 0)) - self.px) / rdx if rdx != 0 else 1e9
            side_dist_y = ((my + (1 if dy > 0 else 0)) - self.py) / rdy if rdy != 0 else 1e9
            delta_x = abs(1.0 / rdx) if rdx != 0 else 1e9
            delta_y = abs(1.0 / rdy) if rdy != 0 else 1e9
            hit = False
            side = 0
            char = "#"
            for _ in range(32):
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_x
                    mx += dx
                    side = 0
                else:
                    side_dist_y += delta_y
                    my += dy
                    side = 1
                ch = self.cell(mx, my)
                if self.is_wall(ch):
                    hit = True
                    char = ch
                    break
            if not hit:
                continue
            perp = (side_dist_x - delta_x) if side == 0 else (side_dist_y - delta_y)
            if perp < 0.001:
                perp = 0.001
            line_h = int(H / perp)
            y0 = (H - line_h) // 2
            y0 = max(0, min(H - line_h, y0))
            # wall color/texture
            if side == 0:
                base = (180,180,180)
            else:
                base = (120,120,120)
            if char == "B":
                base = (70,100,200)
            elif char == "R":
                base = (200,70,70)
            elif char == "G":
                base = (70,200,70)
            elif char == "Y":
                base = (200,200,70)
            # depth tint
            shade = max(0, min(255, int(255 * (1 - perp / 12.0))))
            col = tuple(int(c * shade / 255) for c in base)
            # texture pips
            g.rect(x, y0, 2, line_h, col)
            if perp < 8 and line_h > 12:
                # texture bands
                band = (mx * 7 + my * 11) % 3
                if band == 0:
                    g.rect(x, y0, 2, max(1, line_h // 4), tuple(min(255, c+40) for c in col))
                elif band == 1:
                    g.rect(x, y0 + line_h//2, 2, max(1, line_h//4), tuple(max(0, c-40) for c in col))
        # floor/ceiling faint perspective lines
        for i in range(-4, 5):
            g.line(W//2 + i*40, H//2, W//2 + i*120, H, (40,40,40), 1)
        # minimap
        mw, mh = 2, 2
        ox, oy = W- (self.mw*mw+4), 4
        g.rect(ox, oy, self.mw*mw+2, self.mh*mh+2, "black", outline="white")
        for y in range(self.mh):
            row = self.m[y]
            for x in range(len(row)):
                ch = row[x]
                if ch == "#":
                    g.rect(ox+1+x*mw, oy+1+y*mh, mw-1, mh-1, "gray")
                elif ch in ("G","A","H"):
                    color = "lime" if ch=="G" else ("yellow" if ch=="A" else "red")
                    g.rect(ox+1+x*mw, oy+1+y*mh, mw-1, mh-1, color)
        px = ox + 1 + int(self.px * mw)
        py = oy + 1 + int(self.py * mh)
        g.rect(px-1, py-1, 3, 3, "cyan")
        # HUD
        g.text(4, 4, f"HP {self.health}  Ammo {self.ammo}  Score {self.score}", "white", size="small")
        if self.won:
            g.text(W//2, H//2, "LEVEL CLEAR", "lime", size="medium", center=True)
        g.text(4, H-12, "WASD/Arrows move  R restart", "white", size="small")

    def game_state(self):
        return {"pos": [round(self.px,2), round(self.py,2)], "hp": self.health, "ammo": self.ammo,
                "score": self.score, "won": self.won}


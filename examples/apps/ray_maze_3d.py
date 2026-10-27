
from vga32.game import GameApp
import math

class RayMaze3D(GameApp):
    app_id = "games.raymaz3d"
    title = "3D Ray Maze"
    icon = "star"
    category = "Games"
    width, height = 480, 300
    fps = 6

    def start(self):
        self.m = [
            "################",
            "#..............#",
            "#.####...#.##..#",
            "#.#....#.#..#..#",
            "#.#.####.####..#",
            "#.#....#....#..#",
            "#.####.####.#..#",
            "#......#....#..#",
            "#.######.######",
            "#..............#",
            "#.###########..#",
            "#G.............#",
            "################",
        ]
        self.mw = len(self.m[0])
        self.mh = len(self.m)
        self.px, self.py = 1.5, 1.5
        self.ang = 0.0
        self.t = 0.0
        self.won = False
        self.over = False
        self.score = 0
        self.fov = 0.66

    def cell(self, x, y):
        if x < 0 or y < 0 or x >= self.mw or y >= self.mh:
            return "#"
        return self.m[int(y)][int(x)]

    def update(self, dt):
        if self.pressed("r"):
            self.start()
            return
        if self.over or self.won:
            return
        rot = 1.6 * dt
        if self.held("left") or self.held("a"):
            self.ang -= rot
        if self.held("right") or self.held("d"):
            self.ang += rot
        sp = 2.6 * dt
        nx, ny = self.px, self.py
        if self.held("up") or self.held("w"):
            nx += math.cos(self.ang) * sp
            ny += math.sin(self.ang) * sp
        if self.held("down") or self.held("s"):
            nx -= math.cos(self.ang) * sp
            ny -= math.sin(self.ang) * sp
        if self.cell(nx, self.py) != "#":
            self.px = nx
        if self.cell(self.px, ny) != "#":
            self.py = ny
        if self.cell(self.px, self.py) == "G":
            self.won = True
            self.score += 1000
        self.score += 1

    def render(self, g):
        g.clear("black")
        g.rect(0, 0, self.width, self.height // 2, "navy")
        g.rect(0, self.height // 2, self.width, self.height // 2, "darkgray")
        for x in range(0, self.width, 2):
            cam = 2.0 * x / self.width - 1.0
            rdx = math.cos(self.ang) - math.sin(self.ang) * cam * self.fov
            rdy = math.sin(self.ang) + math.cos(self.ang) * cam * self.fov
            mx, my = int(self.px), int(self.py)
            dx = 1 if rdx > 0 else -1 if rdx < 0 else 0
            dy = 1 if rdy > 0 else -1 if rdy < 0 else 0
            side_dist_x = ((mx + (1 if dx > 0 else 0)) - self.px) / rdx if rdx != 0 else 1e9
            side_dist_y = ((my + (1 if dy > 0 else 0)) - self.py) / rdy if rdy != 0 else 1e9
            delta_x = abs(1.0 / rdx) if rdx != 0 else 1e9
            delta_y = abs(1.0 / rdy) if rdy != 0 else 1e9
            hit = False
            side = 0
            for _ in range(24):
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_x
                    mx += dx
                    side = 0
                else:
                    side_dist_y += delta_y
                    my += dy
                    side = 1
                if 0 <= my < len(self.m) and 0 <= mx < len(self.m[my]) and self.m[my][mx] == "#":
                    hit = True
                    break
            if not hit:
                continue
            perp = (side_dist_x - delta_x) if side == 0 else (side_dist_y - delta_y)
            if perp < 0.001:
                perp = 0.001
            line_h = int(self.height / perp)
            # Y-shear: slant the image by column
            shear = int((x - self.width // 2) * 0.12)
            pitch = int(math.sin(self.t * 0.5) * 6)
            y0 = (self.height - line_h) // 2 + pitch + shear
            y0 = max(0, min(self.height - line_h, y0))
            y1 = y0 + line_h
            # texture coordinate along wall
            if side == 0:
                wall_x = self.py + perp * rdy
            else:
                wall_x = self.px + perp * rdx
            wall_x -= math.floor(wall_x)
            # brick-ish pattern plus distance fog
            hx = int(wall_x * 6)
            hy = int((y0 - (self.height - line_h)//2) / max(1, line_h//6))
            if (hx + hy) % 2 == 0:
                color = "white" if side == 0 else "gray"
            else:
                color = "gray" if side == 0 else "darkgray"
            if perp > 6:
                color = "gray" if side == 0 else "darkgray"
            if perp > 10:
                color = "darkgray"
            g.rect(x, y0, 2, line_h, color)
            # subtle texture pips
            if line_h > 18 and (hx % 3 == 0):
                g.rect(x, y0 + line_h//3, 2, 2, "black")
                g.rect(x, y0 + 2*line_h//3, 2, 2, "black")
        # minimap
        mw, mh = 2, 2
        ox, oy = 4, 4
        g.rect(ox, oy, self.mw*mw+2, self.mh*mh+2, "black", outline="white")
        for y in range(self.mh):
            row = self.m[y]
            for x in range(len(row)):
                if row[x] == "#":
                    g.rect(ox+1+x*mw, oy+1+y*mh, mw-1, mh-1, "gray")
        px = ox + 1 + int(self.px * mw)
        py = oy + 1 + int(self.py * mh)
        g.rect(px-1, py-1, 3, 3, "lime")
        g.text(6, self.height-24, f"Score {self.score}" + (" WIN" if self.won else ""), "yellow", size="small")
        g.text(6, self.height-14, "WASD/Arrows look-move, R restart", "white", size="small")
        if self.won:
            g.text(self.width//2, self.height//2, "ESCAPED!", "lime", size="medium", center=True)

    def game_state(self):
        return {"pos": [round(self.px,2), round(self.py,2)], "angle": round(self.ang,2),
                "score": self.score, "won": self.won}

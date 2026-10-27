import math
import random

from vga32.game import GameApp

NEON = ["cyan", "sky", "white", "lime"]


class BoidsSwarm(GameApp):
    app_id = "games.boids"
    title = "Boids Swarm"
    icon = "triangles"
    category = "Games"
    width, height = 620, 340
    fps = 30

    def start(self):
        random.seed()
        self.n = 90
        self.b = [
            dict(
                x=random.uniform(40, self.width - 40),
                y=random.uniform(40, self.height - 40),
                a=random.uniform(0.0, 2.0 * math.pi),
                s=random.uniform(1.3, 2.1),
            )
            for _ in range(self.n)
        ]
        self.paused = False
        self.score = 0

    def update(self, dt):
        if self.pressed("space"):
            self.paused = not self.paused
        if self.pressed("r"):
            self.start()
            return
        if self.paused:
            return
        w, h = self.width, self.height
        m = 70.0  # soft wall margin
        for p in self.b:
            ax = ay = cx = cy = 0.0
            cnt = 0
            for q in self.b:
                if q is p:
                    continue
                dx = q["x"] - p["x"]
                dy = q["y"] - p["y"]
                d2 = dx * dx + dy * dy
                if d2 < 1900.0:
                    ax += math.cos(q["a"])
                    ay += math.sin(q["a"])
                    cnt += 1
                    if d2 < 160.0:
                        d = math.sqrt(d2)
                        if d > 0.5:
                            cx -= dx / d
                            cy -= dy / d
            if cnt:
                p["a"] += 0.10 * math.sin(math.atan2(ay, ax) - p["a"])
            if cx or cy:
                p["a"] += 0.35 * math.sin(math.atan2(cy, cx) - p["a"])
            ex = 0.0
            ey = 0.0
            if p["x"] < m:
                ex = (m - p["x"]) / m
            elif p["x"] > w - m:
                ex = -(p["x"] - (w - m)) / m
            if p["y"] < m:
                ey = (m - p["y"]) / m
            elif p["y"] > h - m:
                ey = -(p["y"] - (h - m)) / m
            if ex or ey:
                p["a"] += 0.22 * math.sin(math.atan2(ey, ex) - p["a"])
            p["x"] += math.cos(p["a"]) * p["s"]
            p["y"] += math.sin(p["a"]) * p["s"]
            if p["x"] < 2 or p["x"] > w - 2:
                p["a"] = -p["a"]
                p["x"] = min(max(p["x"], 2), w - 2)
            if p["y"] < 2 or p["y"] > h - 2:
                p["a"] = math.pi - p["a"]
                p["y"] = min(max(p["y"], 2), h - 2)

    def render(self, g):
        g.clear("black")
        pi2 = 2.0 * math.pi
        for p in self.b:
            c = NEON[int((p["a"] % pi2) / (math.pi / 2.0)) % 4]
            x = p["x"]
            y = p["y"]
            a = p["a"]
            ca, sa = math.cos(a), math.sin(a)
            g.line(int(x), int(y), int(x - 5 * ca), int(y - 5 * sa), color=c, width=2)
            bx, by = x - 3 * ca, y - 3 * sa
            for w2 in (2.4, -2.4):
                g.line(
                    int(bx), int(by),
                    int(bx - 2.6 * math.cos(a + w2)), int(by - 2.6 * math.sin(a + w2)),
                    color=c, width=1,
                )
        g.frame(0, 0, self.width, self.height, color="navy")
        g.text(6, 4, "BOIDS", color="yellow", size="small")
        g.text(6, self.height - 14, "space=pause  r=reset", color="darkgray", size="small")
        if self.paused:
            g.text(self.width // 2, 24, "PAUSED", color="red", size="medium", center=True)

    def game_state(self):
        return {
            "boids": self.n,
            "paused": self.paused,
        }

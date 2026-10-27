
from vga32.game import GameApp
import random

class RoadDodge3D(GameApp):
    app_id = "games.road_dodge"
    title = "3D Road Dodge"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 24

    def start(self):
        self.player = 0.0
        self.speed = 1.0
        self.score = 0
        self.lives = 3
        self.over = False
        self.obstacles = []
        self.spawn_t = 0.0
        self.t = 0.0
        self.horizon = 110

    def spawn(self):
        self.obstacles.append({"lane": random.choice([-0.7,-0.35,0.0,0.35,0.7]), "z": 1.0, "color": random.choice(["red","orange","yellow"])})

    def lane_to_x(self, lane, z):
        scale = 1.0 / (z + 0.25)
        return int(self.width / 2 + lane * 130 * scale * 0.35)

    def size_for_z(self, z):
        scale = 1.0 / (z + 0.25)
        return max(4, int(18 * scale * 0.35)), max(4, int(12 * scale * 0.35))

    def update(self, dt):
        if self.pressed("r"):
            self.start()
            return
        if self.over:
            return
        self.t += dt
        if self.held("left") or self.held("a"):
            self.player -= 2.4 * dt
        if self.held("right") or self.held("d"):
            self.player += 2.4 * dt
        self.player = max(-0.85, min(0.85, self.player))
        if self.pressed("up") or self.pressed("w"):
            self.speed = min(2.0, self.speed + 0.2)
        if self.pressed("down") or self.pressed("s"):
            self.speed = max(0.6, self.speed - 0.2)
        self.spawn_t += dt
        if self.spawn_t > max(0.5, 1.3 / self.speed):
            self.spawn_t = 0.0
            self.spawn()
        for ob in self.obstacles:
            ob["z"] -= 0.18 * self.speed * dt * (1.0 / (ob["z"] + 0.2))
        remaining = []
        for ob in self.obstacles:
            if ob["z"] <= 0.08:
                sx = self.lane_to_x(ob["lane"], 0.08)
                px = self.width / 2 + self.player * 130
                w, h = self.size_for_z(0.08)
                if abs(sx - px) < (w + 16) / 2:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.over = True
                else:
                    self.score += 10
            else:
                remaining.append(ob)
        self.obstacles = remaining

    def render(self, g):
        g.clear("sky")
        g.rect(0, self.horizon, self.width, self.height - self.horizon, "darkgray")
        g.line(0, self.horizon, self.width, self.horizon, "black", 1)
        g.poly([(30, self.height), (self.width-30, self.height),
                (self.width//2+55, self.horizon), (self.width//2-55, self.horizon)], "gray")
        g.line(30, self.height, self.width//2-55, self.horizon, "white", 1)
        g.line(self.width-30, self.height, self.width//2+55, self.horizon, "white", 1)
        for i in range(1, 6):
            t = i / 6.0
            y = int(self.horizon + (self.height - self.horizon) * (1 - t))
            x1 = int(self.width//2 - 60*(1 - t))
            x2 = int(self.width//2 + 60*(1 - t))
            g.line(x1, y, x2, y, "white", 1)
        for ob in sorted(self.obstacles, key=lambda o: o["z"], reverse=True):
            z = ob["z"]
            sx = self.lane_to_x(ob["lane"], z)
            sy = int(self.horizon + (self.height - self.horizon - 40) * (1 - z))
            w, h = self.size_for_z(z)
            g.rect(sx - w//2, sy, w, h, ob["color"], outline="black")
        px = int(self.width / 2 + self.player * 130)
        g.rect(px - 10, self.height - 34, 20, 18, "blue", outline="white")
        g.rect(px - 4, self.height - 30, 8, 8, "cyan")
        g.text(4, 4, f"Score {self.score}  Lives {self.lives}  Speed {self.speed:.1f}x", "white", size="small")
        if self.over:
            g.text(self.width//2, self.height//2, "CRASH!", "red", size="big", center=True)
            g.text(self.width//2, self.height//2 + 24, "Press R", "yellow", size="small", center=True)

    def game_state(self):
        return {"score": self.score, "lives": self.lives, "speed": round(self.speed, 2), "over": self.over, "obstacles": len(self.obstacles)}

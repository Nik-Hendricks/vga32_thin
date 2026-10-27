from vga32.game import GameApp
import random
import math
import time

class DragonHydra(GameApp):
    app_id = "games.dragon_hydra"
    title = "Dragon Hydra"
    icon = "triangles"
    category = "Games"
    width, height = 320, 200
    fps = 18
    background = "navy"

    def start(self):
        self.x = 120.0
        self.y = 118.0
        self.tx = 120.0
        self.ty = 118.0
        self.facing = 1.0
        self.mood = "idle"
        self.mood_until = 0.0
        self.roar_timer = time.time()
        self.roam_timer = time.time()
        self.time = 0.0
        self.frame = 0.0
        self.fire = []
        self.spawn_idle_roar()
        # state helpers
        self.eye_side = 0.0

    def clamp(self, v, lo, hi):
        return max(lo, min(hi, v))

    def spawn_idle_roar(self):
        self.mood = "roar"
        self.mood_until = time.time() + 1.5
        self.roar_timer = time.time()

    def spawn_fire(self):
        now = time.time()
        self.mood = "breathe"
        self.mood_until = now + 3.0
        for m in range(3):
            head_idx = m
            head_x = self.x + 44 + head_idx * 6 * self.facing
            head_y = self.y - 18 + head_idx * 4
            for _ in range(6):
                speed = (2.8 + random.random() * 1.5) * self.facing
                vy = random.uniform(-0.9, 0.9) + (head_idx - 1) * 0.15
                self.fire.append({"x": head_x + 12 * self.facing, "y": head_y, "vx": speed, "vy": vy, "life": 3.0 + random.random(), "age": 0.0, "c": random.choice(["yellow", "orange", "red", "white"])})
        for _ in range(3):
            self.fire.append({"x": self.x + 10 * self.facing, "y": self.y - 6, "vx": (1.3 + random.random()) * self.facing, "vy": random.uniform(-1.2, 1.2), "life": 4.2, "age": 0.0, "c": "orange"})

    def update(self, dt):
        dt = min(dt, 0.08) if dt > 0 else 0.0
        now = time.time()
        self.time += dt
        self.frame += dt * (2.0 if self.mood != "idle" else 0.9)

        if self.pressed("escape"):
            self.mood = "idle"
            self.mood_until = 0.0
        if self.pressed("r"):
            self.start()
            return

        if self.pressed("space"):
            self.mood = "roar"
            self.mood_until = now + 2.0
            self.roar_timer = now
            for _ in range(4):
                self.fire.append({"x": self.x - 12 * self.facing, "y": self.y - 2, "vx": (-1.8 * self.facing) + random.uniform(-0.5, 0.5), "vy": random.uniform(-0.7, 0.7), "life": 1.6, "age": 0.0, "c": "purple"})
        if self.pressed("f") or self.pressed("enter"):
            self.spawn_fire()
        if self.pressed("a"):
            self.mood = "attack"
            self.mood_until = now + 1.8

        if self.mood in ("roar", "breathe", "attack") and self.mood_until and now >= self.mood_until:
            self.mood = "idle"
            self.mood_until = 0.0

        dx = self.axis("right", "left")
        dy = self.axis("down", "up")
        if dx or dy:
            self.tx += dx * 34 * dt
            self.ty += dy * 34 * dt
            self.tx = self.clamp(self.tx, 48, self.width - 48)
            self.ty = self.clamp(self.ty, 78, self.height - 70)

        if self.mood == "idle":
            if now - self.roam_timer > 5.0:
                self.tx = random.uniform(64, self.width - 64)
                self.ty = random.uniform(94, self.height - 74)
                self.roam_timer = now
            if now - self.roar_timer > 8.0:
                self.spawn_idle_roar()

        vx = self.tx - self.x
        vy = self.ty - self.y
        dist = (vx * vx + vy * vy) ** 0.5
        speed = 28 + (18 if self.mood in ("attack", "breathe") else 0)
        if dist > 3:
            self.x += vx / dist * speed * dt
            self.y += vy / dist * speed * dt
            if vx > 1:
                self.facing = 1.0
            elif vx < -1:
                self.facing = -1.0
            if self.mood not in ("roar", "breathe", "attack"):
                self.mood = "walk"
        else:
            if self.mood == "walk":
                self.mood = "idle"
        self.x = self.clamp(self.x, 36.0, self.width - 36.0)
        self.y = self.clamp(self.y, 96.0, self.height - 44.0)

        # fire particles
        for p in self.fire:
            p["x"] += p["vx"] * 4 * dt
            p["y"] += p["vy"] * 4 * dt
            p["age"] += dt
            p["vx"] *= 0.985
            p["vy"] += random.uniform(-0.1, 0.1) * dt
        self.fire = [p for p in self.fire if p["age"] < p["life"] and 0 <= p["x"] <= self.width and 0 <= p["y"] <= self.height]

    def draw_tail(self, g, cx, cy, face, phase):
        segments = 9
        for i in range(segments):
            tx = cx - (i + 1) * 8 * face
            sway = math.sin(self.frame + i * 0.35) * (5 if self.mood not in ("roar", "attack") else 11)
            ty = cy + sway + (i * 0.4)
            thick = 7 - i * 0.5
            g.rect(int(tx), int(ty), int(thick), int(thick), "maroon")
        # tip
        tailx = cx - segments * 8 * face
        tailsway = math.sin(self.frame + segments * 0.35) * 4
        g.circle(int(tailx), int(cy + tailsway), 5, "red")

    def draw_head(self, g, hx, hy, face, index=0):
        mood = self.mood
        head_color = "maroon"
        if mood in ("roar", "breathe", "attack"):
            head_color = "red"
        # head
        g.rect(int(hx - 12), int(hy - 9), 24, 18, head_color)
        # muzzle
        g.rect(int(hx + 6 * face), int(hy - 5), 14 * face, 12, head_color)
        # horn
        g.line(int(hx + 2 * face), int(hy - 9), int(hx + 8 * face), int(hy - 22), "yellow", width=2)
        g.circle(int(hx + 8 * face), int(hy - 22), 2, "red")
        # eyes
        ex = int(hx - 2 if face > 0 else hx + 2)
        g.circle(ex, int(hy - 2), 3, "yellow")
        if mood in ("roar", "attack"):
            g.circle(ex, int(hy - 2), 1, "red")
            g.line(int(ex - 3), int(hy - 4), int(ex - 1), int(hy - 2), "black", width=1)
            g.line(int(ex + 1), int(hy - 2), int(ex + 3), int(hy - 4), "black", width=1)
        else:
            g.circle(ex, int(hy - 2), 1, "black")
        # sparks in mouth if breathe
        if mood == "breathe":
            for k in (0, 1, 2):
                g.circle(int(hx + 16 * face + k * 3 * face), int(hy + k - 2), 1, "yellow")
        # roar mouth open
        if mood in ("roar", "breathe", "attack"):
            g.rect(int(hx + (8 if face > 0 else -14)), int(hy + 2), 8, 6, "black")
            g.line(int(hx + (8 if face > 0 else -16)), int(hy + 3), int(hx + (16 if face > 0 else -8)), int(hy + 5), "yellow", width=1)
        else:
            g.circle(int(hx + 8 * face), int(hy + 1), 2, "black")
        # neck
        nx = int(hx - 22 * face)
        ny = int(hy + 8)
        g.line(int(self.x + (10 * face)), int(self.y - 24), nx, ny, head_color, width=4)

    def render(self, g):
        g.clear("navy")
        # background
        for i in range(4):
            g.circle(30 + i * 84, 15, 5, "gray")
        # ground
        g.rect(0, 162, self.width, 38, "green")
        g.rect(0, 178, self.width, 22, "darkgray")
        # island rock
        g.rect(0, 148, self.width, 18, "#5b4a2a")
        g.rect(8, 154, 14, 6, "brown" if False else "orange")
        g.rect(self.width - 22, 152, 10, 8, "gray")

        face = self.facing
        cx = int(self.x)
        cy = int(self.y)
        phase = math.sin(self.frame * 3.3) * 3

        # wings
        wing_color = "darkgray"
        wing_y = int(cy - 24 + phase / 2)
        if face > 0:
            pts = [(cx - 6, wing_y + 12), (cx - 56, wing_y - 22), (cx - 32, wing_y - 56)]
        else:
            pts = [(cx + 6, wing_y + 12), (cx + 56, wing_y - 22), (cx + 32, wing_y - 56)]
        # draw via line triangle
        for a, b in zip(pts, pts[1:] + pts[:1]):
            g.line(a[0], a[1], b[0], b[1], wing_color, width=2)
        # wing fill blob
        for i in range(20):
            lx = (pts[0][0] * (20 - i) + pts[1][0] * i) // 20
            ly = (pts[0][1] * (20 - i) + pts[1][1] * i) // 20
            for j in range(5):
                g.pixel(lx + j * (1 if face > 0 else -1), ly - j * 2, "darkgray")
        # legs
        for lx in (-10, 10):
            g.rect(cx + lx, cy + 16, 6, 16, "maroon")
            g.rect(cx + lx, cy + 28, 6, 4, "gray")
        # tail
        self.draw_tail(g, cx, cy, face, phase)

        # body
        g.circle(cx, cy, 26, "darkgray")
        g.circle(cx, cy - 6, 20, "maroon")
        g.circle(cx + (6 * face), cy - 8, 13, "#a61b1b")
        g.circle(cx - (5 * face), cy - 10, 11, "maroon")
        # belly scales
        for i in range(5):
            g.rect(int(cx - 12 + i * 6 * face), int(cy - 2 + i), 3, 2, "orange")

        # front limbs
        lhx = cx + 16 * face
        lhy = cy + 2
        g.rect(int(lhx - 4), int(lhy), 6, 14, "maroon")
        g.circle(int(lhx - 6), lhy + 16, 3, "orange")
        g.circle(int(lhx + 4), lhy + 16, 3, "orange")
        g.line(int(lhx - 4), lhy + 16, int(lhx - 7), lhy + 6, "red", width=1)

        # heads array (hydra style)
        heads = [
            (cx + 30 * face, cy - 26),
            (cx + 44 * face, cy - 12),
            (cx + 26 * face, cy - 48),
        ]
        # necks drawn before heads
        for hx, hy in heads:
            g.line(cx + 4 * face, cy - 20, hx, hy, "maroon", width=4)
            g.line(cx + 4 * face, cy - 20, hx, hy, "purple", width=1)
        # breathe action stagger phase per head
        for idx, (hx, hy) in enumerate(heads):
            if face < 0:
                hx = cx - (abs(hx - cx))
            self.draw_head(g, hx, hy, face, idx)

        # body ridges
        for i in range(6):
            g.rect(int(cx - 16 + i * (6 if i else 0) * (1 if face > 0 else -1)), int(cy - 22 + i * 2), 6, 3, "yellow")

        # fire particles
        for p in self.fire:
            w = int(2 + p["age"])
            g.circle(int(p["x"]), int(p["y"]), w, p["c"])
            if p["c"] in ("orange", "red"):
                g.circle(int(p["x"]), int(p["y"]), 1, "white")
        # roar text
        if self.mood in ("roar", "attack", "breathe"):
            sn = "RAWR!" if self.mood == "roar" else "ZZAP!" if self.mood == "attack" else "FIIIIRE!"
            g.text(cx - 24, cy - (80 if self.mood != "breathe" else 58), sn, "yellow", size="medium")

        # controls
        g.text(4, self.height - 24, "Arrows move  Space roar  F fire  A attack  R reset", "white", size="small")
        g.text(4, 4, "Dragon Hydra hybrid", "white", size="small")

    def game_state(self):
        return {
            "x": int(self.x),
            "y": int(self.y),
            "mood": self.mood,
            "fire": len(self.fire),
            "heads": 3,
            "facing": self.facing,
        }

from vga32.game import GameApp
import random
import time

class PixelPet(GameApp):
    app_id = "games.pixel_pet"
    title = "Pixel Pet"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 16

    def start(self):
        self.x = 160.0
        self.y = 148.0
        self.tx = 160.0
        self.ty = 148.0
        self.facing = 1.0
        self.frame = 0.0
        self.blink = 0
        self.mood = "idle"
        self.mood_until = 0.0
        self.speech = ""
        self.energy = 90.0
        self.hunger = 20.0
        self.thirst = 18.0
        self.happiness = 90.0
        self.stress = 8.0
        self.clean = 92.0
        self.particles = []
        self.toy = None
        self.food = (84.0, 176.0)
        self.pond = (238.0, 176.0)
        self.roam_timer = time.time()
        self.last_decay = time.time()
        self.last_interact = time.time()
        self.day = 0.0
        self.eye_state = 0
        self.sleeping = False

    def pet(self):
        self.happiness = min(100.0, self.happiness + 9.0)
        self.stress = max(0.0, self.stress - 6.0)
        self.add_particle(self.x, self.y - 24.0, "family")
        self.mood = "play"
        self.mood_until = time.time() + 4.0
        self.speech = "pet!"
        self.last_interact = time.time()

    def feed(self):
        self.hunger = max(0.0, self.hunger - 28.0)
        self.energy = min(100.0, self.energy + 12.0)
        self.happiness = min(100.0, self.happiness + 5.0)
        self.tx, self.ty = self.food
        self.mood = "eat"
        self.mood_until = time.time() + 6.0
        self.speech = "nom"
        self.last_interact = time.time()
        self.add_particle(self.tx, self.ty - 18.0, "food")

    def water(self):
        self.thirst = max(0.0, self.thirst - 32.0)
        self.energy = min(100.0, self.energy + 8.0)
        self.happiness = min(100.0, self.happiness + 3.0)
        self.tx, self.ty = self.pond
        self.mood = "drink"
        self.mood_until = time.time() + 6.0
        self.speech = "sip"
        self.last_interact = time.time()
        self.add_particle(self.tx, self.ty - 18.0, "water")

    def play(self):
        self.happiness = min(100.0, self.happiness + 12.0)
        self.energy = max(0.0, self.energy - 7.0)
        self.stress = max(0.0, self.stress - 3.0)
        self.mood = "play"
        self.mood_until = time.time() + 6.0
        self.toy = [random.uniform(70.0, 250.0), 152.0]
        self.tx, self.ty = self.toy
        self.speech = "whee"
        self.last_interact = time.time()
        self.add_particle(self.toy[0], self.toy[1], "toy")

    def sleep(self):
        self.mood = "sleep"
        self.mood_until = time.time() + 16.0
        self.speach = "zzz"
        self.speech = "zzz"
        self.last_interact = time.time()

    def wake(self):
        self.energy = min(100.0, self.energy + 18.0)
        self.stress = max(0.0, self.stress - 4.0)
        self.mood = "idle"
        self.mood_until = 0.0
        self.speech = "awake"
        self.last_interact = time.time()

    def reset(self):
        self.start()

    def clamp(self, v, lo, hi):
        return max(lo, min(hi, v))

    def update(self, dt):
        dt = min(dt, 0.08) if dt > 0 else 0.0
        now = time.time()

        if self.pressed("escape"):
            self.mood = "idle"
            self.mood_until = 0.0
        if self.pressed("r"):
            self.reset()
            return
        if self.pressed("enter") or self.pressed("space"):
            if self.mood == "sleep":
                self.wake()
            else:
                self.pet()
            return
        if self.pressed("f"):
            self.feed()
            return
        if self.pressed("w"):
            self.water()
            return
        if self.pressed("p"):
            self.play()
            return
        if self.pressed("s"):
            self.sleep()
            return

        if self.mood in ("sleep", "eat", "drink", "play") and self.mood_until and now >= self.mood_until:
            self.mood = "idle"
            self.mood_until = 0.0
            self.speech = ""
            self.toy = None

        # movement keys set target
        dx = self.axis("right", "left")
        dy = self.axis("down", "up")
        if dx or dy:
            self.tx += dx * 22.0 * dt
            self.ty += dy * 22.0 * dt
            self.tx = self.clamp(self.tx, 30.0, self.width - 30.0)
            self.ty = self.clamp(self.ty, 90.0, self.height - 34.0)

        # auto idle roaming target
        if self.mood == "idle":
            if now - self.roam_timer > 4.5:
                self.toy = None
                self.tx = random.uniform(48.0, self.width - 48.0)
                self.ty = random.uniform(106.0, self.height - 44.0)
                self.roam_timer = now

        # move toward target
        vx = self.tx - self.x
        vy = self.ty - self.y
        distance = (vx * vx + vy * vy) ** 0.5
        speed = 38.0 + self.energy * 0.32
        if self.mood == "sleep":
            speed = 5.0
        if distance > 3.0:
            self.x += vx / distance * speed * dt
            self.y += vy / distance * speed * dt
            if vx > 1:
                self.facing = 1.0
            elif vx < -1:
                self.facing = -1.0
            if self.mood not in ("sleep", "eat", "drink", "play"):
                self.mood = "walk"
        else:
            if self.mood == "walk":
                self.mood = "idle"

        # bouncing and clamp
        self.x = self.clamp(self.x, 24.0, self.width - 24.0)
        self.y = self.clamp(self.y, 85.0, self.height - 26.0)

        if abs(self.tx - self.x) > 5 or abs(self.ty - self.y) > 5:
            self.mood = "walk" if self.mood == "idle" else self.mood

        # stats decay
        if now - self.last_decay > 1.0:
            self.last_decay = now
            self.hunger = self.clamp(self.hunger + 0.28, 0.0, 100.0)
            self.thirst = self.clamp(self.thirst + 0.34, 0.0, 100.0)
            if distance > 3:
                self.energy = self.clamp(self.energy - 0.35, 0.0, 100.0)
            else:
                self.energy = self.clamp(self.energy - 0.08, 0.0, 100.0)
            self.happiness = self.clamp(self.happiness - 0.22, 0.0, 100.0)
            self.clean = self.clamp(self.clean - 0.1, 0.0, 100.0)
            if self.hunger > 70 or self.thirst > 70:
                self.stress = self.clamp(self.stress + 0.9, 0.0, 100.0)
            else:
                self.stress = self.clamp(self.stress - 0.25, 0.0, 100.0)
            # auto nap if tired/hungry
            if self.mood == "idle" and not self.sleeping and (self.energy < 18 or self.hunger > 90 or self.thirst > 90):
                self.sleep()
            if self.mood == "sleep":
                self.energy = self.clamp(self.energy + 1.0, 0.0, 100.0)
                self.stress = self.clamp(self.stress - 0.6, 0.0, 100.0)

        # blink
        self.frame += dt * 2.5
        if now - self.blink > 3.2:
            self.blink = now
        if self.blink > 0 and now - self.blink < 0.12:
            self.eye_state = 2
        elif self.blink > 0 and now - self.blink < 0.23:
            self.eye_state = 1
        else:
            self.eye_state = 0

        # particles
        for p in self.particles:
            p["age"] += dt
            p["y"] -= 18 * dt
            p["x"] += (14 * dt) if p["kind"] in ("food",) else 0
        self.particles = [p for p in self.particles if p["age"] < p["life"]]

        self.time += dt

    def add_particle(self, x, y, kind):
        if len(self.particles) < 14:
            self.particles.append({"x": float(x), "y": float(y), "kind": kind, "age": 0.0, "life": 4.0})

    def render(self, g):
        g.clear("navy")
        # environment
        g.rect(0, 128, self.width, 72, "green")
        g.rect(0, 160, self.width, 40, "green")
        # pond
        g.circle(int(self.pond[0]), int(self.pond[1] + 4), 26, "blue")
        g.circle(int(self.pond[0]), int(self.pond[1] + 4), 18, "teal")
        g.circle(int(self.pond[0]), int(self.pond[1] + 4), 10, "sky")
        # food bowl
        g.rect(int(self.food[0] - 14), int(self.food[1] - 6), 28, 12, "#8b5a2b")
        g.rect(int(self.food[0] - 10), int(self.food[1] - 4), 8, 4, "orange")
        g.rect(int(self.food[0] + 2), int(self.food[1] - 4), 8, 4, "yellow")
        # grass flowers
        for i in range(6):
            g.pixel(30 + i * 48, 146, "yellow")
            g.pixel(33 + i * 48, 144, "purple")
        # toy
        if self.toy:
            g.circle(int(self.toy[0]), int(self.toy[1]), 5, "yellow", outline="orange")
            g.circle(int(self.toy[0] - 1), int(self.toy[1] - 1), 1, "white")
        # particles
        for p in self.particles:
            fade = max(1, int(4 - p["age"]))
            if p["kind"] == "family":
                g.circle(int(p["x"]), int(p["y"]), fade, "purple")
                g.circle(int(p["x"] + 2), int(p["y"]), fade, "purple")
            elif p["kind"] == "food":
                g.circle(int(p["x"]), int(p["y"]), fade, "orange")
            elif p["kind"] == "water":
                g.circle(int(p["x"]), int(p["y"]), fade, "sky")
            elif p["kind"] == "toy":
                g.circle(int(p["x"]), int(p["y"]), fade, "yellow")
            else:
                g.circle(int(p["x"]), int(p["y"]), fade, "white")
        # creature
        cx = int(self.x)
        cy = int(self.y)
        r = 11
        if self.mood == "sleep":
            r = 12
        body_color = "cyan"
        if self.mood == "sleep":
            body_color = "blue"
        elif self.stress > 60:
            body_color = "purple"
        elif self.energy < 30:
            body_color = "red"
        # stress halo
        if self.stress > 60:
            g.circle(cx, cy, r + 5, "red", outline="red")
        # body shells
        g.circle(cx, cy, r + 3, "blue" if body_color != "blue" else "darkgray")
        g.circle(cx, cy, r, body_color)
        # tail
        bend = int(3 * (1 if self.mood in ("eat", "water", "play") else 0))
        if self.mood == "sleep":
            tail_phase = int(0)
        else:
            tail_phase = int(3 * __import__("math").sin(self.frame * 1.7))
        tail_dir = 1 if self.facing > 0 else -1
        x1 = cx - int(3 * self.facing)
        y1 = cy + r
        points = [
            (cx, cy),
            (cx - 6 * tail_dir, cy + 8 + tail_phase),
            (cx - 10 * tail_dir, cy + 2 + tail_phase),
            (cx - 14 * tail_dir, cy - 3 + tail_phase),
        ]
        for i in range(3):
            g.line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], body_color, width=2)
        # eyes white
        g.circle(cx - int(3 * self.facing), cy - 2, 3, "white")
        g.circle(cx + int(3 * self.facing), cy - 2, 3, "white")
        # blink overlays
        if self.eye_state >= 1 or self.mood == "sleep":
            if self.eye_state >= 2 or self.mood == "sleep":
                g.line(cx - 5, cy - 2, cx - 1, cy - 2, "black", width=1)
                g.line(cx + 1, cy - 2, cx + 5, cy - 2, "black", width=1)
        else:
            g.circle(cx - int(3 * self.facing), cy - 2, 1, "black")
            g.circle(cx + int(3 * self.facing), cy - 2, 1, "black")
        # ant
        ant_x = int(cx + 4 * self.facing)
        ant_y = int(cy - r - 10)
        g.line(cx, cy - r + 1, ant_x, ant_y, "white", width=1)
        g.circle(ant_x, ant_y - 2, 2, "purple" if self.mood == "play" else "white")
        # mouth
        if self.mood in ("eat", "drink"):
            g.circle(cx, cy + 3, 2, "black")
        elif self.mood == "play":
            g.line(cx - 3, cy + 3, cx, cy + 5, "black", width=1)
            g.line(cx + 3, cy + 3, cx, cy + 5, "black", width=1)
        elif self.mood == "sleep":
            g.line(cx - 2, cy + 4, cx + 2, cy + 4, "black", width=1)
        elif self.happiness < 40:
            g.line(cx - 3, cy + 4, cx, cy + 2, "black", width=1)
            g.line(cx, cy + 2, cx + 3, cy + 4, "black", width=1)
        else:
            g.circle(cx, cy + 3, 2, "black")
        # legs
        bounce = 0
        if self.mood in ("walk", "eat", "drink", "play"):
            bounce = int(__import__("math").sin(self.frame * 4.2) * 2)
        for lx in (-4, 4):
            b = bounce if lx > 0 else -bounce
            g.rect(cx + lx - 1, cy + r - 1 + b, 2, 3, body_color)
        # speech
        if self.speech:
            # small bubble
            g.rect(cx - 24, cy - r - 22, 48, 14, "gray")
            g.rect(cx - 22, cy - r - 20, 44, 10, "white")
            g.text(cx - 18, cy - r - 20, self.speech, "black", size="small")
        # stats text
        top = 4
        g.text(4, top, "Pixel Pet", "white", size="small")
        g.text(4, 16, f"energy {int(self.energy)}  hunger {int(self.hunger)}", "white", size="small")
        g.text(4, 28, f"thirst {int(self.thirst)}  happy {int(self.happiness)}  stress {int(self.stress)}", "white", size="small")
        g.text(4, self.height - 26, "Arrows move  Enter/Pet  F feed  W water  P play  S sleep  R reset", "white", size="small")

    def game_state(self):
        return {
            "x": int(self.x),
            "y": int(self.y),
            "mood": self.mood,
            "energy": round(self.energy, 1),
            "hunger": round(self.hunger, 1),
            "thirst": round(self.thirst, 1),
            "happiness": round(self.happiness, 1),
            "stress": round(self.stress, 1),
            "clean": round(self.clean, 1),
            "particles": len(self.particles),
            "toy": bool(self.toy),
        }

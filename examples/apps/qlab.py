import time
import numpy as np
from vga32.game import GameApp

GW, GH = 28, 18
CELL = 20
W = GW * CELL
H = GH * CELL
ACTS = ((1, 0), (-1, 0), (0, 1), (0, -1))
RAMP = ["black", "navy", "blue", "sky", "cyan", "green", "lime"]
MSNAMES = {1: "two gates", 2: "serpentine", 3: "maze"}


class QLab(GameApp):
    app_id = "data.qlab"
    title = "Q-Learning"
    icon = "star"
    category = "Data"
    width, height = 620, 340
    fps = 60

    def start(self):
        self.rng = np.random.default_rng(7)
        self.heat = {}
        self.playing = True
        self.trail = True
        self.spf = 4
        self.camx, self.camy = W / 2.0, H / 2.0
        self.zoom = 1.08
        self._now = time.time()
        self._msg = ""
        self._mexp = 1e9
        self._newmap(1)
        self.splash("q-learning: watch the value map bloom to the goal", 6.0)

    def splash(self, t, secs=3.5):
        self._msg = t
        self._mexp = self._now + secs

    def _newmap(self, key, reset_q=True):
        walls = set()
        if key == 1:
            for y in range(GH):
                if y not in (4, 5, 13, 14):
                    walls.add((9, y))
                    walls.add((18, y))
            start, goal = (2, 9), (25, 8)
        elif key == 2:
            for y in range(GH):
                if y != 2:
                    walls.add((7, y))
                if y != 15:
                    walls.add((14, y))
                if y != 4:
                    walls.add((21, y))
            start, goal = (2, 10), (25, 7)
        else:
            for x in range(4, 12):
                if x != 8:
                    walls.add((x, 4))
            for y in range(4, 12):
                if y != 8:
                    walls.add((16, y))
            for x in range(16, 25):
                if x != 20:
                    walls.add((x, 14))
            start, goal = (3, 15), (24, 3)
        self.walls = walls
        self.mapkey = key
        self.mapname = MSNAMES[key]
        self.start = start
        self.goal = goal
        self.agent = start
        self.q = np.zeros((GH, GW, 4), dtype=float)
        self.eps = 1.0
        self.alpha = 0.9
        self.steps = 0
        self.episodes = 0
        self.ep_steps = 0
        self.best = None
        self.heat = {}
        if reset_q:
            self.splash(self.mapname + "  map reset", 3.0)

    def _step(self):
        ax, ay = self.agent
        self.eps = max(0.05, self.eps * 0.999)
        self.alpha = max(0.04, self.alpha * 0.999)
        if self.rng.random() < self.eps:
            a = int(self.rng.integers(4))
        else:
            a = int(self.q[ay, ax].argmax())
        nx, ny = ax + ACTS[a][0], ay + ACTS[a][1]
        blocked = not (0 <= nx < GW and 0 <= ny < GH) or (nx, ny) in self.walls
        got = False
        if blocked:
            rew = -0.3
        else:
            got = (nx == self.goal[0] and ny == self.goal[1])
            if got:
                rew = 1.0
            else:
                d0 = abs(ax - self.goal[0]) + abs(ay - self.goal[1])
                d1 = abs(nx - self.goal[0]) + abs(ny - self.goal[1])
                rew = 0.02 if d1 < d0 else (-0.03 if d1 == d0 else -0.06)
        cur = float(self.q[ay, ax, a])
        if blocked:
            target = rew
        else:
            target = rew + 0.95 * float(self.q[ny, nx].max())
        self.q[ay, ax, a] = cur + self.alpha * (target - cur)
        self.agent = self.agent if blocked else (nx, ny)
        self.steps += 1
        self.ep_steps += 1
        if self.trail:
            self.heat[(self.agent[0], self.agent[1])] = 1.0
        if got or self.ep_steps >= 120:
            self.episodes += 1
            if got:
                if self.best is None or self.ep_steps < self.best:
                    self.best = self.ep_steps
                    self.splash("new best path: " + str(self.best) + " steps", 4.0)
            elif self.steps > 2000 and self.best is not None:
                pass
            self.agent = self.start
            self.ep_steps = 0

    def update(self, dt):
        self._now = time.time()
        if self._now > self._mexp and self._msg:
            self._msg = ""
        if self.pressed("space"):
            self.playing = not self.playing
            self.splash("paused" if not self.playing else "running", 2.0)
        if self.pressed("n"):
            self.playing = False
            self._step()
        if self.pressed(","):
            self.spf = max(1, self.spf - 1)
            self.splash("steps/frame " + str(self.spf), 2.0)
        if self.pressed("."):
            self.spf = min(32, self.spf + 2)
            self.splash("steps/frame " + str(self.spf), 2.0)
        for key in (1, 2, 3):
            if self.pressed(str(key)):
                self._newmap(key)
        if self.pressed("w"):
            self._newmap(self.mapkey)
        if self.pressed("t"):
            self.trail = not self.trail
            if not self.trail:
                self.heat = {}
        if self.pressed("r"):
            self.splash("reward reset: +1.0 goal", 2.0)
        if self.pressed("h"):
            self.camx, self.camy = W / 2.0, H / 2.0
            self.zoom = 1.08
            self.splash("home", 1.5)
        if self.pressed("x"):
            self.zoom = min(16.0, self.zoom * 1.35)
        if self.pressed("z"):
            self.zoom = max(1.0, self.zoom / 1.35)
        pan = (420.0 / self.zoom) * dt
        if self.held("left"):
            self.camx -= pan
        if self.held("right"):
            self.camx += pan
        if self.held("up"):
            self.camy -= pan
        if self.held("down"):
            self.camy += pan
        self.camx = max(0.0, min(float(W), self.camx))
        self.camy = max(0.0, min(float(H), self.camy))
        if self.playing:
            for _ in range(self.spf):
                self._step()
            if self.trail:
                for k in list(self.heat):
                    v = self.heat[k] * 0.96
                    if v < 0.2:
                        self.heat.pop(k)
                    else:
                        self.heat[k] = v

    def render(self, g):
        g.clear("black")
        zw = self.zoom
        cw, ch = self.width, self.height
        hx = cw / (2.0 * zw)
        hy = ch / (2.0 * zw)
        def sc(wx):
            return int((wx - self.camx) * zw + cw / 2)
        def scy(wy):
            return int((wy - self.camy) * zw + ch / 2)
        xs0 = max(0, int((self.camx - hx) / CELL))
        xs1 = min(GW, int((self.camx + hx) / CELL) + 1)
        ys0 = max(0, int((self.camy - hy) / CELL))
        ys1 = min(GH, int((self.camy + hy) / CELL) + 1)
        size = max(1, int(CELL * zw) - 1)
        for cy_ in range(ys0, ys1):
            for cx_ in range(xs0, xs1):
                if (cx_, cy_) in self.walls:
                    px, py = sc(cx_ * CELL), scy(cy_ * CELL)
                    g.rect(px, py, int(CELL * zw), int(CELL * zw), color="white")
                    continue
                if (cx_, cy_) == self.goal:
                    c = "orange"
                elif (cx_, cy_) == self.start:
                    c = "yellow"
                else:
                    v = float(self.q[cy_, cx_].max())
                    idx = max(0, min(len(RAMP) - 1, int((v / 1.05) * len(RAMP))))
                    c = RAMP[idx]
                    if c == "black":
                        continue
                px, py = sc(cx_ * CELL), scy(cy_ * CELL)
                g.rect(px, py, size, size, color=c)
        gx, gy = self.goal
        cx2, cy2 = sc(gx * CELL + CELL // 2), scy(gy * CELL + CELL // 2)
        g.line(cx2 - 5, cy2, cx2 + 5, cy2, color="white", width=2)
        g.line(cx2, cy2 - 5, cx2, cy2 + 5, color="white", width=2)
        sx, sy = self.start
        cx3, cy3 = sc(sx * CELL + CELL // 2), scy(sy * CELL + CELL // 2)
        g.rect(cx3 - 2, cy3 - 2, 5, 5, color="yellow")
        if self.trail and len(self.heat) <= 300:
            for (kx, ky), h in self.heat.items():
                px, py = sc(kx * CELL + CELL // 2), scy(ky * CELL + CELL // 2)
                if px < 0 or px > cw or py < 0 or py > ch:
                    continue
                g.rect(px - 1, py - 1, 3, 3, color="sky" if h < 0.5 else "cyan")
        ax, ay = self.agent
        px, py = sc(ax * CELL + CELL // 2), scy(ay * CELL + CELL // 2)
        g.rect(px - 3, py - 3, 7, 7, color="white")
        g.frame(0, 0, cw, ch, color="navy")
        best_txt = "  BEST " + str(self.best) if self.best else "  BEST --"
        g.text(6, 4, "STEPS " + str(self.steps) + "  EPS " + ("%.2f" % self.eps) + "  EP " + str(self.episodes) + best_txt,
               color="yellow", size="small")
        state = "LEARN" if self.playing else "PAUSED"
        g.text(6, self.height - 22, state + "  " + self.mapname + "  " + "S/F " + str(self.spf),
               color="lime" if state == "LEARN" else "red", size="small")
        if self._msg:
            g.text(self.width // 2, 16, self._msg, color="white", size="medium", center=True)
        g.text(6, self.height - 12, "space=pause n=1 step ,/.=speed w=reset-map 1-3=maps t=trail h=home", color="darkgray", size="small")
        g.text(6, self.height - 3, "x/z=zoom arrows=pan  white=wall  color=q-value  goal=brightest", color="darkgray", size="small")

    def game_state(self):
        return {
            "steps": self.steps,
            "eps": round(self.eps, 3),
            "episodes": self.episodes,
            "best": self.best,
            "map": self.mapname,
            "agent": list(self.agent),
        }

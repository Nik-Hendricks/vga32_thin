import time
import numpy as np
from vga32.game import GameApp

W, H = 512, 320
CCOLS = ["cyan", "lime", "yellow", "orange", "sky", "red", "purple", "green", "gray"]
TRAIRAMP = ["darkgray", "gray", "sky", "cyan"]


class KMeansApp(GameApp):
    app_id = "data.kmeans"
    title = "K-Means Lab"
    icon = "chat"
    category = "Data"
    width, height = 620, 340
    fps = 60

    def start(self):
        self.heat = {}
        self.playing = True
        self.trail = True
        self.settled = False
        self.iter = 0
        self.inertia = None
        self.speed = 2
        self.camx, self.camy = W / 2.0, H / 2.0
        self.zoom = 1.5
        self._now = time.time()
        self._msg = ""
        self._mexp = 1e9
        self._load(1)
        self.splash("k-means: centroids hunt the clusters", 6.0)

    def splash(self, t, secs=3.5):
        self._msg = t
        self._mexp = self._now + secs

    def _load(self, key):
        r = np.random.default_rng(200 + key)
        if key == 1:
            pts = []
            for cx, cy, s in [(150, 110, 26), (360, 95, 30), (170, 240, 30), (380, 235, 26)]:
                pts.append(r.normal(0, s, size=(185, 2)) + [cx, cy])
            data = np.vstack(pts)
            k = 4
            self.name = "4 blobs"
        elif key == 2:
            a = r.uniform(0, 2 * np.pi, 620)
            rad = 118 + r.normal(0, 7, 620)
            data = np.stack([rad * np.cos(a), rad * np.sin(a)], 1) + [W / 2, H / 2]
            k = 6
            self.name = "ring"
        elif key == 3:
            a1 = r.uniform(0, np.pi, 360)
            p1 = np.stack([170 + 115 * np.cos(a1), 200 - 55 * np.sin(a1)], 1) + r.normal(0, 4, (360, 2))
            a2 = r.uniform(np.pi, 2 * np.pi, 360)
            p2 = np.stack([350 + 115 * np.cos(a2), 140 - 40 * np.sin(a2)], 1) + r.normal(0, 4, (360, 2))
            data = np.vstack([p1, p2])
            k = 4
            self.name = "crescents"
        else:
            pts = []
            for i in range(8):
                cx = 75 + (i % 4) * 98
                cy = 75 + (i // 4) * 175
                pts.append(r.normal(0, 15, size=(100, 2)) + [cx, cy])
            data = np.vstack(pts)
            k = 8
            self.name = "8 blobs"
        self.data = np.clip(data, 6, [W - 6, H - 6])
        self.k = k
        r2 = np.random.default_rng(300 + key)
        self.cents = r2.uniform(25, [W - 25, H - 25], size=(k, 2))
        self.assign = np.zeros(len(self.data), dtype=int)
        self.iter = 0
        self.inertia = None
        self.settled = False
        self.tra = {j: [] for j in range(k)}
        self.splash(self.name + "  k=" + str(k) + "  " + str(len(self.data)) + " pts", 3.0)

    def _step(self):
        data = self.data
        D = ((data[:, None, :] - self.cents[None]) ** 2).sum(-1)
        a = D.argmin(1)
        moved = self.cents.copy()
        for j in range(self.k):
            sel = data[a == j]
            if len(sel):
                moved[j] = sel.mean(0)
                tr = self.tra[j]
                tr.append((int(float(moved[j][0])), int(float(moved[j][1]))))
                if len(tr) > 26:
                    tr.pop(0)
        self.cents = moved
        self.assign = a
        self.iter += 1
        inertia = float(D[np.arange(len(D)), a].sum())
        if self.inertia is not None and abs(self.inertia - inertia) < 0.03 * max(1e-9, self.inertia):
            if not self.settled:
                self.settled = True
                self.splash("settled  (inertia stable)", 4.0)
        else:
            self.settled = False
            self.inertia = inertia
        if self.inertia is None:
            self.inertia = inertia

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
            self.speed = max(1, self.speed - 1)
            self.splash("iters/frame " + str(self.speed), 2.0)
        if self.pressed("."):
            self.speed = min(10, self.speed + 1)
            self.splash("iters/frame " + str(self.speed), 2.0)
        if self.pressed("k"):
            self._bump_k(1)
        if self.pressed("l"):
            self._bump_k(-1)
        for key in (1, 2, 3, 4):
            if self.pressed(str(key)):
                self._load(key)
        if self.pressed("t"):
            self.trail = not self.trail
            if not self.trail:
                for j in list(self.tra):
                    self.tra[j] = []
        if self.pressed("h"):
            self.camx, self.camy = W / 2.0, H / 2.0
            self.zoom = 1.5
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
            for _ in range(self.speed):
                self._step()

    def _bump_k(self, d):
        nk = max(2, min(8, self.k + d))
        if nk == self.k:
            self.splash("k already " + str(nk), 1.5)
            return
        r = np.random.default_rng(400 + nk)
        self.k = nk
        self.cents = r.uniform(25, [W - 25, H - 25], size=(nk, 2))
        self.tra = {j: [] for j in range(nk)}
        self.iter = 0
        self.inertia = None
        self.settled = False
        self.splash("k=" + str(nk), 2.0)

    def render(self, g):
        g.clear("black")
        zw = self.zoom
        cw, ch = self.width, self.height
        hx = cw / (2.0 * zw)
        hy = ch / (2.0 * zw)
        x0 = int(self.camx - hx) - 2
        x1 = int(self.camx + hx) + 2
        y0 = int(self.camy - hy) - 2
        y1 = int(self.camy + hy) + 2
        def sx(x):
            return int((x - self.camx) * zw + cw / 2)
        def sy(y):
            return int((y - self.camy) * zw + ch / 2)
        data = self.data
        assign = self.assign
        stride = 3 if zw < 1.5 else (2 if zw < 3 else 1)
        for i in range(0, len(data), stride):
            p = data[i]
            px, py = sx(p[0]), sy(p[1])
            if px < -2 or px > cw + 2 or py < -2 or py > ch + 2:
                continue
            c = CCOLS[int(assign[i]) % len(CCOLS)]
            g.rect(px, py, 2, 2, color=c)
        if self.trail:
            for j in range(self.k):
                tr = self.tra[j]
                n = len(tr)
                if n < 2:
                    continue
                col = TRAIRAMP[min(n - 2, 3)]
                for (px_, py_) in tr:
                    if px_ < x0 or px_ > x1 or py_ < y0 or py_ > y1:
                        continue
                    px, py = sx(px_), sy(py_)
                    g.rect(px, py, 2, 2, color=col)
        for j in range(self.k):
            cx, cy = sx(self.cents[j, 0]), sy(self.cents[j, 1])
            g.line(cx - 6, cy, cx + 6, cy, color="white", width=2)
            g.line(cx, cy - 6, cx, cy + 6, color="white", width=2)
            g.rect(cx - 2, cy - 2, 5, 5, color="yellow")
        g.frame(0, 0, cw, ch, color="navy")
        head = "ITER " + str(self.iter) + "  K " + str(self.k) + "  N " + str(len(data))
        inertia_txt = "  INERTIA " + format(int(self.inertia), "d") if self.inertia else ""
        state = "SETTLED" if (self.playing and self.settled) else ("RUN" if self.playing else "PAUSED")
        g.text(6, 4, head + inertia_txt, color="yellow", size="small")
        g.text(6, self.height - 22, state + "  ZM " + ("%.1f" % self.zoom) + "  " + self.name,
               color="lime" if state in ("RUN", "SETTLED") else "red", size="small")
        if self._msg:
            g.text(self.width // 2, 16, self._msg, color="white", size="medium", center=True)
        g.text(6, self.height - 12, "space=pause n=1 iter ,/.=speed k/l=k up-down  t=trail h=home", color="darkgray", size="small")
        g.text(6, self.height - 3, "1-4=datasets  x/z=zoom  arrows=pan  color=cluster", color="darkgray", size="small")

    def game_state(self):
        return {
            "iter": self.iter,
            "k": self.k,
            "n_points": len(self.data),
            "inertia": int(self.inertia) if self.inertia else None,
            "settled": self.settled,
            "dataset": self.name,
        }

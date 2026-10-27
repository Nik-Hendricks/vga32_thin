import math
import time
import numpy as np
from vga32.game import GameApp

W, H = 512, 320
NX, NY = 20, 13
NUNITS = NX * NY
RAMP = ["lime", "green", "cyan", "sky", "blue", "navy"]
DSNAMES = {1: "five blobs", 2: "double ring", 3: "spiral", 4: "crossing lines"}


class KohonenApp(GameApp):
    app_id = "data.som"
    title = "Kohonen Map"
    icon = "cloud"
    category = "Data"
    width, height = 620, 340
    fps = 60

    def start(self):
        self.rng = np.random.default_rng(1)
        self.weights = np.array([[W / 2, H / 2]], dtype=float) + \
            self.rng.uniform(-W * 0.4, W * 0.4, size=(NUNITS, 2))
        self.heat = {}
        self.batch = 3
        self.playing = True
        self.trail = True
        self.grid = False
        self.bmu = None
        self._gd = np.zeros(NUNITS, dtype=int)
        self.samples = 0
        self.target = NUNITS * 40
        self.converged = False
        self.dset = "five blobs"
        self.camx, self.camy = W / 2.0, H / 2.0
        self.zoom = 1.6
        self._now = time.time()
        self._msg = ""
        self._mexp = 1e9
        self._data(1)
        self.splash("kohonen map self-organizing onto data", 6.0)

    def splash(self, t, secs=3.5):
        self._msg = t
        self._mexp = self._now + secs

    def _data(self, key):
        r = np.random.default_rng(100 + key)
        if key == 1:
            pts = []
            for cx, cy, s in [(150, 110, 26), (360, 95, 30), (170, 240, 30), (380, 235, 24), (256, 175, 42)]:
                pts.append(r.normal(0, s, size=(240, 2)) + [cx, cy])
            self.data = np.vstack(pts)
        elif key == 2:
            a = r.uniform(0, 2 * np.pi, 650)
            rad = np.where(r.random(650) < 0.5, 85, 145) + r.normal(0, 7, 650)
            self.data = np.stack([rad * np.cos(a), rad * np.sin(a)], 1) + [W / 2, H / 2]
        elif key == 3:
            t = np.linspace(0, 1, 380)
            a1 = t * 4.2 * np.pi + r.normal(0, 0.10, 380)
            p1 = np.stack([np.cos(a1), np.sin(a1)], 1) * (18 + 125 * t)
            a2 = a1 + np.pi + r.normal(0, 0.10, 380)
            p2 = np.stack([np.cos(a2), np.sin(a2)], 1) * (18 + 125 * t)
            self.data = np.vstack([p1, p2]) + [W / 2, H / 2]
        else:
            a = r.uniform(0.1, 0.9, 450)
            l1 = np.stack([W * a, 30 + (H - 60) * a], 1) + r.normal(0, 5, (450, 2))
            b = r.uniform(0.1, 0.9, 450)
            l2 = np.stack([W * (1 - b), 30 + (H - 60) * b], 1) + r.normal(0, 5, (450, 2))
            self.data = np.vstack([l1, l2])
        self.data = np.clip(self.data, 6, [W - 6, H - 6])
        self.dset = DSNAMES[key]
        self.samples = 0
        self.converged = False
        self.splash(self.dset + "  " + str(len(self.data)) + " pts", 3.0)

    def _seed(self):
        self.weights = np.array([[W / 2, H / 2]], dtype=float) + \
            self.rng.uniform(-W * 0.4, W * 0.4, size=(NUNITS, 2))
        self.samples = 0
        self.converged = False
        self.heat = {}
        self.splash("weights reseeded", 2.5)

    def _train(self, n):
        wt = self.weights
        data = self.data
        for _ in range(n):
            self.samples += 1
            x = data[int(self.rng.integers(len(data)))]
            d = ((wt - x) ** 2).sum(1)
            bmu = int(d.argmin())
            self.bmu = bmu
            if not self.converged and self.samples >= self.target:
                self.converged = True
                self.splash("converged  (t=1.0, gentle adaptation continues)", 5.0)
            t = min(1.0, self.samples / self.target)
            lr = 0.07 * (1.0 - t) + 0.004
            rad = 6.0 * (1.0 - t) + 1.0
            bx, by = bmu % NX, bmu // NX
            gd = np.zeros(NUNITS, dtype=int)
            for i in range(NUNITS):
                ix, iy = i % NX, i // NX
                gdist = max(abs(ix - bx), abs(iy - by))
                gd[i] = gdist
                if gdist > 8:
                    continue
                g = lr * math.exp(-(gdist * gdist) / (2.0 * rad * rad))
                if g < 0.005:
                    continue
                wt[i] += g * (x - wt[i])
            self._gd = gd
            if self.trail:
                self.heat[(int(wt[bmu, 0]), int(wt[bmu, 1]))] = 1.0

    def _decay(self, f):
        for k in list(self.heat):
            v = self.heat[k] * f
            if v < 0.15:
                self.heat.pop(k)
            else:
                self.heat[k] = v

    def update(self, dt):
        self._now = time.time()
        if self._now > self._mexp and self._msg:
            self._msg = ""
        if self.pressed("space"):
            self.playing = not self.playing
            self.splash("paused" if not self.playing else "running", 2.0)
        if self.pressed("n"):
            self.playing = False
            self._train(1)
        if self.pressed(","):
            self.batch = max(1, self.batch - 1)
            self.splash("batch " + str(self.batch), 2.0)
        if self.pressed("."):
            self.batch = min(16, self.batch + 1)
            self.splash("batch " + str(self.batch), 2.0)
        for key in (1, 2, 3, 4):
            if self.pressed(str(key)):
                self._data(key)
        if self.pressed("w"):
            self._seed()
        if self.pressed("t"):
            self.trail = not self.trail
            if not self.trail:
                self.heat = {}
        if self.pressed("g"):
            self.grid = not self.grid
        if self.pressed("h"):
            self.camx, self.camy = W / 2.0, H / 2.0
            self.zoom = 1.6
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
            self._train(self.batch)
            if self.trail:
                self._decay(0.94)

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
        if self.grid and zw >= 2:
            for x in range(max(0, (x0 // 64) * 64), min(W, x1) + 64, 64):
                px = sx(x)
                if -1 <= px <= cw:
                    g.line(px, 0, px, ch, color="navy", width=1)
            for y in range(max(0, (y0 // 64) * 64), min(H, y1) + 64, 64):
                py = sy(y)
                if -1 <= py <= ch:
                    g.line(0, py, cw, py, color="navy", width=1)
        stride = 8 if zw < 1.5 else (3 if zw < 3 else 1)
        for i in range(0, len(self.data), stride):
            p = self.data[i]
            px, py = sx(p[0]), sy(p[1])
            if 0 <= px <= cw and 0 <= py <= ch:
                g.rect(px, py, 2, 2, color="gray")
        if self.trail and len(self.heat) <= 2000:
            for (kx, ky), h in self.heat.items():
                if kx < x0 or kx > x1 or ky < y0 or ky > y1:
                    continue
                px, py = sx(kx), sy(ky)
                if px < 0 or px > cw or py < 0 or py > ch:
                    continue
                c = "darkgray" if h < 0.35 else ("gray" if h < 0.6 else ("sky" if h < 0.8 else "cyan"))
                g.rect(px, py, 2, 2, color=c)
        wt = self.weights
        gd = self._gd
        for i in range(NUNITS):
            ix, iy = i % NX, i // NX
            wx, wy = wt[i, 0], wt[i, 1]
            if wx < x0 or wx > x1 or wy < y0 or wy > y1:
                continue
            px, py = sx(wx), sy(wy)
            if ix + 1 < NX:
                j = i + 1
                jwx, jwy = wt[j, 0], wt[j, 1]
                if jwx >= x0 and jwx <= x1 and jwy >= y0 and jwy <= y1:
                    k = min(int(gd[i]), int(gd[j]))
                    g.line(px, py, sx(jwx), sy(jwy), color=RAMP[k] if k < 6 else "navy", width=1)
            if iy + 1 < NY:
                j = i + NX
                jwx, jwy = wt[j, 0], wt[j, 1]
                if jwx >= x0 and jwx <= x1 and jwy >= y0 and jwy <= y1:
                    k = min(int(gd[i]), int(gd[j]))
                    g.line(px, py, sx(jwx), sy(jwy), color=RAMP[k] if k < 6 else "navy", width=1)
            g.rect(px - 1, py - 1, 3, 3, color="white")
        if self.bmu is not None:
            bx, by = sx(wt[self.bmu, 0]), sy(wt[self.bmu, 1])
            g.line(bx - 5, by, bx + 5, by, color="yellow", width=2)
            g.line(bx, by - 5, bx, by + 5, color="yellow", width=2)
        g.frame(0, 0, cw, ch, color="navy")
        t = min(1.0, self.samples / self.target)
        head = "SAMPLES " + str(self.samples) + "  T " + str(int(t * 100)) + "%  B " + str(self.batch)
        state = "TRAIN" if self.playing else "PAUSED"
        g.text(6, 4, head, color="yellow", size="small")
        g.text(6, self.height - 22, state + "  ZM " + ("%.1f" % self.zoom) + "  " + self.dset,
               color="lime" if state == "TRAIN" else "red", size="small")
        if self._msg:
            g.text(self.width // 2, 16, self._msg, color="white", size="medium", center=True)
        g.text(6, self.height - 12, "space=pause n=1 sample ,/.=batch  w=reseed  t=trail g=grid h=home", color="darkgray", size="small")
        g.text(6, self.height - 3, "1-4=datasets  x/z=zoom  arrows=pan  280 map units", color="darkgray", size="small")

    def game_state(self):
        return {
            "sampled": self.samples,
            "t": round(min(1.0, self.samples / self.target), 3),
            "batch": self.batch,
            "dataset": self.dset,
            "converged": self.converged,
        }
